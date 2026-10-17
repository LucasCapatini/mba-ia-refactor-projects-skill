# Desafio MBA — Skill `refactor-arch`: refatoração arquitetural automatizada

Este repositório é a entrega do desafio "Criação de Skills — Refatoração Arquitetural Automatizada". O enunciado original está preservado em [`docs/DESAFIO.md`](docs/DESAFIO.md).

A entrega é uma **Claude Code Skill** chamada `refactor-arch` que, em três fases sequenciais, analisa a stack de um projeto backend, audita o código contra um catálogo de anti-patterns com relatório e pausa para confirmação humana, e refatora o projeto para o padrão MVC validando que a aplicação continua funcionando. A skill é agnóstica de tecnologia e foi aplicada em três projetos legados: dois em Python/Flask e um em Node.js/Express.

**Ferramenta escolhida:** Claude Code (Custom Skills em `.claude/skills/`).

## Sumário

- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)

---

## A) Análise Manual

Antes de escrever a skill, li os três projetos por completo e catalogei os problemas com arquivo e linha. Abaixo estão os achados mais relevantes de cada um, classificados pela escala do desafio (CRITICAL / HIGH / MEDIUM / LOW) e com a justificativa de por que importam. O levantamento completo passa de cem itens; aqui ficam os que mais pesam na arquitetura e na segurança.

### Projeto 1 — `code-smells-project` (Python/Flask, API de E-commerce)

