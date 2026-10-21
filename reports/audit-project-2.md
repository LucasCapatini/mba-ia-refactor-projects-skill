================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 22) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-21
Architecture: Monolito plano

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 4 | LOW: 5
Total: 16 findings

## Findings

### #1 [CRITICAL] God Class / God Module (AP-03)
File: src/AppManager.js:4-141
Locations: src/AppManager.js:7 — conexão `new sqlite3.Database(':memory:')`; src/AppManager.js:10-23 — schema e seed em `initDb`; src/AppManager.js:25-138 — `setupRoutes` com os 3 handlers inline; src/AppManager.js:26 — `const self = this`; src/AppManager.js:37-77 — checkout com 6 níveis de callback
Description: A classe `AppManager` cria a conexão, define o schema, popula seeds e registra todas as rotas com handlers inline que contêm SQL e regra de negócio de três domínios (checkout, relatório financeiro, usuários).
Impact: conexão, schema, seed, roteamento e regras de 3 domínios concentrados numa única classe; impossível testar uma regra (ex.: aprovação de pagamento ou cálculo de receita) sem subir Express e SQLite; callback aninhado em 6 níveis no checkout torna qualquer alteração arriscada
Recommendation: Separar em `config/`, `database/` (conexão, schema, seed), `models/` por entidade, `services/` (checkout, relatório, usuário), `controllers/` e `routes/`; composition root em `app.js` → PB-03, PB-05, PB-10

### #2 [CRITICAL] Armazenamento inseguro de senhas e criptografia caseira (AP-04)
File: src/AppManager.js:66-72
Locations: src/utils.js:17-23 — `badCrypto` (base64 dos 2 primeiros caracteres repetido 10000 vezes e truncado em 10); src/AppManager.js:68 — senha padrão `p || "123456"`; src/AppManager.js:18 — seed grava a senha `'123'` em texto puro
Description: A senha é "hasheada" por `badCrypto`, que é determinística, sem salt e depende só dos ~2 primeiros caracteres (`senhaforte`, `segredo` e `sf` geram todos `c2c2c2c2c2`; `123` e `123456` geram `MTMTMTMTMT`). Quando o cliente não envia `pwd`, o usuário é criado com a senha fixa `123456`, e o seed guarda `123` sem hash.
Impact: qualquer senha com o mesmo prefixo de 2 caracteres produz o mesmo hash, e o valor é reversível para o prefixo; usuários criados pelo checkout sem `pwd` ficam com a senha `123456`, conhecida por qualquer um; o usuário do seed tem a senha `123` em texto puro na coluna `pass`; loop de 10000 iterações por cadastro sem nenhum ganho de segurança
Recommendation: Hash com salt via `node:crypto` (`scrypt` + `timingSafeEqual`) num módulo de utilitário de senha usado pelo service de usuário; senha ausente vira senha aleatória inutilizável; seed com hash → PB-04, PB-14

### #3 [CRITICAL] Segredos e credenciais hardcoded / expostos em logs (AP-01)
File: src/utils.js:1-7
Locations: src/utils.js:3 — `dbPass: "senha_super_secreta_prod_123"`; src/utils.js:4 — `paymentGatewayKey: "pk_live_1234567890abcdef"`; src/utils.js:5 — `smtpUser`; src/AppManager.js:45 — `console.log` com o número completo do cartão e a chave do gateway
Description: A senha de banco, a chave live do gateway de pagamento e o usuário SMTP estão literais no código. A cada checkout, o número do cartão e a chave do gateway são impressos no stdout.
Impact: chave `pk_live_...` e senha de banco versionadas no repositório; cada checkout grava o número completo do cartão e a chave do gateway nos logs; impossível rotacionar segredos sem alterar e redistribuir o código
Recommendation: Módulo `config/` lendo `process.env` com defaults seguros e `.env.example`; remover cartão e chave de qualquer log (no máximo os 4 últimos dígitos) → PB-01, PB-16

### #4 [HIGH] Efeitos colaterais na inicialização, sem composition root nem injeção (AP-07)
File: src/AppManager.js:7-23
Locations: src/app.js:5-14 — `express()`, `initDb()`, `setupRoutes()` e `app.listen` no mesmo arquivo sem guard `require.main === module`; src/AppManager.js:11-22 — schema e seed disparados em `serialize` sem callback/await antes do `listen`
Description: A conexão é criada no construtor da classe que registra rotas, e `initDb()` roda os CREATE/INSERT sem que o boot aguarde a conclusão. O módulo da aplicação abre a porta ao ser importado.
Impact: `require('./src/app')` abre a porta 3000 imediatamente, então não dá para importar o app em teste; o `listen` não espera schema e seed terminarem, e uma requisição na janela de inicialização pode encontrar tabelas inexistentes; não há como passar outro banco para o app (ex.: um banco de teste)
Recommendation: `createApp({ db })` sem efeitos colaterais, `start()` sob guard `require.main`, schema e seed aguardados antes do `listen` → PB-06, PB-07

