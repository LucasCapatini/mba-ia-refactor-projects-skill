# Referência — Guidelines de arquitetura MVC alvo (Fase 3)

Define o que cada camada pode e não pode fazer, a direção das dependências e os layouts-alvo por stack. Leia inteira no início da Fase 3.

## 1. Camadas e responsabilidades

| Camada | Responsabilidade | Pode importar | Nunca |
|---|---|---|---|
| **Config** | Ler variáveis de ambiente, expor valores tipados com defaults seguros | biblioteca padrão | importar framework web, banco ou models |
| **Database / infra** | Abrir/fechar conexão, `init_db()` (schema), `seed()` explícitos, transações | config | conter regra de negócio ou rotas |
| **Models** | Representar entidades e acesso a dados (SQL parametrizado ou ORM), serialização da entidade (`to_dict`/`serialize`) sem campos sensíveis | database, constants | importar `request`/`req`, `jsonify`/`res`; conter regra de negócio multi-entidade |
| **Services** | Regra de negócio e orquestração entre models (checkout, estoque, relatórios, notificações), transações de negócio, lançar exceções de domínio | models, constants, config | conhecer HTTP |
| **Validators** | Validar e normalizar entrada (tipo, faixa, formato), lançar `ValidationError` | constants | acessar banco |
| **Controllers** | Ler request, chamar validator + service/model, montar resposta e status | validators, services, models, serializers | SQL, regra de negócio, `print` |
| **Views / Routes** | Mapear método + path → controller (Blueprint/Router). Nada mais | controllers | lógica |
| **Middlewares** | Error handler central, CORS, JSON, logging de requisição, `asyncHandler` | exceções de domínio, config | regra de negócio |
| **Composition root** | `create_app()`/`createApp()`: instanciar config, banco, registrar middlewares e rotas. Sem efeitos colaterais além de montar a app | tudo | rodar servidor, criar tabelas implicitamente |
| **Entry point** | Chamar o composition root, `init_db()` se aplicável, subir o servidor. Guard `__main__`/`require.main` | composition root, config | definir rotas |

**Direção das dependências:** `entry point → composition root → routes → controllers → (validators, services) → models → database → config`. Nunca ao contrário. Models e services não conhecem HTTP.

**Exceções de domínio** (padrão para o error handler): `ValidationError` → 400, `NotFoundError` → 404, `UnauthorizedError` → 401, `ForbiddenError` → 403, `ConflictError` → 409, `BusinessRuleError` → 422 (ou 400 se o contrato original usava 400). Qualquer outra exceção → 500 genérico com log, sem `str(e)` ao cliente.

## 2. Escolha da estratégia

| Classificação (Fase 1) | Estratégia | O que fazer |
|---|---|---|
| Monolito plano | **A — criar camadas** | Criar o pacote de aplicação (`src/` em Python, `src/<camadas>` em Node), mover cada responsabilidade para sua camada, entry point fino na raiz. |
| Parcialmente em camadas | **B — realocar responsabilidades** | Manter as pastas existentes; adicionar só as que faltam (`config/`, `controllers/`, `middlewares/`, `validators/`, `domain/`); esvaziar as rotas para controllers; consolidar duplicações no que já existe (reaproveitar métodos de model e helpers órfãos antes de criar novos); separar entidades agrupadas no blueprint errado. |
| MVC | Nenhuma estrutural | Aplicar apenas PBs pontuais dos findings. |

Regra de ouro da estratégia B: **não mova o que já está no lugar certo**. Mover `models/` para `src/models/` sem ganho é risco puro.

## 3. Layout-alvo — Python/Flask, estratégia A

```
<projeto>/
├── app.py                    # entry point fino (mantém `python app.py`)
├── .env.example
├── requirements.txt
└── src/
    ├── __init__.py
    ├── app.py                # create_app(): config, CORS, init_db, blueprints, error handlers
    ├── config/
    │   └── settings.py       # class Config lendo os.environ (SECRET_KEY, DEBUG, DB_PATH, PORT, flags)
    ├── database.py           # get_connection() via flask.g + teardown; init_db(); seed()
    ├── domain/
    │   ├── constants.py      # status, categorias, limites, faixas
    │   └── exceptions.py     # ValidationError, NotFoundError, ...
    ├── models/
    │   └── <entidade>_model.py   # SQL parametrizado + serialização
    ├── services/
    │   └── <caso_de_uso>_service.py
    ├── validators/
    │   └── <entidade>_validator.py
    ├── controllers/
    │   └── <entidade>_controller.py
    ├── views/
    │   └── routes.py         # Blueprints por domínio: rota → controller
    └── middlewares/
        └── error_handler.py  # register_error_handlers(app)
```

Entry point:

```python
# app.py (raiz)
from src.app import create_app
from src.config.settings import Config

app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
```

`src/app.py` não colide com `app.py` da raiz porque é importado como `src.app`.

## 4. Layout-alvo — Python/Flask, estratégia B (projeto já com `models/`, `routes/`, `services/`, `utils/`)

