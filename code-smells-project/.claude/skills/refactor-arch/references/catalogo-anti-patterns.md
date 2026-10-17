# Referência — Catálogo de anti-patterns (Fase 2)

Percorra **todos** os anti-patterns, na ordem. Para cada um: rode os sinais (Grep) na linguagem detectada, abra o trecho (Read), confirme e descarte os falsos positivos. Um finding só existe se o trecho foi lido.

## Escala de severidade

- **CRITICAL** — falhas de segurança ou de arquitetura que expõem dados sensíveis, permitem ataque ou violam por completo a separação de responsabilidades.
- **HIGH** — fortes violações de MVC/SOLID que travam manutenção e testes.
- **MEDIUM** — padronização, duplicação, validação ausente, performance moderada.
- **LOW** — legibilidade, nomenclatura, magic numbers, APIs obsoletas sem impacto funcional imediato.

Distribuição deste catálogo: 4 CRITICAL, 4 HIGH, 6 MEDIUM, 4 LOW.

---

## AP-01 — Segredos e credenciais hardcoded (ou expostos em respostas) · CRITICAL

**Descrição.** Chaves, senhas, tokens, `SECRET_KEY`, credenciais SMTP/BD/gateway escritos no código ou devolvidos em respostas HTTP/logs.

**Sinais Python.** `SECRET_KEY['"]?\]?\s*=\s*['"]`; `(password|senha|passwd|api_key|apikey|token|secret)\w*\s*=\s*['"][^'"]+['"]`; `smtplib` próximo a uma senha literal; `jsonify\(` contendo `secret`, `senha`, `db_path`, `debug`.
**Sinais Node.** Objeto `config = {` com `pass|secret|key|token` literais; prefixos `pk_live_`, `sk_live_`, `AKIA`; `console.log` imprimindo chave ou número de cartão; `process.env` ausente no projeto.
**Falsos positivos.** Valores vindos de `os.environ.get(..., default)` com default visivelmente fake (`"dev-only"`); arquivos `.env.example`; fixtures de teste.
**Impacto.** Vazamento em repositório, logs e respostas; impossibilita rotação de segredos.
**Recomendação.** Variáveis de ambiente + módulo de config com defaults seguros; remover campos sensíveis de respostas/logs. → **PB-01**, **PB-16**.

## AP-02 — SQL Injection e execução de SQL arbitrário · CRITICAL

**Descrição.** SQL montado por concatenação/format/f-string com dados do cliente, ou endpoint que executa SQL recebido no body.

