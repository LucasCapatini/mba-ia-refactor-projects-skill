# Referência — Análise de projeto (Fase 1)

Heurísticas para detectar linguagem, framework, banco de dados, papel de cada arquivo e arquitetura atual **sem depender de nomes de arquivo específicos**. Tudo aqui é somente leitura.

## 1. Detecção de linguagem e framework pelo manifesto

| Manifesto na raiz | Linguagem | Como achar o framework e a versão |
|---|---|---|
| `requirements.txt` | Python | Linhas `flask==`, `fastapi==`, `django==`, `bottle`, `tornado`. Versão = pin. Sem pin: `pip show <pkg>`. |
| `pyproject.toml` / `Pipfile` | Python | Seções `[project.dependencies]`, `[tool.poetry.dependencies]`, `[packages]`. |
| `package.json` | Node.js | `dependencies`: `express`, `fastify`, `koa`, `@nestjs/core`, `hapi`. Versão real: Grep pontual no lockfile por `"node_modules/express"` ou `express@` (nunca leia o lockfile inteiro); fallback `npm ls express --depth=0`. Campo `type: module` indica ESM. |
| `go.mod` | Go | `gin-gonic/gin`, `labstack/echo`, `gofiber/fiber`, `net/http` puro. |
| `pom.xml` / `build.gradle` | Java/Kotlin | `spring-boot-starter-web`, `quarkus`, `micronaut`. |
| `*.csproj` | C# | `Microsoft.AspNetCore`, `Sdk="Microsoft.NET.Sdk.Web"`. |
| `Gemfile` | Ruby | `rails`, `sinatra`. |
| `composer.json` | PHP | `laravel/framework`, `slim/slim`, `symfony`. |

Versão da linguagem: `python --version`, `node --version` (somente leitura). Registre se o manifesto exige algo (`engines`, `requires-python`).

Dependências relevantes para o relatório: ORM/driver de banco, CORS, validação, auth, dotenv. Marque dependências pinadas que **não aparecem em nenhum import** (sinal de AP-17).

## 2. Inventário de código-fonte

Glob por extensão da linguagem detectada (`**/*.py`, `**/*.js`, `**/*.ts`, `**/*.go`, ...), excluindo: `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `.git/`, `.claude/`, `dist/`, `build/`, `coverage/`, `*.min.js`, `*.db`, `*.sqlite`.

Conte arquivos e linhas (`wc -l`). Arquivos de teste (`test_*.py`, `*.test.js`, `tests/`, `__tests__/`) contam separadamente. Arquivos `*.http`, `*.rest`, `openapi*`, `swagger*`, `postman*` são **documentação de contrato** e devem ser lidos.

## 3. Detecção de banco de dados

| Sinal (Grep) | Banco / camada |
|---|---|
| `import sqlite3`, `require('sqlite3')`, `better-sqlite3`, `node:sqlite` | SQLite com SQL cru |
| `sqlite:///` em string de conexão | SQLite via ORM |
| `from flask_sqlalchemy import`, `db.Model`, `db.Column` | SQLAlchemy (Flask-SQLAlchemy) |
| `from sqlalchemy import`, `declarative_base`, `Mapped[` | SQLAlchemy puro |
| `psycopg2`, `asyncpg`, `pg`, `postgres://` | PostgreSQL |
| `pymysql`, `mysql2`, `mysql://` | MySQL |
| `pymongo`, `mongoose.Schema`, `mongodb://` | MongoDB |
| `Sequelize`, `prisma`, `knex`, `typeorm` | ORM Node |
| `CREATE TABLE` | schema inline (anote onde está: migration, módulo de BD ou dentro de uma classe de rotas) |

Tabelas/coleções: extraia de `CREATE TABLE <nome>`, `__tablename__ = '<nome>'`, `class <Nome>(db.Model)`, `mongoose.model('<Nome>'`. Liste-as no resumo.

## 4. Papel de cada arquivo (pelo conteúdo, nunca pelo nome)

Classifique cada arquivo-fonte em um ou mais papéis. Um arquivo com três ou mais papéis é candidato a God Class/Module (AP-03).

