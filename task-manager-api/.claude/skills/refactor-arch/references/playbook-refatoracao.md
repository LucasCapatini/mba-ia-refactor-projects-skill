# Referência — Playbook de refatoração (Fase 3)

Dezesseis transformações concretas. Leia **apenas** as seções PB-xx mapeadas aos findings do relatório confirmado (o catálogo traz o mapa AP → PB). Cada padrão traz: quando aplicar, antes/depois em Python e em JavaScript, e um checklist de contrato.

Convenções dos exemplos: Python usa Flask + `sqlite3` ou Flask-SQLAlchemy; JavaScript usa Express 4 + `sqlite3` em CommonJS. Nomes de entidade são ilustrativos.

---

## PB-01 — Configuração por ambiente (resolve AP-01, AP-08)

**Quando.** Qualquer segredo, flag de debug, porta, caminho de banco ou URI escrito no código.

**Antes (Python)**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
db_path = "loja.db"
```

**Depois (Python)** — `src/config/settings.py`
```python
import os

def _bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = _bool("DEBUG")
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    ADMIN_SQL_ENABLED = _bool("ADMIN_SQL_ENABLED")
```
```python
# src/app.py
app.config.from_object(Config)
```

**Antes (JS)**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```

**Depois (JS)** — `src/config/index.js`
```js
const toInt = (v, d) => Number.isFinite(Number(v)) ? Number(v) : d;
module.exports = {
  port: toInt(process.env.PORT, 3000),
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  approvedCardPrefix: process.env.APPROVED_CARD_PREFIX || '4',
  logLevel: process.env.LOG_LEVEL || 'info',
};
```
Node ≥ 20.6 carrega `.env` com `node --env-file=.env src/app.js` sem dependência nova.

**`.env.example`** (sempre criar; nunca criar `.env` real):
```
SECRET_KEY=troque-esta-chave
DEBUG=false
PORT=5000
DB_PATH=loja.db
ADMIN_SQL_ENABLED=false
```

**Checklist.** Defaults seguros (`DEBUG=false`, host local); porta default igual à original; `.env` no `.gitignore`; README do projeto atualizado; nenhum segredo literal restante (`grep -n "secret\|senha\|pk_live"`).

---

## PB-02 — SQL parametrizado e rota de SQL arbitrário desativada (resolve AP-02)

**Quando.** Concatenação, f-string ou template literal em SQL; endpoint que executa SQL do body.

**Antes (Python)**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(f"SELECT * FROM usuarios WHERE email = '{email}' AND senha = '{senha}'")
cursor.execute("SELECT * FROM produtos WHERE nome LIKE '%" + termo + "%'")
```

**Depois (Python)**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))   # senha verificada com check_password_hash (PB-04)
cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", (f"%{termo}%",))
```
Filtros dinâmicos: monte a lista de cláusulas com placeholders e a lista de parâmetros em paralelo; nomes de coluna só a partir de uma allowlist fixa.

**Antes (JS)**
```js
this.db.get(`SELECT * FROM courses WHERE id = ${cid}`, (err, row) => { ... });
```

**Depois (JS)**
```js
const course = await db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [courseId]);
```

**Rota de SQL arbitrário** — manter registrada, desativada por padrão:
```python
def executar_query():
    if not current_app.config["ADMIN_SQL_ENABLED"]:
        raise ForbiddenError("Endpoint desabilitado neste ambiente")
    ...
```

**Checklist.** `grep -n 'execute(f\|execute(".*" +\|\${' ` sem resultados em SQL; endpoint perigoso responde 403 na validação; comportamento documentado em `Intentional Behavior Changes`.

---

## PB-03 — Dividir God Class / God Module por domínio (resolve AP-03)

**Quando.** Um arquivo/classe cobre vários domínios ou várias camadas.

**Procedimento.**
1. Liste as funções/métodos e marque entidade (produto, usuário, pedido…) e camada (dados, regra, HTTP).
2. Crie um arquivo por entidade em `models/` e mova as funções de dados, já parametrizadas (PB-02).
3. Regra multi-entidade (criar pedido baixando estoque, relatório com desconto) vai para `services/<caso>_service.py`.
4. Handlers HTTP viram `controllers/<entidade>_controller.py` (PB-05).
5. Só então apague o arquivo original e ajuste imports.

**Antes (Python)** — `models.py` com `get_todos_produtos`, `login_usuario`, `criar_pedido`, `relatorio_vendas`.

