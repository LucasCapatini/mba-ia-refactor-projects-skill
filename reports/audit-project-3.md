================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, Flask-CORS 4.0.0)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-10-17
Architecture: Parcialmente em camadas — existem models/, routes/, services/ e utils/, mas as rotas concentram queries, regra de negócio e serialização; utils e services não são usados; config hardcoded; sem error handler central

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 6 | LOW: 4
Total: 17 findings

## Findings

### #1 [CRITICAL] Segredos e credenciais hardcoded (AP-01)
File: app.py:13
Locations: app.py:13 — `SECRET_KEY = 'super-secret-key-123'`; services/notification_service.py:7-10 — host, usuário e senha SMTP (`'taskmanager@gmail.com'` / `'senha123'`) literais no construtor
Description: A chave de sessão do Flask e as credenciais SMTP estão escritas no código-fonte. Não há nenhuma leitura de `os.environ`/`getenv` no projeto, apesar de `python-dotenv` estar no manifesto.
Impact: Segredos versionados no repositório e impossíveis de rotacionar sem novo deploy; qualquer pessoa com acesso ao código tem a conta de email e pode forjar cookies de sessão.
Recommendation: Criar `config.py` que lê `SECRET_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` do ambiente com defaults seguros, e `.env.example` documentando as variáveis; o service recebe a config em vez de defini-la → PB-01, PB-16

### #2 [CRITICAL] God Module: módulos de rota acumulam 4 papéis e múltiplos domínios (AP-03)
File: routes/report_routes.py:1-223
Locations: routes/report_routes.py:12-155 — relatórios agregando Task, User e Category; routes/report_routes.py:157-223 — CRUD completo de `/categories` dentro do módulo de relatórios; routes/task_routes.py:1-299 — roteamento + validação + queries + serialização + regra de "atrasado"; routes/user_routes.py:1-211 — idem, mais autenticação (`/login`)
Description: Cada módulo em `routes/` faz roteamento, controller, service e acesso a dados ao mesmo tempo. `report_routes.py` ainda cobre dois domínios distintos (relatórios e categorias) e consulta as três entidades. O pacote `services/` existe mas nenhuma rota o usa.
Impact: Nenhuma regra pode ser testada sem subir o Flask; mudanças em categorias e em relatórios colidem no mesmo arquivo; a camada `services/` virou decorativa.
Recommendation: Separar por camada e por domínio: `controllers/` (task, user, category, report, auth), `services/` (task, user, category, report, auth) e repositórios/queries nos models; `routes/` passa a só mapear path → controller → PB-03, PB-05, PB-10

### #3 [CRITICAL] Hash de senha MD5 sem salt, hash exposto em respostas e token forjável (AP-04)
File: models/user.py:16-32
Locations: models/user.py:21 — `'password': self.password` em `to_dict()`; models/user.py:29 — `hashlib.md5(pwd.encode()).hexdigest()`; models/user.py:32 — comparação `==` não constante; routes/user_routes.py:33-40 — `GET /users/<id>` devolve `to_dict()` com o hash; routes/user_routes.py:85-86 e 129 — `POST`/`PUT /users` devolvem o hash; routes/user_routes.py:207-211 — `/login` devolve o hash e `'token': 'fake-jwt-token-' + str(user.id)`
Description: Senhas são armazenadas como MD5 puro (sem salt, quebrável por rainbow table) e o hash sai em quatro endpoints via `User.to_dict()`. O "token" de login é uma concatenação previsível com o id do usuário.
Impact: Qualquer cliente da API obtém os hashes de todos os usuários; com MD5 sem salt, senhas curtas como as do seed (`1234`, `abcd`, `pass`) são recuperadas instantaneamente. O token permite se passar por qualquer usuário conhecendo apenas o id.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (já vem com o Flask, sem dependência nova); remover `password` da serialização; gerar token com `secrets.token_urlsafe` ou `itsdangerous` (dependência do Flask) assinado com a `SECRET_KEY`. Recriar `tasks.db` via `seed.py` após a troca do esquema de hash → PB-04, PB-14

