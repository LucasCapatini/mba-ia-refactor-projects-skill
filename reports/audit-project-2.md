================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 22.16.0, CommonJS) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-17
Architecture: Monolito plano — uma única classe (`AppManager`) concentra conexão, schema, seeds, roteamento, handlers, regra de negócio e acesso a dados; config e utilitários misturados em `utils.js`.

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 5 | LOW: 5
Total: 17 findings

## Findings

### #1 [CRITICAL] God Class / God Module (AP-03)
File: src/AppManager.js:4-141
Locations: src/AppManager.js:7 — abre a conexão SQLite no construtor; src/AppManager.js:10-23 — schema (5 `CREATE TABLE`) e seeds dentro de `initDb()`; src/AppManager.js:25-138 — `setupRoutes()` registra os 3 endpoints com handlers inline; src/AppManager.js:26 — `const self = this`; src/AppManager.js:37-77 — checkout com 6 níveis de callback aninhado
Description: A classe `AppManager` acumula 7 papéis (infraestrutura de BD, schema, seed, roteamento, controller, service e acesso a dados). O handler de `POST /api/checkout` consulta curso, consulta/cria usuário, decide o pagamento, matricula, registra pagamento e auditoria, tudo em callbacks aninhados dentro de um único método.
Impact: Nenhuma regra (pagamento, matrícula, relatório) pode ser testada sem subir Express e SQLite; qualquer alteração no schema, na rota ou na regra toca o mesmo arquivo e o mesmo método.
Recommendation: Quebrar em camadas — `config/`, `database/` (conexão + schema + seed), `models/` (um por tabela), `services/` (checkout, relatório), `controllers/`, `routes/` — e deixar o composition root apenas montar as peças → PB-03, PB-05, PB-10

### #2 [CRITICAL] Segredos e credenciais hardcoded e expostos em logs (AP-01)
File: src/utils.js:1-7
Locations: src/utils.js:2-5 — `dbUser`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_…"`, `smtpUser` literais no objeto `config`; src/AppManager.js:45 — `console.log` imprime o número completo do cartão e a chave do gateway
Description: Credenciais de banco, chave de gateway com prefixo de produção (`pk_live_`) e usuário SMTP estão escritos no código-fonte e versionados. Não existe nenhuma ocorrência de `process.env` no projeto nem arquivo `.env.example`. No checkout, cartão e chave vão para stdout a cada requisição.
Impact: Vazamento de credenciais de produção por qualquer pessoa com acesso ao repositório ou aos logs; impossibilidade de rotacionar segredos sem novo deploy; dados de cartão (PCI) em texto puro nos logs.
Recommendation: Criar `src/config/index.js` lendo `process.env` com defaults seguros (nunca valores reais), gerar `.env.example`, remover o log de cartão/chave e substituir por logger sem PII → PB-01, PB-16

### #3 [CRITICAL] Armazenamento inseguro de senhas e criptografia caseira (AP-04)
File: src/utils.js:17-23
Locations: src/utils.js:17-23 — `badCrypto()`: concatena 10.000× os 2 primeiros chars do base64 da senha e devolve 10 chars (sem salt, determinístico, reversível por tabela); src/AppManager.js:18 — seed grava senha `'123'` em texto puro; src/AppManager.js:68 — senha padrão `"123456"` quando `pwd` não é enviado; src/AppManager.js:69 — `pass` salvo direto a partir do body com o "hash" acima
Description: A função `badCrypto` não é um hash: para qualquer senha o resultado é sempre a repetição dos 2 primeiros caracteres do base64 (ex.: toda senha iniciada por `"se"` gera o mesmo valor). O seed grava a senha sem nenhum tratamento e o checkout atribui uma senha padrão silenciosa quando o cliente não envia uma.
Impact: Comprometimento de todas as contas em caso de leak do banco; usuários criados sem saber que têm a senha `123456`; colisões triviais entre senhas diferentes.
Recommendation: Substituir por `crypto.scryptSync`/`pbkdf2Sync` com salt aleatório e comparação via `crypto.timingSafeEqual` em `src/services/password.js` (biblioteca padrão, sem dependência nova); aplicar o mesmo hash ao seed; nunca devolver `pass` em respostas → PB-04, PB-14