**Depois (Python)**
```
src/models/produto_model.py    # get_all, get_by_id, create, update, delete, search
src/models/usuario_model.py    # get_all, get_by_id, get_by_email, create
src/models/pedido_model.py     # create, add_item, list_by_user, list_all (com JOIN)
src/services/pedido_service.py # criar_pedido(usuario_id, itens): valida estoque, calcula total, transação
src/services/relatorio_service.py
```

**Antes (JS)** — `AppManager` com `initDb`, `setupRoutes`, SQL e regra de pagamento.

**Depois (JS)**
```
src/database/schema.js            # createTables(db)
src/database/seed.js              # seed(db)
src/models/user.model.js          # findByEmail, create, remove
src/models/course.model.js
src/models/enrollment.model.js
src/models/payment.model.js
src/services/checkout.service.js  # checkout({ name, email, password, courseId, card })
src/services/report.service.js
src/controllers/*.controller.js
src/routes/*.routes.js
```

**Checklist.** Nenhum arquivo com imports de framework web **e** driver de banco; nenhum módulo com funções de ≥ 3 entidades; todos os endpoints do contrato continuam registrados.

---

## PB-04 — Hash de senha seguro e remoção de campos sensíveis (resolve AP-04)

**Quando.** Senha em texto puro, MD5/SHA1, "cripto" própria, senha/hash em serialização.

**Antes (Python)**
```python
cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
# login:
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
# serialização:
return {"id": row["id"], "email": row["email"], "senha": row["senha"]}
```

**Depois (Python)** — `werkzeug.security` já vem com Flask, sem dependência nova
```python
from werkzeug.security import generate_password_hash, check_password_hash

def create(nome, email, senha, tipo):
    senha_hash = generate_password_hash(senha)
    ...execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", (nome, email, senha_hash, tipo))

def authenticate(email, senha):
    row = get_by_email(email)
    if row is None or not check_password_hash(row["senha"], senha):
        return None
    return to_public_dict(row)

def to_public_dict(row):
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
```
Para SQLAlchemy: `set_password`/`check_password` no model usando as mesmas funções; `to_dict()` nunca inclui a coluna de senha.

**Antes (JS)**
```js
function badCrypto(pwd) { let hash = ""; for (let i = 0; i < 10000; i++) { hash += Buffer.from(pwd).toString('base64').substring(0, 2); } return hash.substring(0, 10); }
```

**Depois (JS)** — `src/utils/password.js`, só `node:crypto`
```js
const { scryptSync, randomBytes, timingSafeEqual } = require('node:crypto');

function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const hash = scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, hash] = stored.split(':');
  const candidate = scryptSync(password, salt, 64);
  return timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
module.exports = { hashPassword, verifyPassword };
```

**Tokens.** Se o original devolvia um token fake previsível, substitua por `secrets.token_urlsafe(32)` / `crypto.randomBytes(32).toString('hex')` mantendo a chave `token` na resposta. Não implemente JWT completo sem pedido explícito.

**Checklist.** Seeds hasheiam; banco local antigo recriado e avisado; `grep -n "senha\|password"` nos serializadores sem resultado; login continua respondendo o mesmo status para sucesso/falha.

---

## PB-05 — Thin Routes → Controllers → Services (resolve AP-05, AP-03)

**Quando.** Handler com validação, regra e SQL no mesmo bloco.

**Antes (Python)**
```python
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or 'title' not in data: return jsonify({'error': 'title obrigatório'}), 400
    if len(data['title']) < 3: return jsonify({'error': 'title curto'}), 400
    ...
    task = Task(title=data['title'], ...)
    db.session.add(task); db.session.commit()
    return jsonify(task.to_dict()), 201
```

**Depois (Python)**
```python
# routes/task_routes.py — só mapeamento
task_bp = Blueprint('tasks', __name__)
task_bp.add_url_rule('/tasks', view_func=task_controller.create, methods=['POST'])
task_bp.add_url_rule('/tasks', view_func=task_controller.list_all, methods=['GET'])

# controllers/task_controller.py — HTTP ↔ domínio
def create():
    payload = task_validator.validate_create(request.get_json(silent=True))
    task = task_service.create_task(payload)
    return jsonify(task.to_dict()), 201

# services/task_service.py — regra de negócio
def create_task(data):
    task = Task(**data)
    db.session.add(task)
    db.session.commit()
    return task
```