### #4 [HIGH] Lógica de negócio em rotas (Fat Controller) (AP-05)
File: routes/task_routes.py:11-299
Locations: routes/task_routes.py:85-154 — `create_task` com 70 linhas: 8 `return jsonify(...), 400/404`, lookups de User/Category, parse de data, join de tags, commit; routes/task_routes.py:156-223 — `update_task` repete o mesmo fluxo; routes/task_routes.py:240-271 — montagem de query dinâmica no handler; routes/task_routes.py:273-299 — estatísticas calculadas no handler; routes/user_routes.py:42-90 e 92-132 — validação, unicidade de email, hash e commit no handler; routes/user_routes.py:185-211 — autenticação inteira no handler; routes/report_routes.py:12-101 — relatório de 90 linhas com 15 queries e agregações manuais; routes/report_routes.py:167-223 — CRUD de categorias com `db.session` direto
Description: 75 ocorrências de `db.session`/`.query` e 28 `return jsonify(...), 400` dentro de funções decoradas com `@*.route`. Validação, regra de domínio, acesso ao banco e serialização acontecem no mesmo bloco em todos os 20 handlers de negócio.
Impact: Regras (status válido, faixa de prioridade, unicidade de email, cálculo de atraso) não podem ser testadas sem HTTP e já divergem entre criar e atualizar.
Recommendation: Rotas → controllers (ler `request`, chamar service, montar resposta) → services (regra e transação) → models. Validação via validadores reutilizáveis que lançam `ValidationError` → PB-05, PB-11

### #5 [HIGH] Estado mutável em memória como armazenamento (AP-06)
File: services/notification_service.py:6
Locations: services/notification_service.py:6 — `self.notifications = []`; services/notification_service.py:31-36 e 43-48 — append e leitura dessa lista como fonte de verdade
Description: `NotificationService` guarda as notificações numa lista de instância e expõe `get_notifications(user_id)` lendo dela. Não há persistência; cada instância (ou worker) tem sua própria lista.
Impact: Dados perdidos a cada restart, inconsistentes entre processos e não testáveis de forma isolada.
Recommendation: Remover a lista; se histórico for necessário, persistir via model. O service deve receber a configuração SMTP injetada pelo composition root → PB-06

### #6 [HIGH] Efeitos colaterais no import e script importando a app (AP-07)
File: app.py:30-31
Locations: app.py:30-31 — `with app.app_context(): db.create_all()` no nível do módulo; app.py:9-20 — app, config, CORS e blueprints montados no import (sem `create_app`); seed.py:2 — `from app import app, db`
Description: Importar `app` já cria tabelas no banco. Não há application factory; `seed.py` depende de importar a instância global do entry point, e o `tasks.db` fica em `instance/` por efeito do import.
Impact: Qualquer import para teste toca o banco; impossível instanciar a app com outra config; ordem de inicialização frágil.
Recommendation: `create_app(config)` como composition root, `init_db(app)` explícito chamado no entry point e no seed; manter `app.py` expondo `app` e `db` para não quebrar `python seed.py` → PB-06, PB-07

### #7 [HIGH] Configuração hardcoded e sem separação por ambiente (AP-08)
File: app.py:11-13
Locations: app.py:11 — `'sqlite:///tasks.db'` literal; app.py:34 — `app.run(debug=True, host='0.0.0.0', port=5000)`
Description: URI do banco, modo debug, host e porta estão fixos no código; zero ocorrências de `os.environ`, `getenv` ou `load_dotenv` no projeto.
Impact: Debugger do Werkzeug (execução remota de código) ligado em qualquer ambiente; impossível apontar para outro banco ou porta sem editar o código.
Recommendation: `config.py` com `DATABASE_URL`, `FLASK_DEBUG`, `HOST`, `PORT` lidos do ambiente com defaults seguros (debug desligado) → PB-01