### #4 [HIGH] Efeitos colaterais no boot, ausência de composition root e de injeção de dependência (AP-07)
File: src/app.js:8-14
Locations: src/app.js:8-10 — `new AppManager()` já abre a conexão; `initDb()` enfileira schema+seed sem callback de conclusão; src/app.js:12 — `app.listen()` no mesmo arquivo que monta a app, sem `require.main === module`; src/AppManager.js:7 — `new sqlite3.Database(':memory:')` dentro da classe que registra rotas; src/AppManager.js:10-23 — `CREATE TABLE` e `INSERT` dentro da mesma classe
Description: Não há separação entre "montar a aplicação" e "subir o servidor": importar `app.js` abre porta, cria banco e popula seeds. A conexão é criada pelo construtor da classe de rotas em vez de ser injetada, e a conclusão de `initDb()` não é aguardada antes do `listen` (funciona só porque `serialize` enfileira no mesmo handle).
Impact: Impossível importar a app em testes sem efeitos colaterais; impossível trocar a implementação do banco; ordem de inicialização frágil.
Recommendation: Application factory `createApp({ db })` em `src/app.js`, `initDb(db)`/`seed(db)` explícitos e assíncronos chamados por um `server.js`/bloco `require.main === module`, conexão criada uma vez no composition root e passada aos models → PB-06, PB-07

### #5 [HIGH] Lógica de negócio em rotas (Fat Controller) (AP-05)
File: src/AppManager.js:28-137
Locations: src/AppManager.js:28-78 — checkout: validação, 2 SELECTs, decisão de pagamento (`cc.startsWith("4")`), 3-4 INSERTs, cache e resposta no mesmo callback; src/AppManager.js:80-129 — relatório: 4 queries encadeadas, soma de receita (`revenue +=`) e montagem do JSON inline; src/AppManager.js:131-137 — delete: SQL direto no handler
Description: Os três handlers `(req, res) =>` leem o request, executam SQL via `this.db` e aplicam regra de domínio no mesmo bloco. A regra de aprovação de pagamento é uma linha enterrada no 3º nível de callback do handler HTTP.
Impact: Regra de negócio (pagamento, matrícula, cálculo de receita) não testável sem HTTP; qualquer segundo endpoint que precise matricular ou pagar duplicará o código.
Recommendation: `routes/` só mapeiam para `controllers/`; controllers extraem e validam o request e chamam `services/checkoutService.js` e `services/reportService.js`; services usam `models/` → PB-05, PB-11

### #6 [HIGH] Estado global mutável e conexão singleton na classe de rotas (AP-06)
File: src/AppManager.js:7
Locations: src/AppManager.js:7 — `this.db = new sqlite3.Database(':memory:')` na classe que registra rotas; src/utils.js:9 — `let globalCache = {}` mutado em runtime e exportado; src/utils.js:10 — `let totalRevenue = 0` contador de módulo exportado; src/utils.js:12-15 — `logAndCache()` grava no cache global como efeito colateral do checkout (src/AppManager.js:59)
Description: O cache é um objeto de módulo compartilhado entre todas as requisições, crescendo sem limite a cada checkout (`last_checkout_<id>`), sem nenhum leitor. O contador `totalRevenue` é exportado por valor (nunca será atualizado por quem importa) e a conexão do banco vive dentro da classe de rotas.
Impact: Vazamento de memória proporcional ao número de checkouts; estado invisível que impede testes paralelos; impossível substituir a conexão.
Recommendation: Remover `globalCache`/`totalRevenue`; se a última compra precisar ser lembrada, persistir em `audit_logs` (já gravado) ou em um serviço explícito; conexão injetada pelo composition root → PB-06

### #7 [HIGH] Configuração hardcoded e sem separação por ambiente (AP-08)
File: src/utils.js:6
Locations: src/utils.js:1-7 — objeto `config` inteiro literal, incluindo `port: 3000`; projeto inteiro — zero ocorrências de `process.env`; raiz — não existe `.env.example`
Description: Porta, credenciais e chave do gateway são fixas no código; não há como rodar em outra porta ou com outra chave sem editar o fonte.
Impact: Impossível ter ambientes dev/test/prod distintos; agrava o AP-01.
Recommendation: `src/config/index.js` com `PORT`, `DB_PATH` (`:memory:` default), `PAYMENT_GATEWAY_KEY`, `SMTP_USER` etc. lidos de `process.env`, documentados em `.env.example` → PB-01