**Antes (JS)**
```js
app.post('/api/checkout', (req, res) => { /* 50 linhas com db.get/db.run aninhados */ });
```

**Depois (JS)**
```js
// routes/checkout.routes.js
router.post('/checkout', asyncHandler(checkoutController.checkout));

// controllers/checkout.controller.js
async function checkout(req, res) {
  const input = validateCheckout(req.body);          // mantém usr/eml/pwd/c_id/card na borda
  const result = await checkoutService.checkout(req.app.locals.services, input);
  res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
}

// services/checkout.service.js — sem req/res
async function checkout({ users, courses, enrollments, payments, audit }, input) { ... }
```

**Checklist.** Rotas sem lógica; controllers sem SQL; services sem `request`/`req`; respostas com as mesmas chaves e status de antes.

---

## PB-06 — Conexão gerida por contexto ou injetada (resolve AP-06, AP-07)

**Quando.** Singleton global de conexão, `check_same_thread=False`, estado em memória como armazenamento.

**Antes (Python)**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
        # cria tabelas e seeds aqui
    return db_connection
```

**Depois (Python)** — `src/database.py`
```python
import sqlite3
from flask import g, current_app

def get_connection():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_connection(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        conn = get_connection()
        conn.executescript(SCHEMA_SQL)
        conn.commit()

def init_app(app):
    app.teardown_appcontext(close_connection)
```

**Antes (JS)**
```js
let globalCache = {};
class AppManager { constructor() { this.db = new sqlite3.Database(':memory:'); } }
```

**Depois (JS)** — `src/database/connection.js`
```js
const sqlite3 = require('sqlite3');

function connect(path) {
  return new Promise((resolve, reject) => {
    const raw = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(wrap(raw))));
  });
}
function wrap(raw) {
  return {
    run: (sql, params = []) => new Promise((res, rej) => raw.run(sql, params, function (err) { err ? rej(err) : res({ lastID: this.lastID, changes: this.changes }); })),
    get: (sql, params = []) => new Promise((res, rej) => raw.get(sql, params, (err, row) => (err ? rej(err) : res(row)))),
    all: (sql, params = []) => new Promise((res, rej) => raw.all(sql, params, (err, rows) => (err ? rej(err) : res(rows)))),
    exec: (sql) => new Promise((res, rej) => raw.exec(sql, (err) => (err ? rej(err) : res()))),
    close: () => new Promise((res, rej) => raw.close((err) => (err ? rej(err) : res()))),
  };
}
module.exports = { connect };
```
A instância `db` é criada uma vez em `start()` e passada para `createApp({ db })`, que a injeta nos models/services. Cache em memória vira parâmetro explícito (ou tabela) e nunca um `let` exportado.

**Checklist.** Zero `global`; zero `check_same_thread=False`; zero `let` mutável exportado; uma única conexão para `:memory:`.

---

## PB-07 — Application factory, composition root e entry point com guard (resolve AP-07)

**Quando.** Tabelas/seeds criados no import; `app.listen`/`app.run` sem guard; scripts importando a instância.

**Antes (Python)**
```python
app = Flask(__name__)
...
with app.app_context():
    db.create_all()          # efeito colateral ao importar
if __name__ == '__main__':
    app.run(debug=True)
