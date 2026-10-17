# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este repositório

Desafio de curso (MBA IA): construir uma **Claude Code Skill chamada `refactor-arch`** que analisa, audita e refatora projetos legados para o padrão MVC, de forma agnóstica de tecnologia. O repositório traz três projetos-alvo com code smells **intencionais**. A especificação completa do desafio (severidades, fases, critérios de aceite, checklist de validação) está em `docs/DESAFIO.md`; o `README.md` raiz é a documentação da entrega (análise manual, construção da skill, resultados, como executar). Leia `docs/DESAFIO.md` antes de qualquer trabalho na skill.

Os code smells dos projetos-alvo são o insumo do desafio. **Não corrija problemas nos projetos "de passagem"** ao trabalhar em outra coisa: eles só devem ser alterados pela execução da Fase 3 da skill (ou quando o usuário pedir explicitamente).

## Entregáveis e onde estão

- **Skill:** `code-smells-project/.claude/skills/refactor-arch/` é a cópia canônica (`SKILL.md` + `references/` com 6 arquivos: analise-projeto, catalogo-anti-patterns com AP-01..AP-18, template-relatorio, guidelines-mvc, playbook-refatoracao com PB-01..PB-16, validacao). As cópias em `ecommerce-api-legacy/` e `task-manager-api/` devem ser **byte a byte idênticas**: edite sempre a canônica e recopie (`cp -r`), depois confira com `diff -r`. O nome `refactor-arch` e o arquivo `SKILL.md` são fixos.
- **Relatórios:** `reports/audit-project-{1,2,3}.md` recebem a saída da Fase 2 de cada projeto (`claude "/refactor-arch ../reports/audit-project-N.md"` a partir do diretório do projeto).
- **README raiz:** seções A (Análise Manual), B (Construção da Skill), C (Resultados, preenchida após as execuções) e D (Como Executar).

Regras da skill que não podem ser violadas: a Fase 2 **pausa e pede confirmação** antes de modificar qualquer arquivo; a Fase 3 **valida** boot da aplicação e endpoints respondendo.

## Comandos

Não há suíte de testes, linter ou build em nenhum projeto. A validação é manual: subir a aplicação e bater nos endpoints.

### code-smells-project (Python/Flask, porta 5000)
```bash
cd code-smells-project
pip install -r requirements.txt
python app.py              # cria loja.db e popula seeds no primeiro boot
```

### ecommerce-api-legacy (Node.js/Express, porta 3000)
```bash
cd ecommerce-api-legacy
npm install
npm start                  # node src/app.js; SQLite em memória, seeds no boot
```
Requisições de exemplo (REST Client) em `api.http`.

### task-manager-api (Python/Flask + SQLAlchemy, porta 5000)
```bash
cd task-manager-api
pip install -r requirements.txt
python seed.py             # OBRIGATÓRIO antes do primeiro boot; recria tasks.db
python app.py
```
`seed.py` importa `app` de `app.py`, então o módulo `app.py` precisa continuar expondo `app` e `db` (ou o seed deve ser ajustado junto) em qualquer refatoração.

### Smoke test rápido
```bash
curl http://localhost:5000/health      # projetos Flask
curl http://localhost:3000/api/admin/financial-report   # Express
```

Os dois projetos Flask usam a mesma porta 5000: não os rode simultaneamente.

## Arquitetura dos projetos-alvo

Os três projetos têm níveis de organização deliberadamente diferentes. Isso importa porque a Fase 3 da skill precisa se adaptar: um monolito exige criação de camadas do zero; um projeto parcialmente organizado exige realocação de responsabilidades.

### code-smells-project — monolito plano (4 arquivos)
- `app.py`: cria o `Flask`, registra rotas via `add_url_rule` apontando para funções de `controllers`, e ainda define inline os endpoints `/admin/reset-db` e `/admin/query` (este executa SQL arbitrário vindo do body).
- `controllers.py`: funções de view que leem `request`, validam e chamam `models`.
- `models.py`: funções com SQL cru (sqlite3) para produtos, usuários, pedidos e relatório de vendas, montando dicts à mão.
- `database.py`: singleton global `db_connection` com `check_same_thread=False`, cria tabelas e seeds dentro de `get_db()`.
- Domínio: e-commerce (produtos, usuarios, pedidos, itens_pedido). Senhas em texto puro, `SECRET_KEY` e `DEBUG=True` hardcoded.

### ecommerce-api-legacy — God Class em Node
- `src/app.js`: entry point; instancia `AppManager`, chama `initDb()` e `setupRoutes(app)`.
- `src/AppManager.js`: uma única classe que cria o banco em memória, define o schema, insere seeds e registra todas as rotas com handlers inline. O checkout (`POST /api/checkout`) é um callback hell de ~6 níveis que cria usuário, "processa" pagamento (aprovado se o cartão começa com "4"), matricula e audita. O relatório financeiro tem N+1 em callbacks aninhados com contadores manuais.
- `src/utils.js`: objeto `config` com credenciais e chave de gateway hardcoded, cache global mutável e `badCrypto` (hash falso baseado em base64).
- Domínio: LMS (users, courses, enrollments, payments, audit_logs). Usa `sqlite3` com API de callbacks (sem promises).

### task-manager-api — camadas parciais, responsabilidades vazando
- `app.py`: composition root com `Blueprint`s; config SQLAlchemy e `SECRET_KEY` hardcoded; `db.create_all()` no import.
- `database.py`: só expõe `db = SQLAlchemy()`.
- `models/`: `Task`, `User`, `Category` como `db.Model`, com `to_dict()` manual e alguma validação dentro do model.
- `routes/`: `task_routes.py`, `user_routes.py`, `report_routes.py`. Apesar do nome, concentram lógica de negócio, queries e serialização, ou seja, fazem papel de controller + service. `report_routes.py` também abriga o CRUD de `/categories`.
- `services/notification_service.py`: SMTP com credenciais hardcoded e lista de notificações em memória.
- `utils/helpers.py`: funções utilitárias e constantes (`VALID_STATUSES`, `MAX_TITLE_LENGTH`, etc.) que deveriam viver em config/domínio.
- `seed.py`: popula o banco; depende de `from app import app, db`.
- Dependências pinadas: flask 3.0.0, flask-sqlalchemy 3.1.1. `marshmallow`, `requests` e `python-dotenv` estão no `requirements.txt` mas não são importados em lugar nenhum. `datetime.utcnow` (deprecated no Python 3.12+) aparece em todos os models, rotas, service e helpers.

## Convenções para a skill

- A skill deve funcionar a partir do diretório do projeto-alvo (`cd <projeto> && claude "/refactor-arch"`), sem conhecer nada específico de um projeto. Qualquer heurística deve ser derivada de sinais genéricos (arquivos de manifesto, imports, padrões de código), não de nomes de arquivo deste repositório.
- Relatórios seguem a escala CRITICAL / HIGH / MEDIUM / LOW definida no `README.md` raiz, ordenados do mais grave para o menos grave, cada finding com arquivo e linhas exatos.
- Idioma dos relatórios, README e arquivos de referência: português (os projetos-alvo também usam nomes em português).