### #5 [HIGH] Lógica de negócio nos handlers (Fat Controller) (AP-05)
File: src/AppManager.js:28-137
Locations: src/AppManager.js:28-78 — checkout (validação, busca de curso, criação de usuário, regra de aprovação `cc.startsWith("4")`, matrícula, pagamento, auditoria, cache); src/AppManager.js:80-129 — relatório com agregação de receita no handler; src/AppManager.js:131-137 — DELETE com SQL direto
Description: Os handlers HTTP validam, consultam o banco, aplicam a regra de pagamento, orquestram 4 escritas e montam a resposta no mesmo bloco de callbacks.
Impact: regra de aprovação de pagamento e fluxo de matrícula presos dentro do callback HTTP do checkout (~50 linhas); cálculo de receita por curso feito dentro do handler do relatório; nenhuma regra testável sem requisição HTTP
Recommendation: Rotas → controllers (leem `req`, chamam service, respondem) → services (`checkout`, `payment`, `report`, `user`) → models → PB-05, PB-11

### #6 [HIGH] Configuração hardcoded e sem separação por ambiente (AP-08)
File: src/utils.js:6
Locations: src/app.js:12 — `app.listen(config.port)` com porta literal; projeto inteiro — zero ocorrências de `process.env`; raiz — ausência de `.env.example`
Description: A porta é fixa em 3000 dentro do objeto `config`. Nenhum valor é lido do ambiente e não há documentação de configuração.
Impact: porta 3000 fixa em código, sem como alterar no deploy; nenhuma leitura de `process.env` no projeto; não existe `.env.example` documentando as variáveis
Recommendation: `src/config/` lendo `process.env` (PORT, HOST, chave do gateway, prefixo de aprovação) com defaults seguros + `.env.example` → PB-01

### #7 [HIGH] Estado global mutável e conexão presa à classe de rotas (AP-06)
File: src/utils.js:9-15
Locations: src/utils.js:9 — `let globalCache = {}` exportado; src/utils.js:10 — `let totalRevenue = 0` exportado; src/AppManager.js:59 — `logAndCache` a cada checkout; src/AppManager.js:7 — `this.db = new sqlite3.Database` como atributo da classe de rotas
Description: `globalCache` é mutado a cada checkout e nunca é lido. `totalRevenue` é exportado como número primitivo, então quem importa recebe uma cópia que nunca muda. A única conexão vive dentro da classe que registra as rotas.
Impact: `globalCache` ganha uma entrada por usuário que faz checkout e nunca é lido nem limpo (crescimento de memória sem limite); `totalRevenue` é exportado e importado mas fica sempre em 0, sugerindo uma métrica que não existe; a conexão é atributo da classe de rotas e não pode ser compartilhada nem substituída
Recommendation: Remover o cache e o contador sem uso; conexão única criada no módulo de banco e injetada pelo composition root → PB-06

### #8 [MEDIUM] Integridade de dados: sem transação, sem FK, registros órfãos (AP-14)
File: src/AppManager.js:12-16
Locations: src/AppManager.js:12-16 — `enrollments.user_id/course_id` e `payments.enrollment_id` sem `FOREIGN KEY`; src/AppManager.js:50-72 — INSERT de usuário, matrícula, pagamento e auditoria encadeados sem `BEGIN/COMMIT/ROLLBACK`; src/AppManager.js:131-137 — `DELETE FROM users` sem tratar matrículas e pagamentos
Description: O schema não declara chaves estrangeiras, o checkout faz até 4 escritas independentes e o DELETE de usuário remove só a linha pai. A própria resposta admite que "as matrículas e pagamentos ficaram sujos no banco".
Impact: o schema não tem `FOREIGN KEY` em nenhuma tabela; DELETE de usuário deixa matrículas e pagamentos órfãos; falha no INSERT do pagamento deixa usuário e matrícula criados sem pagamento (escrita parcial)
Recommendation: `PRAGMA foreign_keys=ON` + `REFERENCES ... ON DELETE CASCADE` no schema; transação explícita no service de checkout; cascata na remoção de usuário → PB-15