| Papel | Sinais Python | Sinais Node |
|---|---|---|
| Entry point | `if __name__ == "__main__"`, `app.run(` | `app.listen(`, `require.main === module`, `"main"`/`"start"` do `package.json` |
| Composition root | `Flask(__name__)`, `register_blueprint`, `create_app` | `express()`, `app.use(`, `createApp` |
| Roteamento | `@app.route`, `@bp.route`, `add_url_rule`, `Blueprint(` | `app.get(`, `router.post(`, `express.Router()` |
| Controller/handler | funções que usam `request.get_json()`, `request.args`, `jsonify` | callbacks `(req, res)` que leem `req.body`, `req.params` e chamam `res.json/send/status` |
| Model / acesso a dados | `cursor.execute`, `db.session`, `class X(db.Model)`, `.query.` | `db.run/get/all`, `Model.findAll`, `prisma.x` |
| Service / regra de negócio | cálculos, validações de domínio, orquestração sem `request` | idem sem `req`/`res` |
| Config | `app.config[`, `os.environ`, `load_dotenv` | `process.env`, objeto `config = {` |
| Middleware | `@app.before_request`, `@app.errorhandler`, `CORS(` | `app.use((err, req, res, next)`, `express.json()` |
| Utilitário | funções puras genéricas (format, parse, validate) | idem |
| Seed / script | `insert`, `executemany`, `db.session.add` em script sem rotas | `INSERT INTO` em bloco de inicialização |

Anote **misturas**: handler que executa SQL (roteamento + dados), módulo de dados com regra de negócio, config dentro de utilitário, schema e seeds dentro de classe de rotas.

## 5. Inventário de endpoints (contrato)

Grep por framework:

| Framework | Regex |
|---|---|
| Flask | `@\w+\.route\(\s*['"]([^'"]+)['"]`, `add_url_rule\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]\s*,\s*([\w.]+)`, `methods=\[([^\]]+)\]` |
| FastAPI | `@\w+\.(get|post|put|patch|delete)\(\s*['"]([^'"]+)` |
| Express/Koa/Fastify | `(app|router|fastify)\.(get|post|put|patch|delete|all)\(\s*['"]([^'"]+)` e `app.use\(['"]([^'"]+)['"],\s*\w+Router` para prefixos |
| Spring | `@(Get|Post|Put|Delete|Request)Mapping\(` |
| Gin/Echo | `\.(GET|POST|PUT|DELETE)\(` |

Para cada endpoint registre: método, path (com prefixo do blueprint/router), nome do handler, `arquivo:linha`. Flask sem `methods=` é `GET`. Complete com os exemplos de `*.http`: eles revelam **nomes de campos do body** e **status esperados**, que fazem parte do contrato.

Formato de saída:

```
| # | Method | Path | Handler | Location |
|---|--------|------|---------|----------|
| 1 | GET | /produtos | listar_produtos | controllers.py:5 |
```

## 6. Classificação da arquitetura

Aplique na ordem; a primeira que casar vence.

| Classificação | Critérios |
|---|---|
| **Monolito plano** | Handlers acessam o banco diretamente **ou** não há diretórios por camada **ou** ≤ 6 arquivos-fonte concentram tudo **ou** uma única classe/módulo contém roteamento + dados + regra. |
| **Parcialmente em camadas** | Existem diretórios por camada (`models/`, `routes/`, `services/`, `controllers/`, `utils/`), mas pelo menos uma destas vaza: rotas com `db.session`/`cursor.execute`/regra de negócio; validação duplicada entre arquivos; utilitários/constantes existentes não usados pelas rotas; config hardcoded no composition root; ausência de error handler central. |
| **MVC** | Rotas só mapeiam para controllers; controllers não acessam o banco diretamente; models/services sem `request`/`req`; config externa; error handler central. |

Registre a justificativa em uma linha. Essa classificação escolhe a estratégia da Fase 3 (A: criar camadas / B: realocar).

## 7. Inferência de domínio

Combine os substantivos das tabelas, classes de model e paths de rota. Exemplos: `produtos, pedidos, usuarios` → "E-commerce API"; `courses, enrollments, payments` → "LMS com checkout"; `tasks, users, categories` → "Task Manager". Inclua as entidades principais entre parênteses.

## 8. Checklist de saída da Fase 1

- [ ] Linguagem e versão
- [ ] Framework e versão (fonte: manifesto/lockfile)
- [ ] Dependências relevantes (e as fantasmas, se houver)
- [ ] Banco de dados, driver/ORM e tabelas
- [ ] Nº de arquivos e LOC analisados
- [ ] Papel de cada arquivo e misturas detectadas
- [ ] Tabela de endpoints (contrato)
- [ ] Classificação da arquitetura com justificativa
- [ ] Domínio