```
<projeto>/
├── app.py                    # create_app() + `app = create_app()` em nível de módulo (compat com scripts que fazem `from app import app`)
├── seed.py                   # continua funcionando: usa create_app()/app e init_db()
├── .env.example
├── config/
│   └── settings.py
├── database.py               # db = SQLAlchemy(); init_db(app) chama create_all explicitamente
├── domain/
│   ├── constants.py          # recebe as constantes órfãs de utils
│   └── exceptions.py
├── models/                   # mantidos; to_dict sem campos sensíveis; métodos de domínio (is_overdue) reutilizados
├── validators/
├── services/                 # existentes + novos (task_service, report_service); credenciais saem para config
├── controllers/              # novos: um por entidade
├── routes/                   # mantidos, mas só mapeiam; entidade agrupada no blueprint errado ganha o próprio arquivo com os MESMOS paths
├── middlewares/
│   └── error_handler.py
└── utils/                    # só o que for utilitário puro e usado; o resto migra ou é removido
```

Sobre `db.create_all()`: sai do nível de módulo para `init_db(app)` chamada no entry point (`if __name__ == "__main__"`) e pelo seed. Se algum script externo depende de `from app import app, db`, `app.py` deve continuar exportando ambos.

## 5. Layout-alvo — Node/Express, estratégia A

```
<projeto>/
├── package.json              # "start" inalterado
├── api.http                  # inalterado
├── .env.example
└── src/
    ├── app.js                # createApp({ db }) + start(); `if (require.main === module) start()`
    ├── config/
    │   └── index.js          # process.env com defaults
    ├── database/
    │   ├── connection.js     # abre UMA conexão, expõe run/get/all em Promises
    │   ├── schema.js         # createTables(db)
    │   └── seed.js           # seed(db)
    ├── domain/
    │   ├── constants.js
    │   └── errors.js         # classes de erro com statusCode
    ├── models/
    │   └── <entity>.model.js # funções que recebem db
    ├── services/
    │   └── <useCase>.service.js
    ├── validators/
    ├── controllers/
    │   └── <entity>.controller.js
    ├── routes/
    │   ├── index.js          # monta prefixos (/api)
    │   └── <entity>.routes.js
    ├── middlewares/
    │   ├── errorHandler.js   # (err, req, res, next)
    │   └── asyncHandler.js   # fn => (req, res, next) => fn(req, res, next).catch(next)
    └── utils/
        ├── password.js       # crypto.scrypt + timingSafeEqual
        └── logger.js
```

Entry point:

```js
// src/app.js
async function start() {
  const db = await connect(config.dbPath);
  await createTables(db);
  await seed(db);
  const app = createApp({ db });
  app.listen(config.port, () => logger.info(`listening on ${config.port}`));
}
if (require.main === module) start();
module.exports = { createApp, start };
```

SQLite `:memory:` exige **uma única conexão** criada no `start()` e injetada; cada `new Database(':memory:')` é um banco diferente. Schema e seed devem ser aguardados antes do `listen`.

## 6. Tabela de correspondência de conceitos

| Conceito MVC | Flask | Express |
|---|---|---|
| Model | módulo com SQL parametrizado ou `db.Model` | módulo que recebe `db` e expõe funções de query |
| View/Routes | `Blueprint` | `express.Router()` |
| Controller | função que recebe `request` e devolve `(body, status)` | `async (req, res) => {}` envolto em `asyncHandler` |
| Service | módulo puro | módulo puro |
| Config | `config/settings.py` | `config/index.js` |
| Error handler | `@app.errorhandler(DomainError)` | `app.use((err, req, res, next) => ...)` |
| Composition root | `create_app()` | `createApp({ db })` |
| Entry point | `app.py` raiz com `__main__` | `src/app.js` com `require.main` |

## 7. Contrato de endpoints na refatoração

- Paths, métodos e parâmetros de rota idênticos (inclusive prefixos).
- Nomes dos campos aceitos no body/query **idênticos**, mesmo que ruins (`usr`, `eml`, `c_id`). Renomeie apenas internamente, mapeando na borda do controller.
- Status codes de sucesso e de erro esperado iguais aos originais (se o original devolvia 400 para "pagamento recusado", mantenha 400).
- Chaves de topo da resposta de sucesso iguais. Permitido remover: senha/hash, segredos, caminhos internos. Permitido adicionar: nada, salvo acordo com o usuário.
- Rotas perigosas (SQL arbitrário, reset de banco) continuam registradas, mas respondem 403 a menos que uma flag de ambiente explícita as libere.
- Documente toda exceção na seção `Intentional Behavior Changes` da saída final.

## 8. Scripts auxiliares e documentação do projeto

- Seeds: viram função explícita (`seed()`), chamada pelo script e opcionalmente no boot quando o banco está vazio. Devem usar os mesmos helpers de hash e data da aplicação.
- Arquivos `*.http`: permanecem válidos sem edição. Só altere se a porta passar a ser configurável (acrescente comentário).
- README do projeto: atualize a seção "Como rodar" com as variáveis do `.env.example`. Não documente nada que não exista.
- Manifesto: scripts (`"start"`) mantidos. Remova dependências fantasmas apenas se o finding AP-17 as listou e nada passou a usá-las.