### #9 [MEDIUM] Validação de entrada ausente (AP-11)
File: src/AppManager.js:29-35
Locations: src/AppManager.js:35 — única validação `if (!u || !e || !cid || !cc)`; src/AppManager.js:46 — `cc.startsWith` sem checar tipo; src/AppManager.js:132 — `req.params.id` sem validação
Description: O checkout só verifica presença de campos. Não há checagem de tipo de `card` e `c_id`, formato de email ou tipo de `pwd`, e o `:id` do DELETE vai direto para o SQL.
Impact: `card` enviado como número (ex.: `4111222233334444` sem aspas) gera `TypeError` em `cc.startsWith` dentro do callback do sqlite e derruba o processo; email sem formato válido é aceito e gravado; `c_id` e `:id` não numéricos chegam ao SQL sem resposta 400
Recommendation: Validator de checkout e de id que lança `ValidationError` (400, "Bad Request") antes do service, mapeando `usr/eml/pwd/c_id/card` para nomes internos → PB-11

### #10 [MEDIUM] Tratamento de erros engolido, mascarado e sem handler central (AP-10)
File: src/AppManager.js:37-137
Locations: src/AppManager.js:38 — erro de banco respondido como 404 "Curso não encontrado"; src/AppManager.js:57 — erro do INSERT de auditoria ignorado; src/AppManager.js:92-93 — `err` ignorado e `enrollments.length` sem checagem; src/AppManager.js:104,106 — `err` ignorado; src/AppManager.js:133-135 — erro do DELETE ignorado; src/AppManager.js:41,51,55,70 — `res.status(500)` repetido; projeto — zero `app.use((err, req, res, next))`
Description: Cada callback trata (ou ignora) o erro à sua maneira e não existe error handler central. No relatório, um erro de consulta deixa `enrollments` `undefined`.
Impact: falha de banco na busca de curso responde 404 em vez de 500, mascarando o erro; erro em `SELECT * FROM enrollments` deixa `enrollments` undefined e o `TypeError` derruba o processo; o DELETE responde sucesso mesmo quando o comando falha; não existe error handler central e as respostas 500 são montadas à mão em 4 pontos
Recommendation: Erros de domínio (`ValidationError`, `NotFoundError`, `PaymentDeniedError`) + `asyncHandler` + error handler central com 500 genérico e log → PB-08

### #11 [MEDIUM] Query N+1 no relatório financeiro (AP-09)
File: src/AppManager.js:80-129
Locations: src/AppManager.js:92 — uma consulta de matrículas por curso; src/AppManager.js:104 — uma consulta de usuário por matrícula; src/AppManager.js:106 — uma consulta de pagamento por matrícula; src/AppManager.js:86,93,117-121 — contadores manuais `coursesPending`/`enrPending`
Description: O relatório executa 1 + C + 2·E consultas (C cursos, E matrículas), sincronizadas por contadores decrementados à mão em callbacks.
Impact: o número de consultas cresce linearmente com cursos e matrículas (1 + C + 2·E); sincronização por contadores manuais frágil (um callback que não decrementa trava a resposta); a ordem dos cursos no JSON depende da ordem de chegada dos callbacks, não dos dados
Recommendation: Consulta única com `LEFT JOIN` courses → enrollments → users/payments, agregação no service e ordenação explícita → PB-09

### #12 [LOW] Imports não usados e exports sem consumidor (AP-17)
File: src/AppManager.js:2
Locations: src/AppManager.js:2 — `totalRevenue` importado e nunca usado; src/utils.js:25 — `globalCache` exportado sem consumidor; src/utils.js:2-3,5 — `config.dbUser`, `config.dbPass`, `config.smtpUser` nunca lidos
Description: Símbolos importados ou exportados sem nenhum uso real, além de chaves de config que nada consome.
Impact: `totalRevenue` importado em `AppManager.js` sem uso; `globalCache` exportado sem nenhum consumidor; `dbUser`, `dbPass` e `smtpUser` existem no config sem nenhum leitor
Recommendation: Remover imports, exports e chaves de config sem uso → PB-16

### #13 [LOW] Idiomas obsoletos do driver sqlite3 (AP-12)
File: src/AppManager.js:11-22
Locations: src/AppManager.js:11 — `db.serialize`; src/AppManager.js:37-136 — API de callbacks aninhados; src/AppManager.js:26 — `const self = this`; src/AppManager.js:50-54,69-71 — `function(err) { this.lastID }`
Description: Todo o acesso a dados usa a API de callbacks do `sqlite3` com `serialize`, e o código depende do `this` do driver para obter `lastID`.
Impact: callbacks aninhados impedem `async/await` e tratamento uniforme de erros; `const self = this` e `function(err) { this.lastID }` acoplam o código ao `this` dinâmico do driver
Recommendation: Wrapper em Promises (`run/get/all/exec`) que resolve `{ lastID, changes }` + `async/await` → PB-12