**Sinais Python.** `execute\(\s*f["']`; `execute\(\s*["'][^"']*["']\s*\+`; `\.format\(` ou `%\s*\(` em string contendo `SELECT|INSERT|UPDATE|DELETE`; `execute\((\w+)\)` onde `\w+` vem de `request`.
**Sinais Node.** Template literal `` `...${ `` dentro de `db\.(run|get|all|exec|query)\(`; `"... " + req.` em SQL; `db.exec(req.body`.
**Falsos positivos.** Concatenação de **nomes de coluna/ordenação** vindos de uma allowlist fixa; placeholders `?`/`%s`/`$1` com `params` separados.
**Impacto.** Leitura/alteração/exclusão total do banco; bypass de login (`' OR '1'='1`).
**Recomendação.** Bind parameters em 100% das queries; rota de SQL arbitrário desativada por padrão (403) e protegida por flag de ambiente. → **PB-02**.

## AP-03 — God Class / God Module · CRITICAL

**Descrição.** Um único arquivo/classe concentra roteamento, acesso a dados, regra de negócio, schema e seeds, ou cobre vários domínios.

**Sinais Python.** Arquivo > ~300 linhas com imports de framework web **e** de driver/ORM; funções de ≥ 3 entidades diferentes no mesmo módulo; prints simulando integrações (email, SMS) dentro de handlers.
**Sinais Node.** Classe com métodos `initDb`/`setupRoutes`/`createTables` juntos; handlers inline com ≥ 4 níveis de callback; `const self = this`; `new sqlite3.Database` dentro da classe que registra rotas.
**Falsos positivos.** Arquivo grande mas de uma só responsabilidade (ex.: só constantes ou só schema).
**Impacto.** Impossível testar em isolamento; qualquer mudança afeta tudo.
**Recomendação.** Separar por camada e por domínio. → **PB-03**, **PB-05**, **PB-10**.

## AP-04 — Armazenamento inseguro de senhas, criptografia caseira e vazamento de credenciais · CRITICAL

**Descrição.** Senha em texto puro, hash fraco (MD5/SHA1 sem salt), "cripto" própria, comparação não constante, ou senha/hash devolvido em serializações.

**Sinais Python.** `hashlib\.(md5|sha1)\(` em contexto de senha; `WHERE .*senha\s*=`; `'password'|"senha"` como chave em `to_dict`/dict de resposta; `== password` em comparação de hash; token montado por concatenação (`'token-' + str(id)`).
**Sinais Node.** `Buffer.from(pwd).toString('base64')`; `createHash\(['"](md5|sha1)`; funções `*Crypto`/`*Hash` próprias com loops; `pass` salvo direto do body.
**Falsos positivos.** `werkzeug.security`, `bcrypt`, `argon2`, `scrypt`, `pbkdf2` com salt; hash usado para checksum de arquivo, não senha.
**Impacto.** Comprometimento de contas; escalada se a senha for reutilizada.
**Recomendação.** Hash com salt via biblioteca padrão; remover campos sensíveis de toda serialização; comparação em tempo constante. → **PB-04**, **PB-14**.

## AP-05 — Lógica de negócio em rotas/controllers (Fat Controller) · HIGH

**Descrição.** Handler HTTP que valida, calcula, consulta o banco e formata a resposta no mesmo bloco.

**Sinais Python.** Dentro de função decorada com `@\w+\.route`: `db\.session\.`, `\.query\.`, `cursor\.execute`, ≥ 5 `return jsonify\(.*\),\s*400`, cálculos de domínio (desconto, estoque, estatísticas), função > 40 linhas.
**Sinais Node.** `app\.(get|post|put|delete)\([^)]*\(req,\s*res\)\s*=>\s*\{` contendo `db\.` e regra (`startsWith`, cálculos), callbacks aninhados.
**Falsos positivos.** Handlers finos que só delegam (`return controller.x()`); validação trivial de presença de campo.
**Impacto.** Regra de negócio não testável sem HTTP; duplicação entre endpoints.
**Recomendação.** Rotas → controllers → services → models. → **PB-05**, **PB-11**.

## AP-06 — Estado global mutável e conexão singleton compartilhada · HIGH

**Descrição.** Variáveis de módulo mutadas em runtime, conexão única global reutilizada entre threads/requisições, caches em memória como fonte de verdade.

**Sinais Python.** `^\s*global\s+\w+`; `check_same_thread=False`; `\w+_connection\s*=\s*None` no nível de módulo; `self\.\w+\s*=\s*\[\]` em service usado como armazenamento.
**Sinais Node.** `^let \w+\s*=\s*\{\}` exportado; contadores de módulo (`let total\w* = 0`); `module.exports = \{.*Cache` ; `this.db = new ...` em classe de rotas.
**Falsos positivos.** Constantes (`const`, `UPPER_CASE` nunca reatribuído); pool de conexões gerido pelo framework/ORM.
**Impacto.** Condições de corrida, vazamento entre requisições, impossibilidade de testes paralelos.
**Recomendação.** Conexão por requisição/contexto ou injetada no composition root; estado persistido ou explícito. → **PB-06**.

## AP-07 — Efeitos colaterais no import, ausência de composition root e de injeção de dependência · HIGH

**Descrição.** Criar tabelas, popular seeds ou abrir conexão ao importar um módulo; controllers importando a conexão diretamente; scripts importando a instância da app.

**Sinais Python.** `db\.create_all\(\)` no nível de módulo ou dentro de `with app.app_context\(\)` fora de função; `CREATE TABLE`/`INSERT` dentro de `get_db()`; `from \w*database\w* import get_db` em módulo de controller; `from app import app` em script.
**Sinais Node.** `new sqlite3.Database` e `CREATE TABLE` dentro da classe que também registra rotas; `app.listen(` no mesmo arquivo que monta a app **sem** `require.main === module`; schema/seed sem `await`/callback antes de `listen`.
**Falsos positivos.** `create_all` dentro de uma função `init_db(app)` chamada explicitamente pelo entry point; migrations.
**Impacto.** Importar para testar já toca o banco; impossível trocar a implementação; ordem de inicialização frágil.
**Recomendação.** Application factory, `init_db()`/`seed()` explícitos, dependências passadas pelo composition root. → **PB-06**, **PB-07**.

## AP-08 — Configuração hardcoded e sem separação por ambiente · HIGH

**Descrição.** Debug ligado em código, host/porta/URI de banco fixos, ausência total de leitura de ambiente.

**Sinais Python.** `DEBUG['"]?\]?\s*=\s*True`; `app\.run\([^)]*debug=True`; `'sqlite:///[^']+'` literal em `app.config`; `host=['"]0\.0\.0\.0`; zero ocorrências de `os\.environ|getenv|load_dotenv`.
**Sinais Node.** `port:\s*\d+` literal; zero ocorrências de `process\.env`; ausência de `.env.example`.
**Falsos positivos.** Defaults razoáveis dentro de `os.environ.get("PORT", 5000)`.
**Impacto.** Debug em produção, impossibilidade de deploy em ambientes distintos, segredos expostos (vide AP-01).
**Recomendação.** Módulo de config lendo ambiente com defaults seguros. → **PB-01**.

## AP-09 — Query N+1 e consultas em loop · MEDIUM

**Descrição.** Uma consulta por item de uma coleção, dentro de laço ou de callbacks aninhados.

**Sinais Python.** `for .*:\n(.*\n){0,6}.*\.(execute|query\.get|filter_by|first)\(`; cursores numerados (`cursor2`, `cursor3`); `len\(\w+\.tasks\)` ou acesso a relationship lazy em loop; vários `\.count\(\)` sequenciais para a mesma tabela.
**Sinais Node.** `forEach\(.*=>\s*\{\n(.*\n){0,5}.*db\.(get|all)\(`; contadores manuais `pending--` para sincronizar callbacks; `Promise.all` com uma query por item quando um JOIN resolveria.
**Falsos positivos.** Loop sobre poucos itens fixos (ex.: 3 tipos conhecidos); batch com `IN (...)`.
**Impacto.** Latência cresce linearmente com os dados; carga desnecessária no banco.
**Recomendação.** JOIN, agregação (`GROUP BY`), eager loading (`joinedload`/`selectinload`), ou consulta única com `IN`. → **PB-09**.

## AP-10 — Tratamento de erros duplicado, engolido ou vazando detalhes · MEDIUM

**Descrição.** Mesmo `try/except` copiado em cada handler, `except:` nu, erro ignorado em callback, `str(e)` enviado ao cliente, ausência de error handler central.

**Sinais Python.** `except\s*:` (nu); `except Exception as e:\n.*return jsonify\(.*str\(e\)` repetido; zero `@app\.errorhandler|@\w+\.app_errorhandler`; `request\.get_json\(\)` seguido de `\.get\(` sem checar `None`.
**Sinais Node.** `\(err\)\s*=>\s*\{` cujo corpo não referencia `err`; `if \(err\) return res\.status\(500\)` repetido; zero `app\.use\(\s*\(err,\s*req,\s*res,\s*next\)`; handlers `async` sem wrapper em Express 4.
**Falsos positivos.** `except SpecificError` com tratamento real; wrapper único de erros.
**Impacto.** Vazamento de stack/SQL para o cliente; erros silenciosos; resposta inconsistente.
**Recomendação.** Exceções de domínio + handler central; 500 genérico com log. → **PB-08**.

## AP-11 — Validação de entrada ausente, duplicada ou inconsistente · MEDIUM

**Descrição.** Campos não validados (tipo, faixa, formato), conversões sem tratamento, mesma validação copiada em criar/atualizar com regras divergentes.

**Sinais Python.** Mesmo bloco de `if ... not in dados` em duas funções; `int\(request\.args|float\(request\.args` fora de `try`; `data\['\w+'\]` em handler de PUT; regex de email duplicada; política de senha diferente entre endpoints.
**Sinais Node.** `if \(!u \|\| !e` como única validação; `req\.body\.\w+` usado em SQL/cálculo sem checar tipo; números de cartão/emails sem formato.
**Falsos positivos.** Validação centralizada em schema (marshmallow/pydantic/zod/joi) aplicada a todos os endpoints.
**Impacto.** 500 em vez de 400; dados inconsistentes; regras divergentes entre criar e atualizar.
**Recomendação.** Validadores reutilizáveis que lançam exceção de validação. → **PB-11**.

## AP-12 — APIs deprecated e idiomas obsoletos · MEDIUM

**Descrição.** Uso de APIs marcadas como deprecated/removidas na linguagem, no framework ou nas bibliotecas, ou de idiomas legados com substituto moderno consolidado.

**Sinais.** Grep por cada entrada da tabela abaixo. Reporte cada ocorrência com o equivalente moderno. Severidade do finding: MEDIUM se a API já foi removida na versão seguinte ou gera warning em runtime; LOW se é apenas idioma legado.
**Falsos positivos.** Uso dentro de shim de compatibilidade documentado.
**Recomendação.** → **PB-12**.

### Tabela de APIs deprecated — Python / Flask / SQLAlchemy

| Deprecated | Desde | Equivalente moderno |
|---|---|---|
| `datetime.utcnow()`, `datetime.utcfromtimestamp()` | Python 3.12 (DeprecationWarning) | `datetime.now(timezone.utc)`; centralizar em `utc_now()` para manter naive/aware consistente |
| Adaptadores padrão de `datetime` no `sqlite3` | Python 3.12 | Registrar adapter/converter explícitos ou persistir ISO 8601 |
| `@app.before_first_request` | Flask 2.3 (removido) | Inicialização em `create_app()` com `app.app_context()` |
| `FLASK_ENV` | Flask 2.3 (removido) | `FLASK_DEBUG` / config por ambiente |
| `app.run(debug=True)` no código | — | Debug via variável de ambiente |
| `flask.json.JSONEncoder` customizado | Flask 2.2 | `app.json_provider_class` / `app.json` |
| `Model.query.get(id)` | SQLAlchemy 2.0 (LegacyAPIWarning) | `db.session.get(Model, id)` |
| `Model.query.filter_by(...).all()` | SQLAlchemy 2.0 (legado) | `db.session.execute(db.select(Model).filter_by(...)).scalars()` |
| `werkzeug.security.safe_str_cmp` | Werkzeug 2.1 (removido) | `hmac.compare_digest` |
| `logging.warn` | Python 3.3 | `logging.warning` |
| `distutils`, `imp`, `pkg_resources` | Python 3.12 | `setuptools`, `importlib`, `importlib.metadata` |
| `collections.Mapping` etc. | Python 3.10 (removido) | `collections.abc.Mapping` |
| Dependência pinada com advisory conhecido (ex.: `flask-cors` < 5) | — | Bump de patch/minor verificado com `pip-audit` (só se houver rede) |

### Tabela de APIs deprecated — Node / Express

| Deprecated | Desde | Equivalente moderno |
|---|---|---|
| `sqlite3` com callbacks e `db.serialize` | idioma legado | Wrapper em Promises (`util.promisify` ou função própria) + `async/await`; alternativas `node:sqlite` (Node ≥ 22.5, experimental) ou `better-sqlite3` |
| `new Buffer()` | DEP0005 | `Buffer.from()`, `Buffer.alloc()` |
| `require('url').parse()` | DEP0169 | `new URL()` |
| `crypto.createCipher`/`createDecipher` | DEP0106 | `createCipheriv`/`createDecipheriv` |
| `fs.exists` | DEP0001 | `fs.promises.access` / `fs.existsSync` |
| `util.isArray`, `util.isString` | DEP0044+ | `Array.isArray`, `typeof` |
| `body-parser` como dependência separada | Express 4.16 | `express.json()`, `express.urlencoded()` |
| `res.send(status)`, `res.json(status, obj)` | Express 4 (removidos no 5) | `res.status(n).send()`, `res.status(n).json(obj)` |
| `res.sendfile`, `app.del`, `req.param()`, `res.redirect('back')` | Express 4 (removidos no 5) | `res.sendFile`, `app.delete`, `req.params/body/query`, redirect explícito |
| `dotenv` como dependência | Node 20.6 | `node --env-file=.env` |
| `var`, `const self = this`, `function(err) { this.lastID }` | idioma legado | `let/const`, arrow functions, Promise que resolve `{ lastID, changes }` |

Express 4 continua em manutenção: registrar as remoções do 5 como recomendação, **sem** migrar de major durante a Fase 3.

## AP-13 — Duplicação de código e serialização manual repetida · MEDIUM

**Descrição.** Mesmo bloco (serialização de entidade, regra de "atrasado", cálculo de percentual, lista de status) copiado em vários lugares, muitas vezes ignorando um método/função que já existe.

**Sinais Python.** Dicts `{"id": row["id"], ...}` repetidos em ≥ 3 funções; mesma condição (`due_date < now and status not in (...)`) em ≥ 2 arquivos enquanto existe `def is_overdue`; funções em `utils` sem nenhum chamador.
**Sinais Node.** Montagem de objetos de resposta repetida; mensagens de erro iguais em vários handlers.
**Falsos positivos.** Duas linhas semelhantes com semântica distinta.
**Impacto.** Correções precisam ser replicadas; divergência silenciosa.
**Recomendação.** Serialização única por entidade; reaproveitar o que existe. → **PB-13**, **PB-14**.

## AP-14 — Integridade de dados: sem transação, sem FK/cascata, registros órfãos · MEDIUM

**Descrição.** Vários INSERT/UPDATE com um único commit sem rollback; DELETE de pai sem tratar filhos; schema sem `FOREIGN KEY`.

**Sinais Python.** Múltiplos `execute(` seguidos de um `commit()` sem `try/except ... rollback()`; `DELETE FROM <pai>` sem `DELETE FROM <filho>` associado ou `ON DELETE`; `CREATE TABLE` com `\w+_id INTEGER` sem `FOREIGN KEY`/`REFERENCES`; `ForeignKey(` sem `ondelete`/cascade e rota que deleta o pai.
**Sinais Node.** `db.run("DELETE FROM users` sem cascata; INSERTs encadeados sem `BEGIN`/`COMMIT`/`ROLLBACK`; mensagem admitindo "ficaram sujos".
**Falsos positivos.** Soft delete intencional; ORM com cascade configurado.
**Impacto.** Escrita parcial em falha; órfãos; estoque/saldo inconsistente.
**Recomendação.** Transação explícita; `PRAGMA foreign_keys=ON` + `ON DELETE CASCADE` ou cascata no service. → **PB-15**.

## AP-15 — Magic numbers e magic strings · LOW

**Descrição.** Literais de domínio soltos (listas de status/roles/categorias, limites, faixas de desconto, prefixos de cartão) em vez de constantes nomeadas.

**Sinais Python.** `in \['pending', 'in_progress'` inline; `len\(\w+\)\s*[<>]=?\s*\d{2,}`; `0\.\d+` em cálculo de preço; `>= 1 and .* <= 5` repetido.
**Sinais Node.** `startsWith\("4"\)`; `'PAID'|'DENIED'` literais em vários pontos; `for \(.*< 10000`.
**Falsos positivos.** `0`, `1`, índices, códigos HTTP padrão.
**Recomendação.** Módulo de constantes/enums do domínio. → **PB-13**.

## AP-16 — Nomenclatura ruim e abreviações · LOW

**Descrição.** Identificadores de uma letra ou abreviados, nomes que sombreiam builtins, nomes genéricos (`Manager`, `utils`, `helpers`) para módulos centrais.

**Sinais Python.** Parâmetro `id`; `cursor2`, `cursor3`; `p1..p5`; `td`, `d`, `u`.
**Sinais Node.** `let u =`, `let e =`, `cid`, `cc`, `usr`, `eml`; `const self = this`.
**Falsos positivos.** `i`, `j` em loops curtos; `e` em `catch (e)`.
**Recomendação.** Renomear internamente mantendo o contrato externo (mapear na borda do controller). → **PB-16**.

## AP-17 — Imports não usados e dependências fantasmas · LOW

**Descrição.** Imports sem uso; pacotes no manifesto sem nenhum import no código; símbolos exportados que ninguém consome.

**Sinais Python.** `^import (os|sys|json|time|math|hashlib)` sem ocorrência posterior no arquivo; pacote em `requirements.txt` sem `import <pacote>` no projeto.
**Sinais Node.** Nome em `module.exports` nunca importado; dependência em `package.json` sem `require('<dep>')`.
**Recomendação.** Remover; alinhar manifesto ao uso real. → **PB-16**.

## AP-18 — Logging via `print`/`console.log` e mensagens de implementação ao cliente · LOW

**Descrição.** Saída de debug em stdout em vez de logger; dados sensíveis (email, cartão, chaves) em logs; mensagens de resposta que revelam detalhes internos ("banco resetado", "ficaram sujos no banco", `"ambiente": "producao"` fixo).

**Sinais Python.** `print\(` dentro de handler/model; `print\(.*(email|senha|cart)`.
**Sinais Node.** `console\.log\(.*(card|key|pass)`; `res\.send\("[^"]*(banco|database|sujo)`.
**Falsos positivos.** `print` em script de seed/CLI; logger estruturado.
**Recomendação.** `logging`/logger mínimo sem PII; mensagens de resposta neutras. → **PB-16**.

---

## Mapa AP → PB

| AP | PB |
|---|---|
| AP-01 | PB-01, PB-16 |
| AP-02 | PB-02 |
| AP-03 | PB-03, PB-05, PB-10 |
| AP-04 | PB-04, PB-14 |
| AP-05 | PB-05, PB-11 |
| AP-06 | PB-06 |
| AP-07 | PB-06, PB-07 |
| AP-08 | PB-01 |
| AP-09 | PB-09 |
| AP-10 | PB-08 |
| AP-11 | PB-11 |
| AP-12 | PB-12 |
| AP-13 | PB-13, PB-14 |
| AP-14 | PB-15 |
| AP-15 | PB-13 |
| AP-16 | PB-16 |
| AP-17 | PB-16 |
| AP-18 | PB-16 |