### #8 [MEDIUM] Integridade de dados: sem FK, sem transação, registros órfãos (AP-14)
File: src/AppManager.js:14-16
Locations: src/AppManager.js:14-16 — `enrollments.user_id/course_id` e `payments.enrollment_id` sem `FOREIGN KEY`/`REFERENCES`; src/AppManager.js:50-61 — checkout faz INSERT em `enrollments`, `payments` e `audit_logs` (e às vezes `users`) sem `BEGIN`/`COMMIT`/`ROLLBACK`; src/AppManager.js:133-135 — `DELETE FROM users` sem remover matrículas/pagamentos, com a resposta admitindo "ficaram sujos no banco"
Description: O schema não declara chaves estrangeiras e a aplicação nunca liga `PRAGMA foreign_keys`. O checkout escreve em 3-4 tabelas de forma encadeada: se o INSERT de `payments` falhar, a matrícula já ficou gravada sem pagamento. O DELETE de usuário deixa matrículas e pagamentos órfãos de propósito.
Impact: Matrículas sem pagamento, pagamentos sem matrícula e relatório financeiro inconsistente (o relatório atribui `'Unknown'` a alunos deletados).
Recommendation: `PRAGMA foreign_keys = ON` + `REFERENCES … ON DELETE CASCADE` no schema; checkout dentro de uma transação explícita no service; delete em cascata (ou bloqueio) no `userService` → PB-15

### #9 [MEDIUM] Validação de entrada ausente (AP-11)
File: src/AppManager.js:29-35
Locations: src/AppManager.js:35 — única validação: `if (!u || !e || !cid || !cc)` (presença); src/AppManager.js:32 — `c_id` vai para o SQL sem checar que é inteiro; src/AppManager.js:46 — `cc.startsWith` lança `TypeError` (500 não tratado) se `card` for número ou objeto; src/AppManager.js:30 — `eml` sem formato; src/AppManager.js:31 — `pwd` opcional sem política; src/AppManager.js:132 — `req.params.id` não validado como inteiro
Description: Nenhum campo tem tipo, formato ou faixa validados. Um body com `"card": 4111222233334444` (número em vez de string) passa pela checagem de presença e explode em `startsWith`, derrubando a requisição com exceção não capturada. `usr` não é validado como string.
Impact: 500 (ou crash) em vez de 400; dados inválidos gravados no banco; mensagens de erro pouco úteis ao cliente.
Recommendation: `src/validators/checkoutValidator.js` e `userValidator.js` que verificam tipo/formato e lançam `ValidationError` (400) consumida pelo error handler central → PB-11

### #10 [MEDIUM] Tratamento de erros duplicado, engolido e sem handler central (AP-10)
File: src/AppManager.js:41
Locations: src/AppManager.js:41, 51, 55, 70, 84 — `if (err) return res.status(500).send("…")` copiado 5× com mensagens distintas; src/AppManager.js:57-61 — callback `(err) =>` do INSERT em `audit_logs` ignora `err` e responde 200 mesmo assim; src/AppManager.js:92, 104, 106 — callbacks do relatório ignoram `err` (se `enrollments` vier `undefined`, `enrollments.length` lança `TypeError` e derruba o processo); src/AppManager.js:133-136 — DELETE ignora `err` e responde sucesso sempre; src/app.js:5-14 — nenhum `app.use((err, req, res, next))`
Description: Cada callback trata (ou ignora) o erro de um jeito. Erros de banco no relatório e no delete são engolidos silenciosamente; exceções síncronas dentro dos callbacks do sqlite3 não chegam ao Express e matam o processo.
Impact: Respostas inconsistentes (texto puro em 4xx/5xx, JSON em 200), falhas silenciosas, crash do servidor em erro de banco no relatório.
Recommendation: Exceções de domínio (`NotFoundError`, `ValidationError`, `PaymentDeniedError`) + middleware de erro central em `src/middlewares/errorHandler.js` que mapeia para o status atual e loga o 500 sem expor detalhes → PB-08