### #14 [LOW] Nomenclatura ruim e abreviações (AP-16)
File: src/AppManager.js:26-33
Locations: src/AppManager.js:29-33 — `u`, `e`, `p`, `cid`, `cc`; src/AppManager.js:26 — `self`; src/AppManager.js:4 — classe `AppManager`; src/utils.js — módulo genérico `utils` com config, cache, log e hash; src/utils.js:17 — `badCrypto`
Description: Variáveis de uma letra ou abreviadas no checkout e nomes genéricos para os módulos centrais.
Impact: as abreviações `u/e/p/cid/cc` obrigam a reler o body para entender o checkout; `AppManager` e `utils` não indicam a responsabilidade de cada módulo
Recommendation: Nomes descritivos internos (`name`, `email`, `password`, `courseId`, `cardNumber`), mapeados na borda (validator) sem mudar os campos do contrato → PB-16

### #15 [LOW] Logging via console.log e mensagem de implementação ao cliente (AP-18)
File: src/AppManager.js:45
Locations: src/AppManager.js:45 — `console.log` com cartão e chave; src/utils.js:13 — `console.log` em `logAndCache`; src/AppManager.js:135 — resposta "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."
Description: Saída de debug com `console.log` sem nível, incluindo dados de pagamento, e uma resposta HTTP que descreve o estado interno do banco.
Impact: logs sem nível nem formato, misturando debug e informação de pagamento; a resposta do DELETE expõe ao cliente um detalhe interno de integridade do banco
Recommendation: Logger mínimo (`utils/logger`) com níveis e sem PII; mensagem neutra no DELETE ("Usuário deletado") → PB-16

### #16 [LOW] Magic numbers e magic strings (AP-15)
File: src/AppManager.js:46
Locations: src/AppManager.js:46 — prefixo de aprovação `"4"`; src/AppManager.js:21,46,48,108 — `'PAID'`/`'DENIED'` literais; src/AppManager.js:37 — `active = 1`; src/utils.js:19 — `10000`
Description: A regra de aprovação, os status de pagamento e o flag de curso ativo são literais espalhados pelo código.
Impact: prefixo de aprovação de cartão `"4"` fixo e não configurável; status `PAID`/`DENIED` repetidos em 4 pontos, e um erro de digitação passa sem aviso; flag `active = 1` sem nome
Recommendation: `domain/constants.js` com `PAYMENT_STATUS` e `COURSE_ACTIVE`; prefixo de aprovação via config (`APPROVED_CARD_PREFIX`) → PB-13

## Deprecated APIs
| API | Location(s) | Modern equivalent |
|---|---|---|
| `sqlite3` com callbacks e `db.serialize` (idioma legado) | src/AppManager.js:11-22, 37-136 | Wrapper em Promises + `async/await` (alternativas: `node:sqlite` no Node ≥ 22.5, experimental; `better-sqlite3`) |
| `const self = this` (idioma legado) | src/AppManager.js:26 | Arrow functions / injeção explícita da dependência |
| `function(err) { this.lastID }` (idioma legado) | src/AppManager.js:50-52, 54, 69-71 | Promise que resolve `{ lastID, changes }` |
| Express 4 → 5 | nenhuma API removida no Express 5 em uso (`res.status().send/json` já é o idioma atual) | Sem ação; migração de major fora do escopo |

## Endpoint Contract (from Phase 1)
| # | Method | Path | Handler | Location |
|---|--------|------|---------|----------|
| 1 | POST | /api/checkout | arrow `(req, res)` inline (checkout) | src/AppManager.js:28 |
| 2 | GET | /api/admin/financial-report | arrow `(req, res)` inline (relatório financeiro) | src/AppManager.js:80 |
| 3 | DELETE | /api/users/:id | arrow `(req, res)` inline (remoção de usuário) | src/AppManager.js:131 |

Contrato observado no código: checkout recebe `usr`, `eml`, `pwd`, `c_id`, `card` e responde 200 `{ msg, enrollment_id }`, 400 texto "Bad Request", 404 texto "Curso não encontrado", 400 texto "Pagamento recusado" ou 500 texto. O relatório responde 200 com array `[{ course, revenue, students: [{ student, paid }] }]`. O DELETE responde 200 com texto.

## Refactoring Strategy Preview
Strategy: A — criar camadas
Rationale: Monolito plano (3 arquivos, sem pastas por camada, handlers com SQL direto), então a estrutura MVC é criada em `src/`.

================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