```

**Depois (Python)**
```python
# app.py (raiz) ou src/app.py
def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app)
    db.init_app(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app

def init_db(app):
    with app.app_context():
        db.create_all()

app = create_app()           # mantido em nível de módulo se scripts fazem `from app import app`

if __name__ == '__main__':
    init_db(app)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
```
Seed:
```python
from app import app, init_db
init_db(app)
with app.app_context():
    seed_data()
```

**Antes (JS)**
```js
const app = express(); const manager = new AppManager(); manager.initDb(); manager.setupRoutes(app); app.listen(3000);
```

**Depois (JS)**
```js
function createApp({ db }) {
  const app = express();
  app.use(express.json());
  app.use('/api', buildRoutes({ db }));
  app.use(errorHandler);
  return app;
}

async function start() {
  const db = await connect(config.dbPath);
  await createTables(db);
  await seed(db);
  createApp({ db }).listen(config.port, () => logger.info(`listening on ${config.port}`));
}

if (require.main === module) start();
module.exports = { createApp, start };
```

**Checklist.** `python -c "import app"` / `node -e "require('./src/app')"` terminam sem abrir porta nem tocar o banco; comandos originais (`python app.py`, `npm start`, `python seed.py`) funcionam.

---

## PB-08 — Error handling centralizado (resolve AP-10)

**Quando.** `try/except` copiado em cada handler; `except:` nu; `str(e)` ao cliente; callbacks ignorando `err`.

**Antes (Python)**
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Depois (Python)**
```python
# domain/exceptions.py
class DomainError(Exception):
    status_code = 400
    def __init__(self, message): super().__init__(message); self.message = message
class ValidationError(DomainError): status_code = 400
class NotFoundError(DomainError): status_code = 404
class UnauthorizedError(DomainError): status_code = 401
class ForbiddenError(DomainError): status_code = 403
class ConflictError(DomainError): status_code = 409

# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
```
Controllers deixam de ter `try/except` e passam a lançar `NotFoundError("Produto não encontrado")`. Mantenha as **chaves** da resposta de erro originais (`erro`, `sucesso`, `error`...).

**Antes (JS)**
```js
this.db.get(sql, [id], (err, row) => { if (err) return res.status(500).send("Erro DB"); ... });
```

**Depois (JS)**
```js
// domain/errors.js
class AppError extends Error { constructor(message, statusCode = 400) { super(message); this.statusCode = statusCode; } }
class NotFoundError extends AppError { constructor(m) { super(m, 404); } }
class ValidationError extends AppError { constructor(m) { super(m, 400); } }
class PaymentDeniedError extends AppError { constructor(m) { super(m, 400); } }

// middlewares/asyncHandler.js
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// middlewares/errorHandler.js
module.exports = function errorHandler(err, req, res, _next) {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  logger.error(err);
  return res.status(500).send('Erro interno');
};
```
Preserve o **formato** original da resposta de erro (texto puro via `send` vs JSON) para não quebrar clientes.

**Checklist.** Zero `except:` nu; zero `str(e)` em resposta; todos os handlers async envoltos em `asyncHandler`; payload inválido devolve 400, nunca 500.

---

## PB-09 — Eliminar N+1 (resolve AP-09)

**Quando.** Query dentro de loop; callbacks aninhados por item; vários COUNTs da mesma tabela.

**Antes (Python, sqlite3)**
```python
for pedido in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
```

**Depois (Python, sqlite3)**
```python
rows = conn.execute("""
    SELECT p.id AS pedido_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    WHERE p.usuario_id = ?
    ORDER BY p.id
""", (usuario_id,)).fetchall()
# agrupar em Python por pedido_id
```

**Antes (Python, SQLAlchemy)**
```python
for t in Task.query.all():
    user = User.query.get(t.user_id)
    cat = Category.query.get(t.category_id)
```

**Depois (Python, SQLAlchemy)**
```python
from sqlalchemy.orm import joinedload
tasks = db.session.execute(
    db.select(Task).options(joinedload(Task.user), joinedload(Task.category))
).scalars().all()

# contagens por status numa query:
rows = db.session.execute(
    db.select(Task.status, db.func.count()).group_by(Task.status)
).all()
```

**Antes (JS)**
```js
courses.forEach(c => { db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrs) => { enrs.forEach(e => { db.get("SELECT ... users", ...); db.get("SELECT ... payments", ...); }); }); });
```

**Depois (JS)**
```js
const rows = await db.all(`
  SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id`);