### #11 [MEDIUM] Duplicação de código (AP-13)
File: src/AppManager.js:41-84
Locations: src/AppManager.js:41 e 84 — mesma mensagem `"Erro DB"` em dois handlers; src/AppManager.js:50-52 e 69-71 — mesmo idioma `function(err) { … this.lastID }` para capturar o id inserido; src/AppManager.js:96-98 e 119-121 — bloco `report.push(courseData); coursesPending--; if (coursesPending === 0) res.json(report)` copiado 2× dentro do mesmo handler
Description: Os blocos de sincronização manual de callbacks e de captura de `lastID` estão copiados em vez de encapsulados; as mensagens de erro são strings soltas repetidas.
Impact: Correções precisam ser replicadas; divergência silenciosa (o segundo bloco de sincronização já difere do primeiro em condição de borda).
Recommendation: Wrapper único `run/get/all` em Promise no módulo de banco; finalização do relatório num único ponto após `Promise.all`/JOIN; mensagens centralizadas no error handler → PB-13, PB-14

### #12 [MEDIUM] Query N+1 em callbacks aninhados (AP-09)
File: src/AppManager.js:83-128
Locations: src/AppManager.js:83 — `SELECT * FROM courses`; src/AppManager.js:89-92 — `forEach` de cursos com `SELECT * FROM enrollments WHERE course_id = ?` por curso; src/AppManager.js:102-106 — `forEach` de matrículas com `SELECT … FROM users` **e** `SELECT … FROM payments` por matrícula; src/AppManager.js:86, 93, 97, 117, 120 — contadores `coursesPending`/`enrPending` decrementados à mão para saber quando responder
Description: O relatório executa `1 + C + 2·E` queries (C cursos, E matrículas) e sincroniza o resultado com contadores manuais. A ordem dos cursos no JSON depende de qual callback termina primeiro.
Impact: Latência linear com o número de matrículas; resposta não determinística; risco de responder duas vezes ou nunca se um callback falhar.
Recommendation: Uma única query com `LEFT JOIN enrollments/users/payments` (ou duas queries e agregação em memória) em `models/reportModel.js`, mantendo as chaves `course`, `revenue`, `students[].student`, `students[].paid` → PB-09