Monolito em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`) com SQL cru via `sqlite3`.

| # | Severidade | Problema | Localização | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection por concatenação de strings em praticamente todas as funções de acesso a dados | `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140-166, 279-281, 289-297` | Qualquer parâmetro de rota ou body vai direto para o SQL. O login aceita `' OR '1'='1` e autentica sem senha. |
| 2 | CRITICAL | Endpoint que executa SQL arbitrário recebido no body | `app.py:63-80` | `/admin/query` sem autenticação permite ler, alterar ou apagar o banco inteiro. |
| 3 | CRITICAL | `SECRET_KEY` e `DEBUG=True` hardcoded; `health_check` devolve a secret key, o caminho do banco e `debug: True` | `app.py:7-8`, `controllers.py:285-289` | Segredo versionado no repositório e exposto publicamente por um endpoint. |
| 4 | CRITICAL | Senhas gravadas, comparadas e retornadas em texto puro | `models.py:83, 99, 110, 126-129` | `GET /usuarios` lista todas as senhas; comprometimento total das contas. |
| 5 | HIGH | `models.py` é um God Module: produtos, usuários, pedidos e relatórios num só arquivo, com regra de negócio (estoque, total, desconto) na camada de dados | `models.py:1-314`, `133-169`, `256-262` | Impossível testar a regra de pedido sem banco; qualquer alteração afeta quatro domínios. |
| 6 | HIGH | Conexão singleton global com `check_same_thread=False`, criando tabelas e seeds dentro de `get_db()` | `database.py:4-10, 7-86` | Estado global compartilhado entre threads e efeito colateral no primeiro acesso. |
| 7 | HIGH | `try/except Exception` copiado em todos os controllers, sem error handler central, devolvendo `str(e)` ao cliente | `controllers.py:5-292` | Vaza detalhes internos e replica o mesmo boilerplate em 16 funções. |
| 8 | MEDIUM | Query N+1 em dois níveis ao listar pedidos (itens e depois produto de cada item) | `models.py:187-199, 219-231` | Latência cresce linearmente com o número de pedidos. |
| 9 | MEDIUM | Validação de produto duplicada e divergente entre criar e atualizar; `float()` de query string sem tratamento | `controllers.py:28-50 vs 72-90`, `118-121` | Regras inconsistentes e entrada inválida gerando 500 em vez de 400. |
| 10 | LOW | Magic numbers nas faixas de desconto; `print` como logging; `id` sombreando builtin; `import sqlite3` sem uso | `models.py:257-262`, `controllers.py:8, 11, 57`, `models.py:2` | Legibilidade e manutenção. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

Três arquivos em `src/`: `app.js` (entry point), `AppManager.js` (tudo o resto) e `utils.js` (config, cache e "cripto").

| # | Severidade | Problema | Localização | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais de banco, chave de gateway de pagamento e usuário SMTP hardcoded num objeto `config` | `src/utils.js:1-7` | Segredos de produção versionados; a chave `pk_live_` ainda é impressa no console. |
| 2 | CRITICAL | `badCrypto`: "hash" de senha feito com base64 repetido, trivialmente reversível | `src/utils.js:17-23`, uso em `AppManager.js:68` | Senhas efetivamente em texto puro. |
| 3 | CRITICAL | Número do cartão logado em `console.log` junto com a chave do gateway | `src/AppManager.js:41` | Dados de pagamento em log de aplicação. |
| 4 | CRITICAL | `AppManager` é uma God Class: cria o banco, define schema, insere seeds, registra rotas e contém a regra de pagamento | `src/AppManager.js:1-141` | Nenhuma responsabilidade isolável; impossível testar o checkout sem subir tudo. |
| 5 | HIGH | Checkout em callback hell de seis níveis, sem transação: se o INSERT de pagamento falha, a matrícula já foi gravada | `src/AppManager.js:27-78` | Escrita parcial e fluxo ilegível. |
| 6 | HIGH | Estado global mutável exportado (`globalCache`, `totalRevenue`) e nenhum tratamento de erro central | `src/utils.js:9-15, 25` | Vazamento entre requisições; erros de banco ignorados em vários callbacks. |
| 7 | HIGH | `DELETE /api/users/:id` apaga o usuário e deixa matrículas e pagamentos órfãos, e a própria resposta admite isso | `src/AppManager.js:131-138` | Integridade referencial quebrada por design. |
| 8 | MEDIUM | Relatório financeiro com N+1 em callbacks aninhados e contadores manuais (`coursesPending--`, `enrPending--`) para sincronizar | `src/AppManager.js:80-129` | Uma query por curso, por matrícula, por usuário e por pagamento. |
| 9 | MEDIUM | Validação de entrada limitada a presença dos campos; cartão e email sem formato; API de callbacks do `sqlite3` (idioma obsoleto, sem Promises) | `src/AppManager.js:35`, todo o arquivo | Entradas inválidas chegam ao SQL e ao "gateway". |
| 10 | LOW | Nomes de uma ou duas letras (`u`, `e`, `p`, `cid`, `cc`), `const self = this`, `.verbose()` desnecessário, mensagens internas ao cliente | `src/AppManager.js:29-33, 26, 1, 134` | Legibilidade. |

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy, Task Manager)

Já possui `models/`, `routes/`, `services/` e `utils/`, mas as responsabilidades vazam entre as camadas.

| # | Severidade | Problema | Localização | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | `User.to_dict()` inclui o hash da senha, devolvido em quatro endpoints (listar, criar, atualizar, login) | `models/user.py:21`, `routes/user_routes.py:33, 85, 129, 209` | Hashes expostos publicamente, e são MD5 (item 2). |
| 2 | CRITICAL | Hash de senha com MD5 sem salt e comparação não constante | `models/user.py:29, 32` | Quebrável por rainbow table em segundos. |
| 3 | CRITICAL | Token de login previsível (`'fake-jwt-token-' + id`) e escalada de privilégio: qualquer um cria ou se promove a `admin` | `routes/user_routes.py:210, 52, 71-72, 119-125` | Autenticação e autorização inexistentes na prática. |
| 4 | CRITICAL | Credenciais SMTP e `SECRET_KEY` hardcoded | `services/notification_service.py:9-10`, `app.py:13` | Segredos versionados. |
| 5 | HIGH | Lógica de negócio e validação dentro das rotas (`create_task` e `update_task` com ~70 linhas cada); rotas acessam `db.session` diretamente | `routes/task_routes.py:85-154, 156-223` | As "routes" fazem papel de controller, service e validator ao mesmo tempo. |
| 6 | HIGH | Regra de "task atrasada" duplicada em sete lugares enquanto `Task.is_overdue()` existe e nunca é chamado; CRUD de categorias dentro do blueprint de relatórios | `task_routes.py:30-39, 71-80, 283-287`, `user_routes.py:171-180`, `report_routes.py:33-43, 132-135, 157-223` | Divergência silenciosa de regra; baixa coesão dos blueprints. |
| 7 | HIGH | `db.create_all()` executado no import de `app.py`; `seed.py` importa a instância da app | `app.py:30-31`, `seed.py:2` | Efeito colateral ao importar; sem application factory. |
| 8 | MEDIUM | Queries N+1 (`User.query.get`/`Category.query.get` por task; uma query por usuário e um COUNT por categoria nos relatórios); 12 COUNTs separados no resumo | `task_routes.py:42, 51`, `report_routes.py:15-28, 55-56, 163`, `user_routes.py:22` | Performance degrada com o volume. |
| 9 | MEDIUM | `except:` nu em todas as rotas; `utils/helpers.py` tem validadores e constantes que ninguém usa (`process_task_data`, `VALID_STATUSES`, `validate_email`) enquanto as rotas reimplementam tudo | `task_routes.py:62, 137, 204, 236`, `utils/helpers.py:19-23, 57-116` | Erros engolidos; código morto convivendo com duplicação. |
| 10 | LOW | `datetime.utcnow()` deprecated em todos os arquivos; `Model.query.get` legado no SQLAlchemy 2.x; imports sem uso (`os, sys, json, time, hashlib`); magic numbers (prioridade 1-5, 200, 7 dias, `'#000000'`); `marshmallow`, `requests` e `python-dotenv` pinados sem nenhum import | todos os models e rotas; `app.py:7`; `requirements.txt` | APIs obsoletas e dependências fantasmas. |

---

## B) Construção da Skill

### Estrutura

A skill vive em `.claude/skills/refactor-arch/` dentro de cada um dos três projetos. A cópia canônica é a de `code-smells-project`; as outras duas são idênticas byte a byte.

```
.claude/skills/refactor-arch/
├── SKILL.md                          # orquestrador: regras invioláveis + as 3 fases + formatos de saída
└── references/
    ├── analise-projeto.md            # Fase 1 — heurísticas de detecção de stack, papel de arquivos, endpoints, arquitetura
    ├── catalogo-anti-patterns.md     # Fase 2 — 18 anti-patterns (AP-01..AP-18) + tabelas de APIs deprecated
    ├── template-relatorio.md         # Fase 2 — esqueleto exato do relatório e regras de preenchimento
    ├── guidelines-mvc.md             # Fase 3 — responsabilidades por camada, direção de dependências, layouts-alvo
    ├── playbook-refatoracao.md       # Fase 3 — 16 transformações (PB-01..PB-16) com antes/depois em Python e JS
    └── validacao.md                  # Fase 3 — receitas de boot, smoke de endpoints, diff de contrato, limpeza