const report = groupByCourse(rows);   // revenue = soma de amount onde status = 'PAID'
```

**Checklist.** Nenhuma query dentro de `for`/`forEach`; forma da resposta idêntica à original (mesmas chaves, mesma ordem lógica).

---

## PB-10 — Callback hell → async/await com transação (resolve AP-03, AP-12, AP-14)

**Quando.** Callbacks aninhados ≥ 3 níveis; `function(err) { this.lastID }`; sem rollback.

**Antes (JS)**
```js
this.db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
  const enrId = this.lastID;
  self.db.run("INSERT INTO payments ...", [enrId, price, status], function (err) {
    self.db.run("INSERT INTO audit_logs ...", [...], (err) => { res.json({ msg: "Sucesso", enrollment_id: enrId }); });
  });
});
```

**Depois (JS)** — usando o wrapper de PB-06
```js
async function checkout(db, { name, email, password, courseId, card }) {
  const course = await courses.findActiveById(db, courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');

  const status = card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
  if (status === PAYMENT_STATUS.DENIED) throw new PaymentDeniedError('Pagamento recusado');

  await db.exec('BEGIN');
  try {
    const user = (await users.findByEmail(db, email)) || await users.create(db, { name, email, passwordHash: hashPassword(password || DEFAULT_PASSWORD) });
    const { lastID: enrollmentId } = await enrollments.create(db, user.id, courseId);
    await payments.create(db, enrollmentId, course.price, status);
    await audit.log(db, `Checkout curso ${courseId} por ${user.id}`);
    await db.exec('COMMIT');
    return { enrollmentId };
  } catch (err) {
    await db.exec('ROLLBACK');
    throw err;
  }
}
```

**Python equivalente** (sqlite3): `with conn:` abre transação implícita; para controle explícito, `conn.execute("BEGIN")` … `conn.commit()` / `conn.rollback()` em `try/except`.

**Checklist.** Profundidade máxima de 1 nível de callback (só dentro do wrapper); `BEGIN/COMMIT/ROLLBACK` em operações multi-tabela; mesmos status e chaves de resposta.

---

## PB-11 — Validadores centralizados (resolve AP-11, AP-13)

**Quando.** Validação copiada entre criar/atualizar; conversões sem tratamento; regras divergentes.

**Antes (Python)**
```python
# em criar_produto e em atualizar_produto, com regras ligeiramente diferentes
if "nome" not in dados: return jsonify({"erro": "Nome obrigatório"}), 400
if len(dados["nome"]) > 200: return jsonify({"erro": "Nome muito longo"}), 400
preco_min = float(request.args.get("preco_min"))   # ValueError → 500
```

**Depois (Python)** — `validators/produto_validator.py`
```python
from domain.constants import CATEGORIAS_VALIDAS, MAX_NOME
from domain.exceptions import ValidationError

def _require(data, field):
    if data is None or field not in data:
        raise ValidationError(f"{field} é obrigatório")
    return data[field]

def _as_float(value, field):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} deve ser numérico")

def validate_produto(data, partial=False):
    data = data or {}
    out = {}
    for field in ("nome", "descricao", "preco", "estoque", "categoria"):
        if field in data or not partial:
            out[field] = _require(data, field) if not partial else data[field]
    if "nome" in out and not (1 <= len(str(out["nome"])) <= MAX_NOME):
        raise ValidationError(f"nome deve ter até {MAX_NOME} caracteres")
    if "preco" in out:
        out["preco"] = _as_float(out["preco"], "preco")
        if out["preco"] <= 0: raise ValidationError("preco deve ser positivo")
    if "categoria" in out and out["categoria"] not in CATEGORIAS_VALIDAS:
        raise ValidationError("categoria inválida")
    return out

def optional_float(raw, field):
    return None if raw in (None, "") else _as_float(raw, field)