### #13 [LOW] Imports não usados e símbolos exportados sem consumidor (AP-17)
File: src/AppManager.js:2
Locations: src/AppManager.js:2 — `totalRevenue` importado e nunca usado; src/utils.js:25 — `globalCache` e `totalRevenue` exportados sem nenhum importador externo (o cache só é escrito, nunca lido)
Description: O destructuring do `require('./utils')` traz `totalRevenue` que não aparece em mais nenhuma linha do arquivo; `utils.js` exporta estado interno que ninguém consome.
Impact: Ruído e falsa impressão de que o contador de receita é usado.
Recommendation: Remover junto com a eliminação do estado global (finding #6) → PB-16

### #14 [LOW] APIs e idiomas obsoletos (AP-12)
File: src/AppManager.js:11
Locations: src/AppManager.js:11 — `db.serialize`; src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133 — API de callbacks do `sqlite3`; src/AppManager.js:26 — `const self = this`; src/AppManager.js:50-52 e 69-71 — `function(err) { this.lastID }`
Description: Todo o acesso a dados usa o estilo de callbacks do `sqlite3` com `serialize`, `const self = this` e `function` tradicional para alcançar `this.lastID`. Nenhuma API removida/`DEP` do Node ou do Express 5 foi encontrada (sem `new Buffer`, `res.send(status)`, `body-parser`), por isso a severidade é LOW (idioma legado).
Impact: Callback hell (6 níveis no checkout), erros fora do fluxo do Express, código difícil de ler e testar.
Recommendation: Wrapper em Promises (`run` resolvendo `{ lastID, changes }`, `get`, `all`) em `src/database/connection.js` e `async/await` nos services; manter Express 4 → PB-12

### #15 [LOW] Nomenclatura ruim e abreviações (AP-16)
File: src/AppManager.js:26-33
Locations: src/AppManager.js:26 — `self`; src/AppManager.js:29-33 — `u`, `e`, `p`, `cid`, `cc`; src/AppManager.js:89 — `c`; src/AppManager.js:102 — `enr`, `enrId` (52); src/AppManager.js:4 — `AppManager` (nome genérico para o módulo central); src/utils.js — `utils` abrigando config, cache e cripto; src/app.js:13 — mensagem "Frankenstein LMS"
Description: Variáveis de uma ou duas letras para dados de negócio (usuário, email, senha, curso, cartão) e nomes genéricos para os módulos centrais. Os campos do body (`usr`, `eml`, `pwd`, `c_id`) também são abreviados, mas fazem parte do contrato e devem ser mapeados na borda, não renomeados.
Impact: Legibilidade; `e` colide com a convenção de `catch (e)`.
Recommendation: Renomear internamente (`userName`, `email`, `password`, `courseId`, `cardNumber`) no controller, mantendo os nomes do body; módulos nomeados pela responsabilidade → PB-16

### #16 [LOW] Logging via console.log com dados sensíveis e mensagens de implementação ao cliente (AP-18)
File: src/AppManager.js:45
Locations: src/AppManager.js:45 — `console.log` com número do cartão e chave do gateway; src/utils.js:13 — `console.log` a cada gravação no cache; src/AppManager.js:135 — resposta `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`; src/AppManager.js:41, 84 — `"Erro DB"` ao cliente
Description: Logs de debug em stdout com PII/segredos e mensagens HTTP que descrevem o estado interno do banco.
Impact: Vazamento de dados em logs; cliente recebe detalhes de implementação.
Recommendation: Logger mínimo (`console` encapsulado ou `util.debuglog`) sem PII; mensagens de resposta neutras mantendo o status atual → PB-16

### #17 [LOW] Magic numbers e magic strings (AP-15)
File: src/AppManager.js:46-48
Locations: src/AppManager.js:46 — `cc.startsWith("4")` (prefixo que aprova o pagamento); src/AppManager.js:21, 46, 48, 108 — `'PAID'`/`"DENIED"` literais; src/AppManager.js:68 — senha padrão `"123456"`; src/utils.js:19-22 — `10000`, `2`, `10` em `badCrypto`
Description: Status de pagamento e a regra de aprovação por prefixo de cartão estão como literais espalhados; ninguém lendo `startsWith("4")` sabe que é "bandeira Visa aprovada".
Impact: Alteração da regra exige busca por string; risco de typo entre `'PAID'` e `"PAID"` em pontos diferentes.
Recommendation: `src/constants/payment.js` com `PAYMENT_STATUS = { PAID, DENIED }` e `APPROVED_CARD_PREFIXES`; remover senha padrão → PB-13

## Deprecated APIs
| API | Location(s) | Modern equivalent |
|---|---|---|
| `sqlite3` API de callbacks + `db.serialize` | src/AppManager.js:11, 37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133 | Wrapper em Promises (`util.promisify` ou função própria) + `async/await`; manter o pacote `sqlite3` |
| `const self = this` | src/AppManager.js:26 | Arrow functions / Promise que resolve `{ lastID, changes }` |
| `function(err) { this.lastID }` | src/AppManager.js:50-52, 69-71 | Promise que resolve `{ lastID, changes }` |

## Endpoint Contract (from Phase 1)
| # | Method | Path | Handler | Location |
|---|--------|------|---------|----------|
| 1 | POST | /api/checkout | inline (AppManager.setupRoutes) — body: `usr`, `eml`, `pwd`, `c_id`, `card`; respostas 200 `{msg, enrollment_id}`, 400 texto, 404 texto, 500 texto | src/AppManager.js:28 |
| 2 | GET | /api/admin/financial-report | inline (AppManager.setupRoutes) — 200 `[{course, revenue, students[{student, paid}]}]` | src/AppManager.js:80 |
| 3 | DELETE | /api/users/:id | inline (AppManager.setupRoutes) — 200 texto | src/AppManager.js:131 |

## Refactoring Strategy Preview
Strategy: A — criar camadas
Rationale: Monolito plano com uma God Class e sem nenhum diretório por camada; é preciso criar `config/`, `database/`, `models/`, `services/`, `controllers/`, `routes/`, `middlewares/` e `validators/` do zero, mantendo `npm start` e o contrato dos 3 endpoints.

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