```

### Decisões de design

**O SKILL.md é um prompt, as referências são conhecimento.** O `SKILL.md` diz *o que fazer e em que ordem*; não contém heurísticas nem exemplos de código. Cada fase abre com a instrução "Leia agora: `references/<arquivo>.md`", de modo que o agente carrega só o conhecimento daquela fase (progressive disclosure). Na Fase 3 ele lê apenas as seções `PB-xx` mapeadas aos findings confirmados, não o playbook inteiro.

**Regras invioláveis no topo.** Oito regras curtas que valem para todas as fases: sequência estrita, Fases 1 e 2 somente leitura, exclusões de diretórios, agnosticismo, contrato de endpoints intocável, escopo fechado nos findings, honestidade na validação e idioma. Elas existem porque os modos de falha mais comuns de um agente refatorando são "corrigir de passagem", trocar o framework sem pedir, e declarar sucesso sem ter testado.

**Pausa obrigatória com fallback.** A Fase 2 usa `AskUserQuestion` para perguntar onde salvar o relatório e se pode prosseguir. Se a ferramenta não existir ou a sessão for não interativa, a skill imprime `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e **encerra o turno**; só continua com resposta afirmativa. O relatório só é gravado em disco depois da resposta, porque gravar já seria uma escrita antes da confirmação.

**Contrato de endpoints como oráculo.** A Fase 1 produz uma tabela `método | path | handler | arquivo:linha`. A Fase 3 sobe a aplicação original antes de mexer em qualquer coisa, registra status e chaves JSON de cada endpoint (baseline), e repete o mesmo smoke ao final. As únicas diferenças permitidas são remoção de campos sensíveis e desativação de rotas perigosas por flag, ambas listadas numa seção própria da saída.

**Duas estratégias de refatoração.** A classificação da Fase 1 (`Monolito plano` / `Parcialmente em camadas` / `MVC`) escolhe entre **A — criar camadas** e **B — realocar responsabilidades**. Na B, a guideline proíbe mover o que já está no lugar certo e manda reaproveitar métodos e helpers órfãos antes de criar novos. Isso foi pensado para o projeto 3, que já tem pastas por camada.

**Identificadores cruzados.** Cada anti-pattern tem um ID (`AP-xx`) e aponta para o(s) padrão(ões) de transformação que o resolve (`PB-xx`). O relatório cita ambos, e a saída da Fase 3 lista `finding → PB aplicado → arquivos`. Isso torna rastreável por que cada mudança foi feita.