### #8 [MEDIUM] Query N+1 e consultas em loop (AP-09)
File: routes/report_routes.py:53-61
Locations: routes/report_routes.py:15-28 — 12 `count()` sequenciais na mesma tabela; routes/report_routes.py:53-61 — uma query de tasks por usuário dentro de `for u in users`; routes/report_routes.py:159-164 — um `count()` por categoria; routes/task_routes.py:41-57 — `User.query.get` e `Category.query.get` por task dentro do loop de `GET /tasks`; routes/task_routes.py:275-281 — 5 `count()` + `query.all()` para contar atrasadas; routes/user_routes.py:14-24 — `len(u.tasks)` dispara lazy load por usuário
Description: Listagens e relatórios fazem uma consulta por item da coleção, além de várias contagens sequenciais que uma única agregação resolveria.
Impact: Latência cresce linearmente com o número de tasks/usuários/categorias; `GET /tasks` com N tasks executa até 2N+1 queries.
Recommendation: `joinedload`/`selectinload` para user e category em `GET /tasks`; `GROUP BY` com `func.count` para contagens por status/prioridade/categoria/usuário, centralizados em um `ReportService` → PB-09

### #9 [MEDIUM] Tratamento de erros duplicado, engolido e sem handler central (AP-10)
File: routes/task_routes.py:62-63
Locations: routes/task_routes.py:62, 137, 204, 236 — `except:` nu; routes/user_routes.py:130, 149 — `except:` nu; routes/report_routes.py:186, 207, 221 — `except:` nu; utils/helpers.py:46, 49, 88 — `except:` nu; routes/task_routes.py:146-154, 217-223, 231-238 e routes/user_routes.py:80-90, 127-132, 144-151 e routes/report_routes.py:182-188, 204-209, 217-223 — mesmo bloco `try/commit/except/rollback/500` copiado 9 vezes; routes/report_routes.py:196-197 — `request.get_json()` seguido de `'name' in data` sem checar `None`; app.py — zero `@app.errorhandler`
Description: `GET /tasks` inteiro está num `except:` nu que converte qualquer bug em "Erro interno" 500 sem log. O padrão commit/rollback é repetido em cada handler de escrita. Não existe error handler central; `PUT /categories/<id>` sem body JSON gera `TypeError` → 500.
Impact: Erros silenciosos e indiagnosticáveis; respostas inconsistentes; 500 onde deveria ser 400.
Recommendation: Exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`) + `@app.errorhandler` central que mapeia para 404/400/409 e registra 500 com `logging`; commit/rollback uma vez no service → PB-08

### #10 [MEDIUM] Validação de entrada duplicada, inconsistente ou ausente (AP-11)
File: routes/task_routes.py:92-114
Locations: routes/task_routes.py:92-114 vs 166-184 — mesmas regras de título/status/prioridade copiadas em criar e atualizar; routes/task_routes.py:113 e 182 — `priority < 1` sem checar tipo (string → `TypeError` 500); routes/task_routes.py:261 e 264 — `int(priority)`/`int(user_id)` de query string fora de `try` (`?priority=abc` → 500); routes/user_routes.py:61 e 106 — regex de email duplicada (e triplicada em utils/helpers.py:21); routes/user_routes.py:102-103 — `PUT /users` aceita `name` vazio sem validar; routes/user_routes.py:124-125 — `active` aceito sem checar bool; routes/report_routes.py:173-180 e 196-202 — `color` nunca validado embora `is_valid_color` exista em utils/helpers.py:52; utils/helpers.py:57-108 — `process_task_data` implementa a validação de task e ninguém a chama
Description: As validações vivem inline em cada handler, divergem entre criar e atualizar, e os validadores/constantes de `utils/helpers.py` não são usados por nenhuma rota.
Impact: 500 em vez de 400 para entrada malformada; regras diferentes dependendo do endpoint; correções precisam ser replicadas.
Recommendation: `validators/` (task, user, category) reutilizados por criar e atualizar, lançando `ValidationError`; constantes de domínio centralizadas; conversões numéricas com tratamento → PB-11

### #11 [MEDIUM] APIs deprecated: datetime.utcnow, Model.query.get, debug no código, dependência com advisory (AP-12)
File: models/task.py:15-16
Locations: ver tabela "Deprecated APIs" abaixo (40 ocorrências de `datetime.utcnow()`, 14 de `Model.query.get()`, 1 de `app.run(debug=True)`, Flask-CORS 4.0.0)
Description: `datetime.utcnow()` emite `DeprecationWarning` desde o Python 3.12 (o ambiente local é 3.13) e aparece em models, rotas, service, helpers e seed. `Model.query.get()` é API legada do SQLAlchemy 2.0 (`LegacyAPIWarning`). Flask-CORS 4.0.0 tem advisory conhecido (CVE-2024-1681, log injection, corrigido em 4.0.1).
Impact: Warnings em runtime hoje, remoção futura; comportamento naive/aware inconsistente ao migrar.
Recommendation: `utc_now()` centralizado em `utils/datetime.py` usando `datetime.now(timezone.utc)`; `db.session.get(Model, id)`; debug via ambiente; registrar bump de Flask-CORS para 4.0.1+ como recomendação (sem alterar o manifesto na Fase 3) → PB-12

### #12 [MEDIUM] Duplicação de código e helpers existentes ignorados (AP-13)
File: routes/task_routes.py:30-39
Locations: routes/task_routes.py:30-39, 71-80, 284-287; routes/user_routes.py:171-180; routes/report_routes.py:34-37, 132-135 — regra "atrasada" copiada 6 vezes enquanto `Task.is_overdue()` (models/task.py:50-60) existe e não é chamado; routes/task_routes.py:17-28 e routes/user_routes.py:162-169 — serialização manual de Task repetindo `Task.to_dict()` (models/task.py:23-36); routes/user_routes.py:15-23 — serialização manual de User; routes/task_routes.py:296, routes/report_routes.py:67 e 151 — `round((x / total) * 100, 2) if total > 0 else 0` 3 vezes enquanto `calculate_percentage` existe (utils/helpers.py:14-17); routes/report_routes.py:7 — importa `format_date` e `calculate_percentage` e não usa; models/task.py:38-48 — `validate_status`/`validate_priority` sem chamador; models/user.py:34-38 — `is_admin` sem chamador; services/notification_service.py — classe inteira sem chamador; utils/helpers.py:9-116 — 9 de 10 funções e todas as 7 constantes sem chamador
Description: O projeto tem as abstrações certas (métodos de model, helpers, constantes, service) mas as rotas reimplementam tudo inline.
Impact: Correção da regra de atraso precisa ser replicada em 6 lugares; divergência silenciosa (ex.: `GET /users/<id>/tasks` serializa menos campos que `to_dict`).
Recommendation: Serialização única por entidade (`to_dict` ou serializer); `is_overdue()` como única fonte da regra; relatórios usam `calculate_percentage`; remover helpers que continuarem sem uso → PB-13, PB-14

### #13 [MEDIUM] Integridade: exclusão de pai sem tratar filhos e cascata manual na rota (AP-14)
File: routes/report_routes.py:211-223
Locations: routes/report_routes.py:217-219 — `DELETE /categories/<id>` apaga a categoria sem tratar tasks que a referenciam; models/task.py:13-14 — `ForeignKey` sem `ondelete` e relationships sem `cascade`; routes/user_routes.py:140-142 — cascata de tasks feita manualmente no handler, item a item
Description: SQLite não aplica FK por padrão e os relationships não definem política explícita de cascata. Ao apagar uma categoria, o SQLAlchemy anula `tasks.category_id` apenas como efeito implícito do `backref` (comportamento padrão não documentado no código); qualquer acesso que contorne o ORM deixaria órfãos. A exclusão de usuário faz a cascata "na mão" dentro da rota, item a item.
Impact: Política de integridade invisível e inconsistente entre entidades (implícita para categoria, manual na rota para usuário); `GET /tasks` devolve `category_name: null` para tasks cuja categoria foi apagada sem que isso seja uma decisão explícita do domínio.
Note: Correção pós-Fase 3 — a versão original deste finding afirmava que havia órfãos de fato; a verificação do código confirmou que o ORM já anulava a FK implicitamente. O problema real é a ausência de política explícita.
Recommendation: Definir no model a política (`cascade='all, delete-orphan'` para user→tasks; `ondelete='SET NULL'` + `passive_deletes` para category→tasks, ou limpar `category_id` no service) e habilitar `PRAGMA foreign_keys=ON` no engine SQLite → PB-15

### #14 [LOW] Magic numbers e magic strings (AP-15)
File: routes/task_routes.py:110-113
Locations: routes/task_routes.py:110, 177; models/task.py:39; utils/helpers.py:75 — lista de status inline 4 vezes; routes/user_routes.py:71, 120 — lista de roles inline; routes/task_routes.py:96, 99, 167, 169; utils/helpers.py:64 — limites 3/200 de título; routes/task_routes.py:113, 182; models/task.py:46; utils/helpers.py:84 — faixa 1..5 de prioridade; routes/user_routes.py:64, 115 — mínimo 4 da senha; routes/report_routes.py:45 — `timedelta(days=7)`; routes/report_routes.py:129 — `priority <= 2` como "alta prioridade"; models/category.py:10 e routes/report_routes.py:180 — `'#000000'`
Description: As constantes `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY` e `DEFAULT_COLOR` existem em utils/helpers.py:110-116 e não são importadas por ninguém.
Impact: Alterar um status ou limite exige caçar literais em 4 arquivos.
Recommendation: Módulo `constants.py` (ou enum) de domínio consumido por validators, models e services → PB-13

### #15 [LOW] Nomenclatura abreviada e genérica (AP-16)
File: routes/report_routes.py:24-28
Locations: routes/report_routes.py:24-28 — `p1..p5`; routes/task_routes.py:16, 268, 283 e routes/user_routes.py:14, 37, 141, 161 e routes/report_routes.py:33, 55, 59, 119, 161 — `t`, `u`, `c`, `cat`; models/task.py:45 — parâmetro `p`; models/user.py:27 — `pwd`; models/category.py:14 — `d`; seed.py:78 — `td`; utils/helpers.py — módulo `helpers` como depósito de validação, constantes e logging
Description: Variáveis de uma letra em loops de 20+ linhas e nomes genéricos para módulos centrais.
Impact: Legibilidade; dificulta revisão dos relatórios de 90 linhas.
Recommendation: Renomear internamente (`task`, `user`, `category`, `priority_counts`) mantendo o contrato externo → PB-16

### #16 [LOW] Imports não usados e dependências fantasmas (AP-17)
File: requirements.txt:4-6
Locations: requirements.txt:4-6 — `marshmallow`, `requests`, `python-dotenv` sem nenhum import no projeto; app.py:7 — `os, sys, json` não usados; routes/task_routes.py:7 — `json, os, sys, time` não usados; routes/user_routes.py:6 — `hashlib, json` não usados; routes/report_routes.py:7-8 — `format_date, calculate_percentage, json` não usados; models/task.py:3 — `json`; utils/helpers.py:3-7 — `os, json, sys, math, hashlib` não usados; services/notification_service.py — módulo nunca importado
Description: Três pacotes pinados sem uso e imports mortos em 7 dos 15 arquivos.
Impact: Manifesto mente sobre a stack real; ruído em cada arquivo.
Recommendation: Remover imports mortos; decidir o destino das dependências fantasmas (usar `python-dotenv` em PB-01 ou remover do manifesto; `marshmallow` e `requests` removidos salvo uso futuro declarado) → PB-16

### #17 [LOW] Logging via print dentro de handlers e service (AP-18)
File: routes/task_routes.py:149
Locations: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147 — `print` com id e nome de usuário em handlers; services/notification_service.py:21, 24 — `print` com email do destinatário; utils/helpers.py:39-41 — `log_action` baseado em `print`
Description: Saída de debug em stdout em vez de `logging`, incluindo email (PII) e exceções completas.
Impact: Sem níveis, sem destino configurável; PII em logs.
Recommendation: `logging.getLogger(__name__)` com nível por ambiente; mensagens sem PII → PB-16

## Deprecated APIs
| API | Location(s) | Modern equivalent |
|---|---|---|
| `datetime.utcnow()` | models/category.py:11; models/task.py:15, 16, 52; models/user.py:14; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38; seed.py:66, 67, 69, 70, 74 | `datetime.now(timezone.utc)` centralizado em `utc_now()` |
| `Model.query.get(id)` | routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `db.session.get(Model, id)` |
| `Model.query.filter_by(...).all()/.count()` | routes/task_routes.py:247-266, 275-281; routes/user_routes.py:35, 67, 109, 140, 159, 197; routes/report_routes.py:15-56, 109, 163 | `db.session.execute(db.select(Model).filter_by(...)).scalars()` / `func.count` |
| `app.run(debug=True)` no código | app.py:34 | `FLASK_DEBUG` via ambiente |
| Flask-CORS 4.0.0 (CVE-2024-1681) | requirements.txt:3 | Flask-CORS ≥ 4.0.1 (bump a confirmar fora da Fase 3) |

## Endpoint Contract (from Phase 1)
| # | Method | Path | Handler | Location |
|---|--------|------|---------|----------|
| 1 | GET | /health | health | app.py:22 |
| 2 | GET | / | index | app.py:26 |
| 3 | GET | /tasks | get_tasks | routes/task_routes.py:11 |
| 4 | GET | /tasks/<int:task_id> | get_task | routes/task_routes.py:65 |
| 5 | POST | /tasks | create_task | routes/task_routes.py:85 |
| 6 | PUT | /tasks/<int:task_id> | update_task | routes/task_routes.py:156 |
| 7 | DELETE | /tasks/<int:task_id> | delete_task | routes/task_routes.py:225 |
| 8 | GET | /tasks/search | search_tasks | routes/task_routes.py:240 |
| 9 | GET | /tasks/stats | task_stats | routes/task_routes.py:273 |
| 10 | GET | /users | get_users | routes/user_routes.py:10 |
| 11 | GET | /users/<int:user_id> | get_user | routes/user_routes.py:27 |
| 12 | POST | /users | create_user | routes/user_routes.py:42 |
| 13 | PUT | /users/<int:user_id> | update_user | routes/user_routes.py:92 |
| 14 | DELETE | /users/<int:user_id> | delete_user | routes/user_routes.py:134 |
| 15 | GET | /users/<int:user_id>/tasks | get_user_tasks | routes/user_routes.py:153 |
| 16 | POST | /login | login | routes/user_routes.py:185 |
| 17 | GET | /reports/summary | summary_report | routes/report_routes.py:12 |
| 18 | GET | /reports/user/<int:user_id> | user_report | routes/report_routes.py:103 |
| 19 | GET | /categories | get_categories | routes/report_routes.py:157 |
| 20 | POST | /categories | create_category | routes/report_routes.py:167 |
| 21 | PUT | /categories/<int:cat_id> | update_category | routes/report_routes.py:190 |
| 22 | DELETE | /categories/<int:cat_id> | delete_category | routes/report_routes.py:211 |

## Refactoring Strategy Preview
Strategy: B — realocar responsabilidades
Rationale: As pastas por camada já existem (models/, routes/, services/, utils/); falta criar config, controllers, validators e error handler, e mover regra, queries e serialização das rotas para o lugar certo, reaproveitando o que já existe.

================================
Total: 17 findings
================================