```
`validate_produto(data)` em criar, `validate_produto(data, partial=True)` em atualizar: uma regra, dois usos.

**Antes (JS)**
```js
if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
```

**Depois (JS)** — `validators/checkout.validator.js`
```js
function validateCheckout(body = {}) {
  const { usr, eml, pwd, c_id: courseId, card } = body;   // nomes do contrato preservados
  if (!usr || !eml || courseId === undefined || !card) throw new ValidationError('Bad Request');
  if (!/^\S+@\S+\.\S+$/.test(eml)) throw new ValidationError('Bad Request');
  if (!/^\d{13,19}$/.test(String(card))) throw new ValidationError('Bad Request');
  return { name: String(usr), email: String(eml), password: pwd, courseId: Number(courseId), card: String(card) };
}
```

**Checklist.** Nomes de campos de entrada inalterados; mensagens e status das validações originais preservados onde existiam; entrada inválida nunca gera 500.

---

## PB-12 — Substituir APIs deprecated (resolve AP-12)

**Quando.** Qualquer entrada da tabela de deprecated do catálogo apareceu no relatório.

**Datas (Python)** — centralizar para não misturar naive e aware:
```python
# domain/time.py
from datetime import datetime, timezone
def utc_now() -> datetime:
    """UTC naive, compatível com colunas DateTime existentes e com valores já gravados."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
```
Substitua **todas** as ocorrências de `datetime.utcnow()` por `utc_now()`. Se optar por aware, mude as colunas para `DateTime(timezone=True)` e a serialização para `isoformat()` em um único lugar, e documente a mudança de formato.

**SQLAlchemy**
```python
# antes
task = Task.query.get(task_id)
tasks = Task.query.filter_by(status='done').all()
# depois
task = db.session.get(Task, task_id)
tasks = db.session.execute(db.select(Task).filter_by(status='done')).scalars().all()
```

**Flask**
```python
# antes: @app.before_first_request
# depois: dentro de create_app(): with app.app_context(): ...
```

**Node**
```js
// antes                        // depois
new Buffer(str)                 Buffer.from(str)
require('url').parse(u)         new URL(u)
bodyParser.json()               express.json()
res.send(404)                   res.status(404).send()
res.json(400, obj)              res.status(400).json(obj)
app.del(...)                    app.delete(...)
```
`sqlite3` callbacks → wrapper de PB-06 (sem dependência nova). Registre `node:sqlite`/`better-sqlite3` apenas como recomendação futura.

**Checklist.** `grep -n "utcnow\|\.query\.get(\|before_first_request\|new Buffer\|bodyParser"` sem resultados; nenhuma mudança de major de framework.

---

## PB-13 — Extrair constantes e enums de domínio (resolve AP-15, AP-13)

**Quando.** Listas literais de status/roles/categorias, limites e faixas repetidos.

**Antes (Python)**
```python
if status not in ["pendente", "pago", "enviado", "entregue", "cancelado"]: ...
if total > 10000: desconto = total * 0.1
elif total > 5000: desconto = total * 0.05
```

**Depois (Python)** — `domain/constants.py`
```python
from enum import Enum

class StatusPedido(str, Enum):
    PENDENTE = "pendente"; PAGO = "pago"; ENVIADO = "enviado"; ENTREGUE = "entregue"; CANCELADO = "cancelado"

STATUS_PEDIDO_VALIDOS = {s.value for s in StatusPedido}
CATEGORIAS_VALIDAS = {"informatica", "moveis", "vestuario", "geral"}
MAX_NOME = 200
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (limite_inferior_exclusivo, percentual)
```
```python
def calcular_desconto(total):
    for limite, pct in FAIXAS_DESCONTO:
        if total > limite:
            return total * pct
    return 0.0
```
Se o projeto já tem constantes órfãs em `utils`, **mova-as** para `domain/constants.py` e passe a usá-las, em vez de criar novas.

**Antes (JS)**
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```

**Depois (JS)** — `domain/constants.js`
```js
module.exports = {
  PAYMENT_STATUS: Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' }),
  DEFAULT_PASSWORD: '123456',
};
// prefixo aprovado vem de config.approvedCardPrefix (PB-01)
```

**Checklist.** Nenhuma lista literal de domínio em controllers/services; valores idênticos aos originais (não "corrija" a regra de negócio).

---

## PB-14 — Serialização única por entidade (resolve AP-13, AP-04)

**Quando.** Dicts de resposta montados à mão em vários lugares; método do model existente ignorado.

**Antes (Python)**
```python
# em 3 funções diferentes
result.append({"id": row["id"], "nome": row["nome"], "preco": row["preco"], ...})
# e em outro arquivo, ignorando Task.is_overdue():
overdue = t.due_date and t.due_date < datetime.utcnow() and t.status not in ('done', 'cancelled')
```

**Depois (Python)**
```python
# models/produto_model.py
def to_dict(row):
    return {"id": row["id"], "nome": row["nome"], "descricao": row["descricao"], "preco": row["preco"],
            "estoque": row["estoque"], "categoria": row["categoria"], "ativo": row["ativo"], "criado_em": row["criado_em"]}

# models/task.py
def to_dict(self, include_relations=False):
    data = {... campos ...}
    if include_relations:
        data["overdue"] = self.is_overdue()
        data["user_name"] = self.user.name if self.user else None
        data["category_name"] = self.category.name if self.category else None
    return data
```
Todos os endpoints passam a chamar o mesmo `to_dict`. Campos extras que só alguns endpoints devolviam entram via flag (`include_relations`), preservando o formato de cada endpoint.

**Antes (JS)**
```js
courseData.students.push({ student: user ? user.name : 'Unknown', paid: payment ? payment.amount : 0 });
```

**Depois (JS)** — `models/report.model.js` ou `serializers/`
```js
const toStudentEntry = (row) => ({ student: row.student ?? 'Unknown', paid: row.amount ?? 0 });
```

**Checklist.** Um serializador por entidade; chaves da resposta por endpoint iguais às do baseline; nenhum campo sensível.

---

## PB-15 — Transações e integridade referencial (resolve AP-14)

**Quando.** Múltiplas escritas sem rollback; delete de pai sem tratar filhos; schema sem FK.

**Antes (Python)**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
db.commit()
```

**Depois (Python)**
```python
def criar_pedido(conn, usuario_id, itens):
    try:
        conn.execute("BEGIN")
        total = 0.0
        for item in itens:
            produto = produto_model.get_by_id_for_update(conn, item["produto_id"])
            if produto is None: raise NotFoundError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]: raise BusinessRuleError(f"Estoque insuficiente para {produto['nome']}")
            total += produto["preco"] * item["quantidade"]
        pedido_id = pedido_model.create(conn, usuario_id, total)
        for item in itens:
            pedido_model.add_item(conn, pedido_id, item)
            produto_model.decrement_stock(conn, item["produto_id"], item["quantidade"])   # UPDATE ... WHERE estoque >= ?
        conn.commit()
        return pedido_id
    except Exception:
        conn.rollback()
        raise
```
Schema: `FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE` + `PRAGMA foreign_keys = ON` na conexão. SQLAlchemy: `db.relationship(..., cascade="all, delete-orphan")` ou `ForeignKey(..., ondelete="CASCADE")`.

**Antes (JS)**
```js
this.db.run("DELETE FROM users WHERE id = ?", [id], () => res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."));
```

**Depois (JS)**
```js
async function removeUser(db, userId) {
  await db.exec('BEGIN');
  try {
    await db.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [userId]);
    await db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
    const { changes } = await db.run('DELETE FROM users WHERE id = ?', [userId]);
    await db.exec('COMMIT');
    return changes;
  } catch (err) { await db.exec('ROLLBACK'); throw err; }
}
// controller mantém status 200 e resposta em texto, com mensagem neutra: "Usuário deletado"
```

**Checklist.** Toda escrita multi-tabela em transação; nenhum órfão após delete (verifique com SELECT no smoke); status de resposta inalterado.

---

## PB-16 — Nomenclatura, logging e limpeza (resolve AP-16, AP-17, AP-18)

**Quando.** Nomes abreviados, `print`/`console.log` em handlers, imports/deps sem uso, mensagens internas ao cliente.

**Renomear mantendo contrato (Python)**
```python
# antes
def buscar_produto(id): ...
# depois
def buscar_produto(produto_id): ...     # a rota continua "/produtos/<int:id>"? Não: Flask exige o mesmo nome do parâmetro.
```
Atenção: em Flask o nome do parâmetro da rota (`<int:id>`) deve bater com o da função. Para renomear, mude ambos **no mesmo passo** (`/produtos/<int:produto_id>` + `def buscar_produto(produto_id)`); o path externo não muda.

**Renomear mantendo contrato (JS)**
```js
const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;   // contrato externo intacto
```

**Logging (Python)**
```python
import logging
logger = logging.getLogger(__name__)
# antes: print("Listando " + str(len(produtos)) + " produtos")
logger.debug("Listando %d produtos", len(produtos))
# nunca logar email, senha, cartão ou chaves
```
Configure uma vez em `create_app()`: `logging.basicConfig(level=Config.LOG_LEVEL)`.

**Logging (JS)** — `utils/logger.js` mínimo, sem dependência
```js
const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const current = LEVELS[process.env.LOG_LEVEL || 'info'] ?? 2;
const log = (level) => (...args) => { if (LEVELS[level] <= current) console[level === 'debug' ? 'log' : level](`[${level}]`, ...args); };
module.exports = { error: log('error'), warn: log('warn'), info: log('info'), debug: log('debug') };
```

**Mensagens ao cliente.** `"Usuário deletado, mas as matrículas... ficaram sujos"` → `"Usuário deletado"`; `"!!! BANCO RESETADO !!!"` sai do stdout para `logger.warning`.

**Imports e dependências.** Remova imports sem uso (`grep -n "^import\|^from"` e confira cada símbolo). Dependências do manifesto sem import no código: remova somente se o finding AP-17 as listou e nenhuma transformação passou a usá-las; registre na saída.

**Checklist.** Zero `print`/`console.log` fora de scripts de CLI; nenhum dado sensível em log; paths e nomes de campos externos inalterados; manifesto coerente com os imports.