### Catálogo de anti-patterns (18) e por quê

| Severidade | Anti-patterns | Motivação |
|---|---|---|
| CRITICAL | AP-01 segredos hardcoded/expostos; AP-02 SQL injection e SQL arbitrário; AP-03 God Class/Module; AP-04 senhas inseguras e vazamento de credenciais | São os quatro problemas que aparecem nos três projetos e que, sozinhos, comprometem a aplicação. |
| HIGH | AP-05 Fat Controller; AP-06 estado global mutável e singleton; AP-07 efeitos colaterais no import e ausência de composition root/DI; AP-08 config hardcoded | Violações estruturais de MVC/SOLID que a Fase 3 precisa resolver para a nova estrutura fazer sentido. |
| MEDIUM | AP-09 N+1; AP-10 erros duplicados/engolidos/vazados; AP-11 validação ausente ou duplicada; AP-12 APIs deprecated; AP-13 duplicação e serialização manual; AP-14 integridade (sem transação/FK/cascata) | Padronização, performance e robustez. AP-12 é o requisito de detecção de APIs deprecated, com tabelas separadas para Python/Flask/SQLAlchemy e Node/Express, cada entrada com o equivalente moderno. |
| LOW | AP-15 magic numbers; AP-16 nomenclatura; AP-17 imports/deps sem uso; AP-18 `print`/`console.log` e mensagens internas ao cliente | Legibilidade e higiene, baratos de corrigir junto com o resto. |

Cada entrada traz sinais de detecção em regex para Python e para JavaScript, lista de falsos positivos (para o agente não reportar `except SpecificError` como bare except, por exemplo), impacto, recomendação e os PBs associados.

### Playbook (16 transformações)

PB-01 config por ambiente · PB-02 SQL parametrizado e rota de SQL arbitrário atrás de flag · PB-03 dividir God Class por domínio · PB-04 hash seguro e remoção de campos sensíveis · PB-05 Thin Routes → Controllers → Services · PB-06 conexão por contexto/injetada · PB-07 application factory e entry point com guard · PB-08 error handling centralizado · PB-09 eliminar N+1 · PB-10 callback hell → async/await com transação · PB-11 validadores centralizados · PB-12 substituir APIs deprecated · PB-13 constantes e enums · PB-14 serialização única por entidade · PB-15 transações e integridade · PB-16 nomenclatura, logging e limpeza.

Todos têm código antes/depois em Python **e** em JavaScript e um checklist de contrato. As soluções usam só biblioteca padrão ou o que já está no manifesto (`werkzeug.security` para hash em Flask, `node:crypto` com scrypt em Node, wrapper de Promises sobre `sqlite3` em vez de trocar o driver), porque a regra de escopo proíbe dependências novas sem confirmação.

### Como a skill ficou agnóstica de tecnologia

- **Detecção pelo manifesto e pelo conteúdo, nunca pelo nome do arquivo.** A referência de análise mapeia `requirements.txt`, `package.json`, `go.mod`, `pom.xml`, `*.csproj`, `Gemfile` e `composer.json` para linguagem/framework, e classifica o papel de cada arquivo por sinais de código (`@route` vs `app.get(`, `cursor.execute` vs `db.run`, `db.Model` vs `mongoose.Schema`). Um projeto com `models.py` que na verdade contém rotas seria classificado corretamente.
- **Sinais de detecção por linguagem.** Cada anti-pattern tem uma coluna de regex para Python e outra para JavaScript; frameworks extras (FastAPI, Spring, Gin) aparecem nas tabelas de endpoints.
- **Layouts-alvo por stack e tabela de correspondência de conceitos** (`Blueprint` ↔ `express.Router`, `@app.errorhandler` ↔ `app.use((err, req, res, next))`, `create_app()` ↔ `createApp({ db })`).
- **Receitas de validação por stack e por shell**, incluindo PowerShell 5.1 (sem `&&`, `curl` como alias) e Bash.
- **Nenhum nome de arquivo deste repositório aparece na skill.** Os exemplos do playbook usam entidades ilustrativas.

### Desafios encontrados e como foram resolvidos

