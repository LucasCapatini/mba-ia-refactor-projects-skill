================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.13 + Flask 3.1.1 (pin; ambiente local tem 3.0.0 instalado) + flask-cors 5.0.1 + sqlite3 (SQL cru)
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-17
Architecture: Monolito plano — 4 módulos na raiz, sem pacotes por camada; handlers executam SQL direto; conexão, schema e seeds no mesmo singleton

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 4
Total: 17 findings

## Findings

### #1 [CRITICAL] Segredos e credenciais hardcoded e expostos em respostas (AP-01)
File: app.py:7
Locations: app.py:7 — `SECRET_KEY = "minha-chave-super-secreta-123"` literal; controllers.py:285-289 — `/health` devolve `secret_key`, `debug`, `db_path` e `ambiente` no JSON; database.py:75-79 — senhas de seed (`admin123`, `123456`, `senha123`) em texto puro no código
Description: A chave secreta da aplicação está escrita no código e, pior, é devolvida a qualquer cliente anônimo pelo endpoint público `/health`, junto com o caminho do banco e o estado de debug. Não existe nenhuma leitura de `os.environ`/`getenv` no projeto.
Impact: Qualquer pessoa que acesse `/health` obtém a `SECRET_KEY` (forja de sessões/cookies assinados); segredo versionado no git não pode ser rotacionado sem novo deploy.
Recommendation: Criar módulo de config (`src/config.py`) lendo `SECRET_KEY`, `DEBUG`, `DB_PATH`, `PORT` do ambiente com defaults seguros e `.env.example`; remover `secret_key`, `debug`, `db_path` e `ambiente` fixo da resposta do health → PB-01, PB-16

### #2 [CRITICAL] God Module: roteamento, dados, regra, schema e seeds misturados (AP-03)
File: app.py:47-78
Locations: app.py:1-88 — composition root + roteamento + 2 handlers inline com SQL + entry point; controllers.py:1-292 — handlers de 3 entidades + validação + regras de domínio (categorias, status) + "integrações" por `print` (linhas 208-210, 248-250) + SQL direto em `health_check` (264-292); models.py:1-314 — acesso a dados de 4 tabelas + regra de negócio (cálculo de total e baixa de estoque em 133-169, faixas de desconto em 256-262) + serialização manual; database.py:7-86 — conexão + DDL + seeds em uma única função
Description: Nenhum arquivo tem uma responsabilidade só. `controllers.py` importa `get_db` e executa SQL, `models.py` decide regras de negócio (desconto, estoque) e `app.py` abriga handlers administrativos completos. Os quatro módulos cobrem os domínios produto, usuário e pedido simultaneamente.
Impact: Impossível testar regra de pedido ou relatório sem subir Flask e SQLite; qualquer mudança em uma entidade exige editar os mesmos quatro arquivos.
Recommendation: Estratégia A — criar pacote `src/` com `config`, `database`, `models/` (um por entidade), `services/` (pedido, relatório, auth), `controllers/`, `routes/` e `middlewares/`, separando por camada e por domínio → PB-03, PB-05, PB-10

