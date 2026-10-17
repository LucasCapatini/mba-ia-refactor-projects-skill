# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este repositório

Entrega do desafio de MBA "Criação de Skills — Refatoração Arquitetural Automatizada": uma **Claude Code Skill chamada `refactor-arch`** que analisa, audita e refatora projetos backend legados para o padrão MVC em 3 fases, de forma agnóstica de tecnologia. O repositório contém a skill, três projetos-alvo **já refatorados** por ela, os relatórios de auditoria e a documentação.

- Especificação completa do desafio (severidades, fases, critérios de aceite, checklist): `docs/DESAFIO.md`.
- Documentação da entrega (análise manual, construção da skill, resultados, como executar): `README.md`.
- O código **original** dos projetos, com os code smells intencionais, está no commit `6d1ce62` (`git show 6d1ce62:code-smells-project/models.py`, por exemplo). Os relatórios em `reports/` citam linhas desse código original.

## Entregáveis e onde estão

- **Skill:** `code-smells-project/.claude/skills/refactor-arch/` é a cópia canônica (`SKILL.md` + `references/` com 6 arquivos: analise-projeto, catalogo-anti-patterns com AP-01..AP-18, template-relatorio, guidelines-mvc, playbook-refatoracao com PB-01..PB-16, validacao). As cópias em `ecommerce-api-legacy/` e `task-manager-api/` devem ser **byte a byte idênticas**: edite sempre a canônica e recopie (`cp -r`), depois confira com `diff -r`. O nome `refactor-arch` e o arquivo `SKILL.md` são fixos.
- **Relatórios:** `reports/audit-project-{1,2,3}.md` são a saída da Fase 2 de cada projeto. O finding #13 do projeto 3 foi corrigido após a Fase 3 (nota no próprio arquivo).
- **Evidências de validação:** `docs/validacao/` tem o smoke test externo (`smoke.py`), sua saída por projeto e os logs dos servidores.

## Comandos

Não há suíte de testes nem linter nos projetos. A validação é "sobe e responde". Os dois projetos Flask usam a porta 5000: não os rode simultaneamente. Todos aceitam variáveis de ambiente documentadas no `.env.example` de cada projeto; os defaults são seguros (`DEBUG=false`, host `127.0.0.1`).

```bash
# Projeto 1 — Python/Flask + sqlite3 (porta 5000). Cria loja.db e seeds no primeiro boot.
cd code-smells-project && pip install -r requirements.txt && python app.py

# Projeto 2 — Node/Express + sqlite3 em memória (porta 3000). Exemplos de requisições em api.http.
cd ecommerce-api-legacy && npm install && npm start

# Projeto 3 — Python/Flask + Flask-SQLAlchemy (porta 5000). seed.py é OBRIGATÓRIO antes do boot.
cd task-manager-api && pip install -r requirements.txt && python seed.py && python app.py
```

Smoke test externo de todos os endpoints (sobe e derruba o servidor sozinho; rode um projeto por vez):

```bash
python docs/validacao/smoke.py 1   # ou 2, 3
```

Rodar a skill em um projeto (sessão nova do Claude Code aberta dentro do diretório do projeto):

```bash
cd <projeto> && claude "/refactor-arch ../reports/audit-project-N.md"
```

No PowerShell use `curl.exe` ou `Invoke-RestMethod`, pois `curl` é alias de `Invoke-WebRequest`. Os dois projetos Flask compartilham o Python global; o último `pip install` vence (Flask 3.0.0 ou 3.1.1, ambos funcionam).

## Arquitetura dos projetos refatorados

Os três seguem a mesma direção de dependências: `entry point → composition root → routes → controllers → (validators, services) → models → database → config`. Models e services não conhecem HTTP. Erros de domínio (`ValidationError` 400, `NotFoundError` 404, etc.) são lançados nas camadas internas e convertidos em resposta por um error handler central. O contrato HTTP original (paths, métodos, nomes de campos do body, status codes, chaves de topo) foi preservado, exceto remoção de campos sensíveis e rotas perigosas atrás de flag.

### code-smells-project (Estratégia A: camadas criadas em `src/`)
- `app.py` raiz é só entry point: `create_app()` + `init_db()` + `seed_db()` + `app.run()` sob `__main__`.
- `src/database.py`: conexão por requisição via `flask.g` (autocommit), `transaction()` com `BEGIN IMMEDIATE`/`COMMIT`/`ROLLBACK`, `PRAGMA foreign_keys=ON`, schema e seeds explícitos.
- `src/models/*`: SQL parametrizado, um `to_dict` por entidade. Listagem de pedidos usa um único JOIN.
- `/admin/query` e `/admin/reset-db` continuam registradas, mas respondem 403 salvo `ADMIN_SQL_ENABLED=true` / `ADMIN_RESET_ENABLED=true`.
- Status de pedido válidos: `pendente, aprovado, enviado, entregue, cancelado` (em `src/domain/constants.py`).

### ecommerce-api-legacy (Estratégia A)
- `src/app.js`: `createApp({ db })` sem efeitos colaterais + `start()` com guard `require.main`. `require('./src/app')` não abre porta.
- `src/database/connection.js`: **uma única** conexão `sqlite3` (obrigatório com `:memory:`), wrapper `run/get/all/exec` em Promises, `transaction()` serializado por fila. Schema e seed são aguardados antes do `listen`.
- Campos do body do checkout (`usr`, `eml`, `pwd`, `c_id`, `card`) fazem parte do contrato e são mapeados para nomes internos no validator. Cartão começando com `APPROVED_CARD_PREFIX` (default `4`) é aprovado; o gateway é simulado.
- Handlers async passam por `asyncHandler`; erros em texto puro para manter o formato original.

### task-manager-api (Estratégia B: pastas originais mantidas)
- `app.py` expõe `app = create_app()` em nível de módulo porque `seed.py` faz `from app import app, db`. `init_db(app)` é explícito (entry point e seed); importar `app` não cria tabelas.
- `routes/` só mapeiam para `controllers/`; regra em `services/`; validação em `validators/`; constantes em `domain/constants.py`; `domain/clock.py` tem `utc_now()` (UTC naive, compatível com as colunas existentes).
- `Task.is_overdue()` é a fonte única da regra de atraso em Python; `task_service.overdue_condition()` é a mesma regra em SQL para contagens.
- `seed.py` faz `drop_all` + `create_all`: bancos antigos com MD5 não permitem login.

## Convenções

- Idioma de código, comentários, relatórios e documentação: português (identificadores técnicos em inglês onde a convenção da stack pede, como em Node).
- Nenhuma dependência nova sem necessidade comprovada: hash de senha usa `werkzeug.security` (Flask) e `node:crypto` (scrypt); `.env` via `python-dotenv` (já pinado) ou `node --env-file`.
- Ao alterar a skill, mantenha a regra de que nenhuma heurística depende de nomes de arquivo deste repositório.