- **Garantir que a Fase 2 realmente pare.** Um agente tende a continuar quando a instrução é só "pergunte". A solução foi tornar a pausa uma regra inviolável, oferecer dois mecanismos (ferramenta de pergunta e fallback textual com encerramento de turno) e definir que ausência de resposta significa "não".
- **Preservar o contrato em projetos com nomes ruins.** O checkout do projeto 2 recebe `usr`, `eml`, `c_id`. Renomear quebraria o cliente. O playbook mostra como mapear na borda do controller (`const { usr: name, eml: email } = req.body`) e manter o path e os campos externos.
- **`datetime.utcnow` sem mudar o formato das respostas.** Trocar para `datetime.now(timezone.utc)` muda a serialização (`+00:00`) e quebra comparações com datas naive gravadas no SQLite. A solução é um helper único `utc_now()` que devolve UTC naive, documentado no PB-12.
- **Projeto já parcialmente organizado.** Sem orientação, o agente mudaria tudo para `src/` e quebraria o `seed.py`. A estratégia B e a seção sobre scripts auxiliares da guideline tratam isso: manter as pastas, exportar `app` em nível de módulo e chamar `init_db()` explicitamente.
- **Validação honesta no Windows.** O reloader do Flask cria um processo filho que sobrevive ao `kill`, e PowerShell 5.1 não tem `&&`. A referência de validação traz receitas para os dois shells, exige desligar o reloader e manda confirmar que a porta ficou livre.
- **Banco SQLite em memória no Node.** Cada `new Database(':memory:')` é um banco diferente; a guideline exige uma única conexão criada no `start()` e injetada em `createApp({ db })`, com schema e seed aguardados antes do `listen`.

---

## C) Resultados

> Esta seção é preenchida após a execução da skill nos três projetos (Etapa 3 do plano). Os relatórios ficam em `reports/audit-project-{1,2,3}.md`.

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1 — code-smells-project | _pendente_ | | | | |
| 2 — ecommerce-api-legacy | _pendente_ | | | | |
| 3 — task-manager-api | _pendente_ | | | | |

### Estrutura antes/depois

_pendente por projeto._

### Checklist de validação

_pendente por projeto (modelo em `docs/DESAFIO.md`)._

### Logs das aplicações após refatoração

_pendente._

### Observações sobre o comportamento em stacks diferentes

_pendente._

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado.
- Python 3.12+ e Node.js 20+ (desenvolvido com Python 3.13 e Node 22).
- `pip` e `npm` disponíveis no PATH.

### Rodar a skill em cada projeto

A skill é invocada a partir do diretório do projeto. O argumento opcional é o caminho onde salvar o relatório da Fase 2.

```bash
# Projeto 1 — Python/Flask (monolito)
cd code-smells-project
claude "/refactor-arch ../reports/audit-project-1.md"

# Projeto 2 — Node.js/Express
cd ../ecommerce-api-legacy
claude "/refactor-arch ../reports/audit-project-2.md"

# Projeto 3 — Python/Flask (parcialmente organizado)
cd ../task-manager-api
claude "/refactor-arch ../reports/audit-project-3.md"
```

Fluxo esperado em cada execução:

1. A skill imprime `PHASE 1: PROJECT ANALYSIS` com stack, domínio, arquitetura e a tabela de endpoints.
2. Imprime `ARCHITECTURE AUDIT REPORT` e **para**, perguntando se pode salvar o relatório e prosseguir. Revise o relatório e responda.
3. Com a confirmação, executa a refatoração, valida e imprime `PHASE 3: REFACTORING COMPLETE` com a estrutura nova, a tabela de endpoints antes/depois e o checklist de validação.

### Validar que a refatoração funcionou

Depois da Fase 3, suba cada aplicação com os comandos originais e bata nos endpoints. As variáveis de ambiente opcionais estão no `.env.example` de cada projeto.

```bash
# Projeto 1
cd code-smells-project && pip install -r requirements.txt && python app.py
curl http://localhost:5000/health
curl http://localhost:5000/produtos

# Projeto 2
cd ecommerce-api-legacy && npm install && npm start
curl http://localhost:3000/api/admin/financial-report
# demais exemplos em api.http

# Projeto 3
cd task-manager-api && pip install -r requirements.txt && python seed.py && python app.py
curl http://localhost:5000/health
curl http://localhost:5000/tasks
```

Os dois projetos Flask usam a porta 5000: não os rode ao mesmo tempo. No PowerShell use `curl.exe` (ou `Invoke-RestMethod`), pois `curl` é alias de `Invoke-WebRequest`.

### Reutilizar a skill em outro projeto

Copie a pasta `.claude/skills/refactor-arch/` para a raiz do projeto-alvo e rode `claude "/refactor-arch"` a partir dela. Nada na skill depende destes três projetos.