### #3 [CRITICAL] SQL Injection e execução de SQL arbitrário (AP-02)
File: app.py:59-78
Locations: app.py:59-78 — `POST /admin/query` executa `dados["sql"]` sem restrição e faz commit; models.py:28 — `WHERE id = " + str(id)`; models.py:47-50 — INSERT produto por concatenação de `nome`, `descricao`, `categoria`; models.py:57-61 — UPDATE produto; models.py:68 — DELETE produto; models.py:92 — SELECT usuário; models.py:109-111 — login com `email` e `senha` concatenados; models.py:126-129 — INSERT usuário; models.py:140, 148-151, 155-166 — criar_pedido; models.py:174, 188, 192, 220, 224 — listagens de pedidos; models.py:279-281 — UPDATE status; models.py:289-299 — busca com `termo`, `categoria`, `preco_min`, `preco_max` concatenados em `LIKE`/`WHERE`
Description: 100% das queries do módulo de dados são montadas por concatenação de strings com valores vindos do body ou da query string (ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`). Nenhuma usa placeholders `?`. Além disso, o endpoint `/admin/query` executa qualquer SQL recebido, sem autenticação.
Impact: Bypass de login com `' OR '1'='1' --`; leitura, alteração e `DROP` de qualquer tabela via `/produtos/busca?q=` ou diretamente via `/admin/query`.
Recommendation: Bind parameters (`?`) em todas as queries dos novos `models/`; `/admin/query` mantido registrado mas respondendo 403 por padrão, liberado só com flag de ambiente (`ADMIN_QUERY_ENABLED`) → PB-02

### #4 [CRITICAL] Senhas armazenadas e comparadas em texto puro, devolvidas em respostas (AP-04)
File: database.py:75-83
Locations: database.py:75-83 — seeds inserem senhas em claro; models.py:83 e models.py:99 — campo `senha` incluído na serialização de `GET /usuarios` e `GET /usuarios/<id>`; models.py:109-111 — login compara `senha = '<texto>'` direto no SQL; models.py:126-129 — `criar_usuario` grava a senha recebida sem hash
Description: Não há nenhum uso de `werkzeug.security`, `hashlib` com salt ou equivalente. A senha é persistida como veio no body e devolvida integralmente nas listagens públicas de usuários.
Impact: `GET /usuarios` expõe credenciais de todos os usuários, inclusive do admin; comprometimento de contas e de senhas reutilizadas em outros serviços.
Recommendation: `generate_password_hash`/`check_password_hash` do Werkzeug (já é dependência transitiva do Flask) em criação e login; serialização de usuário sem o campo `senha`; recriar o banco local após a mudança de esquema de senha → PB-04, PB-14

### #5 [HIGH] Configuração hardcoded e sem separação por ambiente (AP-08)
File: app.py:7-8
Locations: app.py:7-8 — `SECRET_KEY` e `DEBUG = True` em `app.config`; app.py:88 — `app.run(host="0.0.0.0", port=5000, debug=True)`; database.py:5 — `db_path = "loja.db"` fixo; controllers.py:286 — `"ambiente": "producao"` fixo
Description: Debug ligado em código e servidor exposto em `0.0.0.0` por padrão; porta, caminho do banco e ambiente são literais. Zero ocorrências de `os.environ`, `getenv` ou `load_dotenv` no projeto.
Impact: Debugger do Werkzeug (execução remota de código via console) ativo em qualquer deploy; impossível apontar para outro banco ou porta sem editar código.
Recommendation: `src/config.py` com classe/objeto lendo `FLASK_DEBUG`, `PORT`, `HOST`, `DB_PATH`, `SECRET_KEY` do ambiente com defaults seguros (debug desligado, host `127.0.0.1`); `.env.example` documentando as variáveis → PB-01

### #6 [HIGH] Lógica de negócio e acesso a dados em handlers (Fat Controller) (AP-05)
File: app.py:47-78
Locations: app.py:47-57 — `reset_database` executa 4 DELETEs direto; app.py:59-78 — `executar_query` executa SQL e decide commit; controllers.py:24-62 — `criar_produto` com 10 `return jsonify(...), 400`, lista de categorias e regras de faixa inline; controllers.py:64-96 — `atualizar_produto` repete a validação; controllers.py:188-220 — `criar_pedido` interpreta `"erro" in resultado` e dispara "email/SMS/push" por `print`; controllers.py:237-255 — regras de notificação por status; controllers.py:264-292 — `health_check` abre cursor e roda 4 queries
Description: Os handlers validam, aplicam regra de domínio, acessam o banco e montam a resposta no mesmo bloco. O "contrato" de erro entre `models.criar_pedido` e o controller é um dict com chave `"erro"`, não uma exceção.
Impact: Regras (categorias válidas, transições de status, notificações) não são testáveis sem HTTP e divergem entre criar/atualizar.
Recommendation: Controllers finos que só traduzem HTTP ↔ serviço; regras em `services/` (`pedido_service`, `relatorio_service`, `auth_service`); validação em `validators/`; health e reset em `services/admin_service` → PB-05, PB-11

### #7 [HIGH] Conexão singleton global compartilhada entre threads (AP-06)
File: database.py:4-11
Locations: database.py:4 — `db_connection = None` no nível de módulo; database.py:8-10 — `global db_connection` e `sqlite3.connect(db_path, check_same_thread=False)`
Description: Uma única conexão SQLite é criada na primeira chamada e reutilizada por todas as requisições do servidor multi-thread do Flask, com a proteção de thread desligada. Cursores concorrentes compartilham a mesma transação implícita.
Impact: Condições de corrida em `criar_pedido` (leitura de estoque e UPDATE sem isolamento), commits parciais de uma requisição afetando outra, impossibilidade de testes paralelos.
Recommendation: Conexão por requisição via `flask.g` + `teardown_appcontext`, aberta por `get_connection()` em `src/database.py` sem estado global → PB-06

### #8 [HIGH] Efeitos colaterais no import e ausência de composition root (AP-07)
File: database.py:7-86
Locations: database.py:14-53 — `CREATE TABLE` dentro de `get_db()`; database.py:56-84 — seeds (`executemany`) dentro de `get_db()`; app.py:4, controllers.py:3, models.py:1 — `from database import get_db` importado diretamente por composition root, controllers e models; app.py:6-30 — `app` construída no nível de módulo, sem `create_app()`
Description: A primeira chamada de `get_db()` (que pode vir de qualquer handler) cria o schema e popula o banco. Não há `init_db()` nem `seed()` explícitos; a instância `app` é um global de módulo com rotas registradas no import.
Impact: Importar `controllers` ou `models` para testar já abre `loja.db` no diretório corrente; ordem de inicialização dependente de qual endpoint é chamado primeiro.
Recommendation: `create_app(config)` como application factory em `src/app.py`; `init_db(app)` e `seed_db()` explícitos chamados pelo entry point `app.py`; controllers sem acesso à conexão → PB-06, PB-07

### #9 [MEDIUM] Tratamento de erros duplicado, vazando detalhes e sem handler central (AP-10)
File: app.py:77-78
Locations: app.py:77-78 — `except Exception as e: return jsonify({"erro": str(e)}), 500`; controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292 — 16 blocos `try/except Exception` idênticos devolvendo `str(e)`; app.py:61-62, controllers.py:169-171, controllers.py:239-240 — `request.get_json()` seguido de `.get(` sem checar `None`; zero `@app.errorhandler`
Description: Todo handler repete o mesmo `try/except` genérico que envia a mensagem interna da exceção (incluindo erros de SQL) ao cliente. Body ausente ou não JSON em `/login`, `/pedidos/<id>/status` e `/admin/query` gera `AttributeError` → 500.
Impact: Vazamento de estrutura do banco e de stack nas respostas; respostas de erro inconsistentes (`erro` com e sem `sucesso`); 500 onde deveria ser 400.
Recommendation: Exceções de domínio (`NotFoundError`, `ValidationError`, `AuthError`) + `@app.errorhandler` central em `middlewares/error_handler.py` devolvendo `{"erro": ...}` com os mesmos códigos de hoje e 500 genérico com log → PB-08

### #10 [MEDIUM] Validação de entrada ausente, duplicada e divergente (AP-11)
File: controllers.py:28-54
Locations: controllers.py:28-54 vs controllers.py:72-91 — bloco de presença/faixa copiado em criar e atualizar, mas o PUT não valida tamanho de `nome` nem `categoria`; controllers.py:43-46 — `preco < 0` sem checar tipo (string → `TypeError` → 500); controllers.py:118-121 — `float(preco_min)` fora de `try` específico; controllers.py:153-158 — usuário sem validação de formato de email nem política de senha; controllers.py:195-203 e models.py:139-146 — itens do pedido sem validar `produto_id`/`quantidade` (ausência → `KeyError` → 500; quantidade negativa ou zero aceita e aumenta o estoque)
Description: As validações existem apenas em alguns handlers, são copiadas com divergências e dependem do `except Exception` genérico para erros de tipo.
Impact: Dados inconsistentes (produto com categoria inválida via PUT, estoque incrementado por quantidade negativa); 500 em vez de 400 para entradas malformadas.
Recommendation: `validators/produto_validator.py`, `usuario_validator.py`, `pedido_validator.py` reutilizados por criar/atualizar, lançando `ValidationError` com as mesmas mensagens atuais → PB-11

### #11 [MEDIUM] Integridade de dados: sem FK, sem transação explícita, órfãos (AP-14)
File: database.py:14-53
Locations: database.py:14-53 — tabelas `pedidos.usuario_id`, `itens_pedido.pedido_id`, `itens_pedido.produto_id` declaradas como `INTEGER` sem `FOREIGN KEY`/`REFERENCES`; models.py:133-169 — `criar_pedido` faz 1 INSERT de pedido + N INSERTs de itens + N UPDATEs de estoque com um único `commit()` no final e sem `rollback` em falha; models.py:65-70 — `deletar_produto` não trata `itens_pedido` associados; app.py:51-54 — reset deleta na ordem certa mas sem transação
Description: O banco não conhece as relações entre tabelas e `PRAGMA foreign_keys` nunca é ativado. Uma exceção no meio de `criar_pedido` deixa o pedido inserido sem itens ou estoque parcialmente baixado na conexão global compartilhada.
Impact: Pedidos para usuários inexistentes, itens apontando para produtos apagados (`"produto_nome": "Desconhecido"` em models.py:196 já contorna isso), estoque inconsistente após falha.
Recommendation: `PRAGMA foreign_keys = ON` por conexão, `FOREIGN KEY ... REFERENCES` no DDL, `BEGIN`/`commit`/`rollback` explícitos no `pedido_service` → PB-15

### #12 [MEDIUM] Duplicação de código e serialização manual repetida (AP-13)
File: models.py:12-21
Locations: models.py:12-21, 31-40, 304-313 — dict de produto montado 3 vezes campo a campo; models.py:79-86, 95-102 — dict de usuário 2 vezes; models.py:171-201 vs 203-233 — `get_pedidos_usuario` e `get_todos_pedidos` são 30 linhas idênticas exceto o `WHERE`; controllers.py:28-50 vs 72-91 — validação duplicada
Description: Não existe uma função de serialização por entidade; cada query repete a montagem do dict. As duas funções de listagem de pedidos diferem em uma linha.
Impact: Adicionar uma coluna exige editar 3 a 5 pontos; correções divergem silenciosamente (o PUT já diverge do POST).
Recommendation: `to_dict()`/`from_row()` por model (`Produto`, `Usuario`, `Pedido`), uma única função `listar_pedidos(usuario_id=None)` → PB-13, PB-14

### #13 [MEDIUM] Query N+1 e consultas em loop (AP-09)
File: models.py:139-166
Locations: models.py:139-146 e 154-166 — `criar_pedido` faz 1 SELECT por item duas vezes (validação e inserção), mais 1 INSERT e 1 UPDATE por item; models.py:177-200 e 209-232 — para cada pedido, `cursor2` busca itens e, para cada item, `cursor3` busca o nome do produto (1 + P + P×I queries); models.py:239-254 — relatório roda 5 `COUNT`/`SUM` separados sobre a mesma tabela `pedidos`
Description: Listagens de pedidos executam uma query por pedido e outra por item, em vez de um JOIN. O relatório usa 5 full scans quando uma agregação condicional resolve.
Impact: Latência de `GET /pedidos` cresce com pedidos × itens; carga desnecessária no SQLite single-writer.
Recommendation: JOIN `pedidos ⋈ itens_pedido ⋈ produtos` com agrupamento em Python no `pedido_model`; uma query com `SUM(CASE WHEN status = ...)` no `relatorio_model`; `IN (...)` para validar os produtos do pedido de uma vez → PB-09

### #14 [LOW] Logging via print e mensagens de implementação ao cliente (AP-18)
File: app.py:56
Locations: app.py:56, 83-86 — `print` de "BANCO RESETADO" e banner de boot; app.py:57 — resposta "Banco de dados resetado"; controllers.py:8, 11, 57, 61, 106, 208-210, 219, 248, 250 — `print` de debug e de "integrações" (email/SMS/push) em handlers; controllers.py:161, 179, 182 — `print` com e-mail do usuário (PII) em criação e login; controllers.py:286 — `"ambiente": "producao"` fixo na resposta
Description: 19 chamadas a `print` fazem o papel de logger, incluindo e-mails de usuários em tentativas de login (sucesso e falha).
Impact: Sem níveis, sem formatação, sem controle por ambiente; PII em stdout; respostas revelam detalhes operacionais.
Recommendation: `logging.getLogger(__name__)` com nível por config; notificações em `services/notificacao_service.py` sem PII no log; manter as chaves de resposta → PB-16

### #15 [LOW] Nomenclatura ruim e sombra de builtins (AP-16)
File: controllers.py:14
Locations: controllers.py:14, 64, 98, 136 e models.py:24, 54, 65, 89 — parâmetro `id` sombreia o builtin `id()`; models.py:187-193, 219-225 — `cursor2`, `cursor3`, `prod`; módulo `models.py` contém funções soltas, não entidades; `dados`/`resultado` genéricos em todos os handlers
Description: Nomes de parâmetro e de cursores numerados dificultam leitura e escondem o N+1.
Impact: Legibilidade; risco de bug ao precisar do builtin `id` dentro das funções.
Recommendation: `produto_id`, `usuario_id` internamente (mantendo `<int:id>` no path do contrato), cursores eliminados pelo JOIN, classes de model nomeadas por entidade → PB-16

### #16 [LOW] Magic numbers e magic strings (AP-15)
File: controllers.py:47-54
Locations: controllers.py:47-49 — limites `2` e `200` de tamanho do nome; controllers.py:52 — lista de categorias inline; controllers.py:242 — lista de status inline; models.py:257-262 — faixas `10000/5000/1000` e taxas `0.1/0.05/0.02` de desconto; app.py:36 e controllers.py:285 — versão `"1.0.0"` repetida; app.py:88 — porta `5000`
Description: Regras de domínio (categorias, status, faixas de desconto) vivem como literais dentro de handlers e queries.
Impact: Alterar uma categoria ou faixa exige localizar o literal; status aceito no PUT não é o mesmo conjunto usado pelo relatório.
Recommendation: `src/constants.py` (ou `domain/`) com `CATEGORIAS_VALIDAS`, `STATUS_PEDIDO`, `FAIXAS_DESCONTO`, `NOME_MIN/MAX`, `APP_VERSION` → PB-13

### #17 [LOW] Imports não usados (AP-17)
File: database.py:2
Locations: database.py:2 — `import os` sem nenhum uso; models.py:2 — `import sqlite3` sem nenhum uso (a conexão vem de `get_db`)
Description: Dois imports mortos. O manifesto (`flask`, `flask-cors`) está alinhado ao uso real.
Impact: Ruído; sugere intenção não concretizada de ler config do ambiente.
Recommendation: Remover ao migrar os módulos para `src/` → PB-16

## Deprecated APIs
| API | Location(s) | Modern equivalent |
|---|---|---|
| `app.run(debug=True)` no código | app.py:88 | Debug via variável de ambiente (`FLASK_DEBUG`) lida em `config.py` (idioma legado, coberto pelo finding #5) |
Nenhuma API removida/deprecated do Python 3.13 ou do Flask 3.x foi encontrada no código (`utcnow`, `before_first_request`, `FLASK_ENV`, `safe_str_cmp`, `distutils`: 0 ocorrências). As colunas `TIMESTAMP` usam `CURRENT_TIMESTAMP` do SQLite sem `detect_types`, então os adaptadores de `datetime` deprecated do `sqlite3` não entram em jogo.

## Endpoint Contract (from Phase 1)
| # | Method | Path | Handler | Location |
|---|--------|------|---------|----------|
| 1 | GET | /produtos | listar_produtos | app.py:11 → controllers.py:5 |
| 2 | GET | /produtos/busca | buscar_produtos | app.py:12 → controllers.py:111 |
| 3 | GET | /produtos/<int:id> | buscar_produto | app.py:13 → controllers.py:14 |
| 4 | POST | /produtos | criar_produto | app.py:14 → controllers.py:24 |
| 5 | PUT | /produtos/<int:id> | atualizar_produto | app.py:15 → controllers.py:64 |
| 6 | DELETE | /produtos/<int:id> | deletar_produto | app.py:16 → controllers.py:98 |
| 7 | GET | /usuarios | listar_usuarios | app.py:18 → controllers.py:128 |
| 8 | GET | /usuarios/<int:id> | buscar_usuario | app.py:19 → controllers.py:136 |
| 9 | POST | /usuarios | criar_usuario | app.py:20 → controllers.py:146 |
| 10 | POST | /login | login | app.py:21 → controllers.py:167 |
| 11 | POST | /pedidos | criar_pedido | app.py:23 → controllers.py:188 |
| 12 | GET | /pedidos | listar_todos_pedidos | app.py:24 → controllers.py:229 |
| 13 | GET | /pedidos/usuario/<int:usuario_id> | listar_pedidos_usuario | app.py:25 → controllers.py:222 |
| 14 | PUT | /pedidos/<int:pedido_id>/status | atualizar_status_pedido | app.py:26 → controllers.py:237 |
| 15 | GET | /relatorios/vendas | relatorio_vendas | app.py:28 → controllers.py:257 |
| 16 | GET | /health | health_check | app.py:30 → controllers.py:264 |
| 17 | GET | / | index | app.py:32 |
| 18 | POST | /admin/reset-db | reset_database | app.py:47 |
| 19 | POST | /admin/query | executar_query | app.py:59 |

Campos de body/query que fazem parte do contrato: `/produtos` POST/PUT → `nome`, `descricao`, `preco`, `estoque`, `categoria`; `/produtos/busca` → `q`, `categoria`, `preco_min`, `preco_max`; `/usuarios` POST → `nome`, `email`, `senha`; `/login` → `email`, `senha`; `/pedidos` POST → `usuario_id`, `itens[{produto_id, quantidade}]`; `/pedidos/<id>/status` PUT → `status`; `/admin/query` → `sql`. Chaves de topo de sucesso: `dados`, `sucesso`, `mensagem`, `total` (busca), e `status`/`database`/`counts`/`versao` no health.

## Refactoring Strategy Preview
Strategy: A — criar camadas
Rationale: Monolito plano sem nenhum diretório por camada; é preciso criar `src/` com config, database, models, services, validators, controllers, routes e middlewares do zero, mantendo `python app.py` como entry point.

================================
Total: 17 findings
================================
