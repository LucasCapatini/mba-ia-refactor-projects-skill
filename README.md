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
| 2 | CRITICAL | Endpoint que executa SQL arbitrário recebido no body | `app.py:59-78` | `/admin/query` sem autenticação permite ler, alterar ou apagar o banco inteiro. |
| 3 | CRITICAL | `SECRET_KEY` e `DEBUG=True` hardcoded; `health_check` devolve a secret key, o caminho do banco e `debug: True` | `app.py:7-8`, `controllers.py:285-289` | Segredo versionado no repositório e exposto publicamente por um endpoint. |
| 4 | CRITICAL | Senhas gravadas, comparadas e retornadas em texto puro | `models.py:83, 99, 110, 126-129` | `GET /usuarios` lista todas as senhas; comprometimento total das contas. |
| 5 | HIGH | `models.py` é um God Module: produtos, usuários, pedidos e relatórios num só arquivo, com regra de negócio (estoque, total, desconto) na camada de dados | `models.py:1-314`, `133-169`, `256-262` | Impossível testar a regra de pedido sem banco; qualquer alteração afeta quatro domínios. |
| 6 | HIGH | Conexão singleton global com `check_same_thread=False`, criando tabelas e seeds dentro de `get_db()` | `database.py:4-10` (singleton), `14-84` (schema e seeds) | Estado global compartilhado entre threads e efeito colateral no primeiro acesso. |
| 7 | HIGH | `try/except Exception` copiado em todos os controllers, sem error handler central, devolvendo `str(e)` ao cliente | `controllers.py:5-292` | Vaza detalhes internos e replica o mesmo boilerplate em 16 funções. |
| 8 | MEDIUM | Query N+1 em dois níveis ao listar pedidos (itens e depois produto de cada item) | `models.py:187-199, 219-231` | Latência cresce linearmente com o número de pedidos. |
| 9 | MEDIUM | Validação de produto duplicada e divergente entre criar e atualizar; `float()` de query string sem tratamento | `controllers.py:28-54 vs 72-90`, `118-121` | Regras inconsistentes e entrada inválida gerando 500 em vez de 400. |
| 10 | LOW | Magic numbers nas faixas de desconto (`10000`/`5000`/`1000` e `0.1`/`0.05`/`0.02`) | `models.py:257-262` | Regra comercial sem nome; mudar uma faixa exige caçar literais. |
| 11 | LOW | `print` usado como logging, inclusive com o email do usuário | `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`; `app.py:56, 83-86` | Sem nível nem destino configurável; dado pessoal no stdout. |
| 12 | LOW | Variável e parâmetro `id` sombreando o builtin | `controllers.py:56, 160` (parâmetros em `controllers.py:14, 64, 98, 136` e `models.py:24, 54, 65, 89`) | Esconde `id()` no escopo e confunde a leitura. |
| 13 | LOW | Imports sem uso | `models.py:2` (`sqlite3`), `database.py:2` (`os`) | Ruído e dependência aparente que não existe. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

Três arquivos em `src/`: `app.js` (entry point), `AppManager.js` (tudo o resto) e `utils.js` (config, cache e "cripto").

| # | Severidade | Problema | Localização | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais de banco, chave de gateway de pagamento e usuário SMTP hardcoded num objeto `config` | `src/utils.js:1-7` | Segredos de produção versionados; a chave `pk_live_` ainda é impressa no console. |
| 2 | CRITICAL | `badCrypto`: pseudo-hash que só depende dos 2 primeiros caracteres da senha (base64 do prefixo repetido e cortado em 10), sem salt; checkout sem `pwd` grava a senha padrão `"123456"` | `src/utils.js:17-23`, uso e senha padrão em `AppManager.js:68` | Qualquer senha com o mesmo prefixo colide (`123`, `123456` e `19abc` geram `MTMTMTMTMT`); o loop de 10.000 iterações não acrescenta segurança; contas criadas sem senha entram com `123456`. |
| 3 | CRITICAL | Número do cartão logado em `console.log` junto com a chave do gateway | `src/AppManager.js:45` | Dados de pagamento em log de aplicação. |
| 4 | CRITICAL | `AppManager` é uma God Class: cria o banco, define schema, insere seeds, registra rotas e contém a regra de pagamento | `src/AppManager.js:1-141` | Nenhuma responsabilidade isolável; impossível testar o checkout sem subir tudo. |
| 5 | HIGH | Checkout em callback hell de seis níveis, sem transação: se o INSERT de pagamento falha, a matrícula já foi gravada | `src/AppManager.js:28-78` | Escrita parcial e fluxo ilegível. |
| 6 | HIGH | Estado global mutável exportado (`globalCache` só cresce e nunca é lido; `totalRevenue` é um primitivo exportado por cópia e nunca alterado) e nenhum tratamento de erro central, com erros de banco ignorados | `src/utils.js:9-15, 25`; erros ignorados em `src/AppManager.js:57, 92, 104, 106, 133` | Crescimento de memória sem limite a cada checkout; falhas de banco silenciosas ou que derrubam o processo. |
| 7 | HIGH | `DELETE /api/users/:id` apaga o usuário e deixa matrículas e pagamentos órfãos, e a própria resposta admite isso | `src/AppManager.js:131-137` | Integridade referencial quebrada por design. |
| 8 | MEDIUM | Relatório financeiro com N+1 em callbacks aninhados e contadores manuais (`coursesPending--`, `enrPending--`) para sincronizar | `src/AppManager.js:80-129` | 1 query de cursos + 1 por curso (matrículas) + 2 por matrícula (usuário e pagamento). |
| 9 | MEDIUM | Validação de entrada limitada a presença dos campos; cartão e email sem formato; API de callbacks do `sqlite3` (idioma obsoleto, sem Promises) | `src/AppManager.js:35`, todo o arquivo | Entradas inválidas chegam ao SQL e ao "gateway". |
| 10 | LOW | Nomes de uma ou duas letras para os dados do checkout | `src/AppManager.js:29-33` (`u`, `e`, `p`, `cid`, `cc`); também `c` em 89 e `enr` em 102 | O leitor precisa mapear cada abreviação para o significado real. |
| 11 | LOW | `const self = this` misturado com `this` em arrow functions e `function` | `src/AppManager.js:26` (uso em 54, 57) | Dois idiomas de contexto no mesmo fluxo; fácil errar o `this`. |
| 12 | LOW | `.verbose()` do `sqlite3` ligado incondicionalmente | `src/AppManager.js:1` | Stack traces longas e overhead fora de desenvolvimento. |
| 13 | LOW | Mensagem de implementação interna devolvida ao cliente | `src/AppManager.js:135` | A resposta HTTP expõe o estado interno do banco ("ficaram sujos"). |
| 14 | LOW | Import e export mortos (`totalRevenue`) | `src/AppManager.js:2`, `src/utils.js:10, 25` | Sugere um acumulador de receita que não existe. |

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy, Task Manager)

Já possui `models/`, `routes/`, `services/` e `utils/`, mas as responsabilidades vazam entre as camadas.

| # | Severidade | Problema | Localização | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | `User.to_dict()` inclui o hash da senha, devolvido em quatro endpoints (detalhar, criar, atualizar, login) | `models/user.py:21`, `routes/user_routes.py:33, 85, 129, 209` | Hashes expostos publicamente, e são MD5 (item 2). |
| 2 | CRITICAL | Hash de senha com MD5 sem salt e comparação não constante | `models/user.py:29, 32` | Quebrável por rainbow table em segundos. |
| 3 | CRITICAL | Token de login previsível (`'fake-jwt-token-' + id`) e escalada de privilégio: qualquer um cria ou se promove a `admin` | `routes/user_routes.py:210, 52, 71-72, 119-122` | Autenticação e autorização inexistentes na prática. |
| 4 | CRITICAL | Credenciais SMTP e `SECRET_KEY` hardcoded | `services/notification_service.py:9-10`, `app.py:13` | Segredos versionados. |
| 5 | HIGH | Lógica de negócio e validação dentro das rotas (`create_task` e `update_task` com ~70 linhas cada); rotas acessam `db.session` diretamente | `routes/task_routes.py:85-154, 156-223` | As "routes" fazem papel de controller, service e validator ao mesmo tempo. |
| 6 | HIGH | Regra de "task atrasada" duplicada em seis lugares enquanto `Task.is_overdue()` existe e nunca é chamado; CRUD de categorias dentro do blueprint de relatórios | `task_routes.py:30-39, 71-80, 283-287`, `user_routes.py:171-180`, `report_routes.py:33-43, 132-135, 157-223` | Divergência silenciosa de regra; baixa coesão dos blueprints. |
| 7 | HIGH | `db.create_all()` executado no import de `app.py`; `seed.py` importa a instância da app | `app.py:30-31`, `seed.py:2` | Efeito colateral ao importar; sem application factory. |
| 8 | MEDIUM | Queries N+1 (`User.query.get`/`Category.query.get` por task; uma query por usuário e um COUNT por categoria nos relatórios); 14 COUNTs separados no resumo | `task_routes.py:42, 51`, `report_routes.py:15-28, 46, 48-51, 55-56, 163`, `user_routes.py:22` | Performance degrada com o volume. |
| 9 | MEDIUM | `except:` nu em 9 pontos das rotas (e mais 3 em `helpers.py`), sem tratamento de erro padronizado; `utils/helpers.py` tem validadores e constantes que ninguém usa (`process_task_data`, `VALID_STATUSES`, `validate_email`) enquanto as rotas reimplementam tudo | `task_routes.py:62, 137, 204, 236`, `user_routes.py:130, 149`, `report_routes.py:186, 207, 221`, `utils/helpers.py:46, 49, 88`; código morto em `utils/helpers.py:19-23, 57-116` | Erros engolidos; código morto convivendo com duplicação. |
| 10 | LOW | `datetime.utcnow()` deprecated (Python 3.12+) | `models/task.py:15, 16, 52`; `models/user.py:14`; `models/category.py:11`; `routes/task_routes.py:31, 72, 215, 285`; `routes/user_routes.py:172`; `routes/report_routes.py:35, 42, 45, 71, 133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66, 67, 69, 70, 74` | Warning hoje, remoção futura; datas naive. |
| 11 | LOW | `Model.query.get()` legado no SQLAlchemy 2.x | `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/user_routes.py:29, 94, 136, 155`; `routes/report_routes.py:105, 192, 213` | API legada; o substituto é `db.session.get()`. |
| 12 | LOW | Imports sem uso | `app.py:7` (`os, sys, json`); `routes/task_routes.py:7` (`json, os, sys, time`); `routes/user_routes.py:6` (`hashlib, json`); `routes/report_routes.py:7-8` (`format_date, calculate_percentage, json`); `models/task.py:3` (`json`); `utils/helpers.py:3-7` (`os, json, sys, math, hashlib`) | Ruído e falsa impressão de acoplamento. |
| 13 | LOW | Magic numbers (limites de título, prioridade 1-5, tamanho de senha, janela de 7 dias, cor `'#000000'`) | `routes/task_routes.py:96, 99, 104, 113, 167, 169, 182`; `models/task.py:46`; `routes/user_routes.py:64, 115`; `routes/report_routes.py:45, 129, 180`; `models/category.py:10` | As constantes já existem em `helpers.py:110-116` e são ignoradas; os valores podem divergir. |
| 14 | LOW | Dependências pinadas e nunca importadas (`marshmallow`, `requests`, `python-dotenv`) | `requirements.txt:4-6` | Instalação e superfície de ataque sem uso. |

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

**Resolvido = Impact conferido.** Aplicar o PB não basta para dar um finding como resolvido. Na Fase 3, o plano diz como cada item do `Impact` vai deixar de acontecer, e a validação confere cada item com uma evidência observada no código novo ou na execução (tabela `Impact Verification`). Um item `✗` mantém o finding em `Findings Remaining`. A regra entrou depois da avaliação: o finding de senha do projeto 2 tinha sido dado como resolvido com hash correto aplicado sobre uma senha padrão fixa.

### Catálogo de anti-patterns (18) e por quê

| Severidade | Anti-patterns | Motivação |
|---|---|---|
| CRITICAL | AP-01 segredos hardcoded/expostos; AP-02 SQL injection e SQL arbitrário; AP-03 God Class/Module; AP-04 senhas inseguras e vazamento de credenciais | São os quatro problemas que aparecem nos três projetos e que, sozinhos, comprometem a aplicação. |
| HIGH | AP-05 Fat Controller; AP-06 estado global mutável e singleton; AP-07 efeitos colaterais no import e ausência de composition root/DI; AP-08 config hardcoded | Violações estruturais de MVC/SOLID que a Fase 3 precisa resolver para a nova estrutura fazer sentido. |
| MEDIUM | AP-09 N+1; AP-10 erros duplicados/engolidos/vazados; AP-11 validação ausente ou duplicada; AP-12 APIs deprecated; AP-13 duplicação e serialização manual; AP-14 integridade (sem transação/FK/cascata) | Padronização, performance e robustez. AP-12 é o requisito de detecção de APIs deprecated, com tabelas separadas para Python/Flask/SQLAlchemy e Node/Express, cada entrada com o equivalente moderno. |
| LOW | AP-15 magic numbers; AP-16 nomenclatura; AP-17 imports/deps sem uso; AP-18 `print`/`console.log` e mensagens internas ao cliente | Legibilidade e higiene, baratos de corrigir junto com o resto. |

Cada entrada traz sinais de detecção em regex para Python e para JavaScript, lista de falsos positivos (para o agente não reportar `except SpecificError` como bare except, por exemplo), impacto, recomendação e os PBs associados.

### Playbook (16 transformações)

PB-01 config por ambiente · PB-02 SQL parametrizado e rota de SQL arbitrário atrás de flag · PB-03 dividir God Class por domínio · PB-04 hash seguro, senha ausente aleatória e inutilizável e remoção de campos sensíveis · PB-05 Thin Routes → Controllers → Services · PB-06 conexão por contexto/injetada · PB-07 application factory e entry point com guard · PB-08 error handling centralizado · PB-09 eliminar N+1 · PB-10 callback hell → async/await com transação · PB-11 validadores centralizados · PB-12 substituir APIs deprecated · PB-13 constantes e enums · PB-14 serialização única por entidade · PB-15 transações e integridade · PB-16 nomenclatura, logging e limpeza.

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

A skill foi executada nos três projetos. Os relatórios da Fase 2 estão em `reports/audit-project-{1,2,3}.md` e as evidências de validação em `docs/validacao/`.

### Resumo dos relatórios de auditoria

| Projeto | Stack detectada | Arquitetura | CRITICAL | HIGH | MEDIUM | LOW | Total | Deprecated detectado |
|---|---|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python 3.13 + Flask 3.1.1 + sqlite3 | Monolito plano → Estratégia A | 4 | 4 | 5 | 4 | 17 | só `app.run(debug=True)` (nenhuma API removida; verificado e declarado) |
| 2 — ecommerce-api-legacy | Node 22 + Express 4.22.1 + sqlite3 | Monolito plano → Estratégia A | 3 | 4 | 4 | 5 | 16 | API de callbacks do `sqlite3`, `const self = this`, `function(err){this.lastID}` |
| 3 — task-manager-api | Python 3.13 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 | Parcialmente em camadas → Estratégia B | 3 | 4 | 6 | 4 | 17 | `datetime.utcnow` (40×), `Model.query.get` (14×), `app.run(debug=True)`, Flask-CORS 4.0.0 (CVE-2024-1681) |

Todos os findings (17, 16 e 17) citam arquivo e linhas exatos, estão ordenados de CRITICAL para LOW e apontam o `AP-xx` do catálogo e o `PB-xx` do playbook. Uma amostra de 29 referências arquivo:linha da primeira execução e de mais 10 do relatório refeito do projeto 2 foi conferida manualmente contra o código original: todas corretas.

Os problemas da Análise Manual aparecem nos relatórios, com uma exceção: o `.verbose()` do `sqlite3` no projeto 2 (item LOW #12), que a skill não reportou. Na primeira execução, a saída das sessões também mostrou a skill descartando dois falsos positivos com justificativa: no projeto 2, o sinal de SQL injection, porque todas as queries usavam placeholders; no projeto 3, o `like(f'%{query}%')`, que monta apenas o valor do bind parameter. Esses descartes não ficam registrados nos relatórios, porque o template só lista findings confirmados.

**Correção pós-execução.** O finding #13 do projeto 3 afirmava que apagar uma categoria deixava tasks órfãs. Na Fase 3 a própria skill verificou que o SQLAlchemy já anulava a FK implicitamente via `backref`, e apontou a imprecisão. O texto do finding foi corrigido no relatório salvo, com nota explicando a correção; o problema real, ausência de política explícita de integridade, permanece válido.

**Segunda execução no projeto 2 (após a avaliação).** O avaliador notou que o relatório listava no Impact do finding de senhas "usuários criados sem saber que têm a senha `123456`", mas o `checkout.service.js` gerado na primeira execução continuava usando `DEFAULT_PASSWORD = '123456'` quando o `pwd` não vinha, agora só hasheado. A conta continuava acessível com `123456`. Havia duas causas na skill. Primeira: o próprio playbook trazia essa constante como exemplo no PB-10 e no PB-13, e o checklist do PB-13 ("valores idênticos aos originais") incentivava manter o literal. Segunda: a Fase 3 dava o finding como resolvido porque o PB tinha sido aplicado, sem conferir as consequências descritas no Impact. Ajustes:

- **PB-04:** ganhou a seção "Senha padrão fixa". Senha ausente vira uma senha aleatória inutilizável (`randomBytes(32)` / `secrets.token_urlsafe(32)`), hasheada e descartada. O `pwd` segue opcional e o contrato não muda.
- **PB-10 e PB-13:** os exemplos perderam o `DEFAULT_PASSWORD`. O PB-13 agora diz que credenciais não são constantes de domínio.
- **Catálogo:** o AP-04 ganhou sinais de detecção para fallback de senha literal, e o AP-15 deixou de tratar senha como magic string.
- **Fase 3:** passa a conferir o Impact item a item, com evidência observada (grep, leitura ou execução), numa tabela `Impact Verification`. Um finding só conta como resolvido com todos os itens `✓`.

A skill foi então executada de novo, do zero, sobre o código original do projeto 2 (restaurado do commit `6d1ce62`) numa sessão nova. O relatório refeito tem 16 findings. A diferença para os 17 da primeira execução é que a duplicação de código (AP-13) não foi reportada como finding próprio; os problemas da análise manual continuam cobertos (salvo o `.verbose()`, que nenhuma das duas execuções reportou). A Fase 3 conferiu 47/47 itens de Impact. Para o item da senha, a evidência foi `verifyPassword('123456', hash da conta criada sem pwd) → false`. A verificação independente refez o mesmo teste pelo caminho real (checkout sem `pwd` → hash gravado no banco): `false` para `123456`, `false` para `123` no usuário do seed, e um hash distinto por conta.

### Estrutura antes/depois

**Projeto 1 — code-smells-project** (4 arquivos / 780 LOC → 33 módulos / 1070 LOC)

```
ANTES                         DEPOIS
app.py                        app.py                    # entry point fino: create_app() + init_db() + seed_db()
controllers.py                .env.example
models.py                     src/
database.py                   ├── app.py                # create_app(): config, CORS, teardown, blueprints, error handlers
                              ├── config/settings.py    # os.environ com defaults seguros
                              ├── database.py           # conexão via flask.g, transaction(), init_db(), seed_db()
                              ├── domain/               # constants.py, exceptions.py
                              ├── models/               # produto, usuario, pedido, relatorio, sistema (SQL parametrizado)
                              ├── services/             # produto, usuario, pedido (transação), relatorio, notificacao, admin
                              ├── validators/           # produto, usuario, pedido
                              ├── controllers/          # produto, usuario, pedido, relatorio, sistema, admin
                              ├── views/routes.py       # 6 Blueprints, mesmos paths
                              └── middlewares/error_handler.py
```

**Projeto 2 — ecommerce-api-legacy** (3 arquivos / 180 LOC → 31 módulos / 603 LOC)

```
ANTES                         DEPOIS
src/app.js                    src/app.js                # createApp({ db }) + start(); guard require.main
src/AppManager.js             .env.example
src/utils.js                  src/
                              ├── config/index.js       # process.env com defaults
                              ├── database/             # connection.js (Promises + transação), schema.js (FKs), seed.js
                              ├── domain/               # constants.js, errors.js
                              ├── models/               # user, course, enrollment, payment, auditLog, report (JOIN)
                              ├── services/             # checkout (transacional), payment, report, user
                              ├── validators/           # checkout, user, common (inteiro positivo)
                              ├── controllers/          # checkout, report, user
                              ├── routes/               # index.js (/api) + um por entidade
                              ├── middlewares/          # asyncHandler.js, errorHandler.js
                              └── utils/                # logger.js, password.js (scrypt + senha aleatória inutilizável)
```

`package.json` e `api.http` não foram alterados.

**Projeto 3 — task-manager-api** (15 arquivos / 1158 LOC → 46 módulos / 1306 LOC, pastas originais mantidas)

```
ANTES                         DEPOIS
app.py                        app.py                    # create_app() + init_db(); `from app import app, db` continua válido
database.py                   seed.py                   # init_db(reset=True) + seed com o mesmo hash da aplicação
seed.py                       .env.example
models/  (3)                  config/settings.py        # novo
routes/  (3, com lógica)      domain/                   # novo: constants.py, exceptions.py, clock.py (utc_now)
services/ (1, sem uso)        models/  (3)              # to_dict sem senha; is_overdue() como fonte única
utils/   (1, quase sem uso)   validators/ (3)           # novo
                              services/ (6)             # task, user, auth, category, report, notification
                              controllers/ (6)          # novo
                              routes/   (6, só mapeiam) # categorias e login separados, mesmos paths
                              middlewares/error_handler.py  # novo
                              utils/helpers.py          # só o que é usado
```

`requirements.txt` perdeu `marshmallow` e `requests` (nunca importados); `python-dotenv`, que já estava pinado, passou a ser usado.

### Checklist de validação

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** | | | |
| Linguagem detectada corretamente | ✓ Python 3.13 | ✓ JavaScript/Node 22 | ✓ Python 3.13 |
| Framework detectado corretamente | ✓ Flask 3.1.1 | ✓ Express 4.22.1 | ✓ Flask 3.0.0 + SQLAlchemy |
| Domínio descrito corretamente | ✓ E-commerce | ✓ LMS com checkout | ✓ Task Manager |
| Nº de arquivos condiz com a realidade | ✓ 4 | ✓ 3 (+ api.http) | ✓ 15 |
| **Fase 2** | | | |
| Relatório segue o template | ✓ | ✓ | ✓ |
| Cada finding tem arquivo e linhas exatos | ✓ | ✓ | ✓ |
| Findings ordenados CRITICAL → LOW | ✓ | ✓ | ✓ |
| Mínimo de 5 findings | ✓ 17 | ✓ 16 | ✓ 17 |
| Detecção de APIs deprecated incluída | ✓ | ✓ | ✓ |
| Skill pausa e pede confirmação antes da Fase 3 | ✓ | ✓ | ✓ |
| **Fase 3** | | | |
| Estrutura de diretórios segue MVC | ✓ | ✓ | ✓ |
| Configuração extraída para módulo de config | ✓ `src/config/settings.py` | ✓ `src/config/index.js` | ✓ `config/settings.py` |
| Models criados para abstrair dados | ✓ 5 | ✓ 6 | ✓ 3 (mantidos e corrigidos) |
| Views/Routes separadas | ✓ `src/views/routes.py` | ✓ `src/routes/` | ✓ `routes/` só mapeiam |
| Controllers concentram o fluxo | ✓ 6 | ✓ 3 | ✓ 6 |
| Error handling centralizado | ✓ | ✓ | ✓ |
| Entry point claro | ✓ `app.py` | ✓ `src/app.js` com guard | ✓ `app.py` |
| Aplicação inicia sem erros | ✓ | ✓ | ✓ |
| Endpoints originais respondem corretamente | ✓ 19/19 rotas, 28/28 chamadas | ✓ 3/3 rotas, 9/9 chamadas | ✓ 22/22 rotas, 31/31 chamadas |

### Logs das aplicações após refatoração

Além da validação feita pela própria skill, cada aplicação foi validada de forma independente, em sequência e na porta padrão, por um smoke test externo (`docs/validacao/smoke.py`) que sobe o servidor, bate em todos os endpoints do contrato com payloads válidos e inválidos, confere status e chaves de topo do JSON, verifica a ausência de campos sensíveis e derruba o processo. Saída completa em `docs/validacao/smoke-project-{1,2,3}.txt` e logs dos servidores em `docs/validacao/server-project-{1,2,3}.log`. Trechos:

```
=== code-smells-project boot=OK (python app.py) ===
OK  GET    /health            -> 200 keys=['ambiente', 'counts', 'database', 'status', 'versao']   # sem secret_key/db_path
OK  GET    /usuarios          -> 200 keys=['dados', 'sucesso']                                      # sem campo senha
OK  POST   /login             -> 401 (payload: ' OR '1'='1' --)                                     # injection bloqueada
OK  POST   /pedidos           -> 400 (estoque insuficiente; rollback, nada gravado)
OK  POST   /admin/query       -> 403                                                                # desligado por flag
=== code-smells-project: 28/28 OK ===

=== ecommerce-api-legacy boot=OK (npm start) ===
OK  POST   /api/checkout      -> 200 keys=['enrollment_id', 'msg']       # cartão 4111... (api.http)
OK  POST   /api/checkout      -> 400 "Pagamento recusado"                # cartão 5111... (api.http)
OK  DELETE /api/users/1       -> 200 "Usuário deletado"
OK  DELETE /api/users/abc     -> 400 "Bad Request"
OK  GET    /api/admin/financial-report -> 200 list[2] item:['course', 'revenue', 'students']   # sem 'Unknown'
=== ecommerce-api-legacy: 9/9 OK ===

=== task-manager-api boot=OK (python seed.py && python app.py) ===
OK  GET    /tasks             -> 200 list[10] item:[..., 'overdue', 'user_name', 'category_name']
OK  GET    /users/1           -> 200 keys=['active', 'created_at', 'email', 'id', 'name', 'role', 'tasks']   # sem password
OK  POST   /login             -> 200 keys=['message', 'token', 'user']    # token aleatório, sem 'fake-jwt'
OK  GET    /reports/summary   -> 200 keys=['generated_at', 'overdue', 'overview', ...]
=== task-manager-api: 31/31 OK ===
```

### Mudanças de comportamento intencionais (documentadas pela skill)

Comuns aos três: campos de senha ou hash removidos das respostas; segredos saem do código para variáveis de ambiente com defaults seguros (`DEBUG=false`, host local); entradas malformadas que geravam 500 passam a responder 400; bancos locais recriados por causa da troca do esquema de senha. Específicas: no projeto 1, `/admin/query` e `/admin/reset-db` continuam registradas mas respondem 403 salvo flag de ambiente; no projeto 2, o `DELETE /api/users/:id` cascateia matrículas e pagamentos e a mensagem deixa de admitir "ficaram sujos no banco", contas criadas no checkout sem `pwd` recebem uma senha aleatória inutilizável em vez de `123456` (o campo segue opcional), o usuário do seed deixa de ter a senha `123`, e checkout recusado não grava mais o usuário; no projeto 3, o token de login passa a ser aleatório em vez de `fake-jwt-token-<id>`. Nomes de campos de entrada, paths, métodos e status codes de sucesso foram preservados em todos os endpoints, inclusive os campos `usr`, `eml`, `c_id` e `card` do checkout.

### Observações sobre o comportamento em stacks diferentes

- **Agnosticismo confirmado.** A mesma skill, sem nenhuma alteração entre projetos, detectou Python e JavaScript, SQL cru e ORM, callbacks e Blueprints. Os sinais por linguagem do catálogo foram suficientes; nenhum finding dependeu de nome de arquivo.
- **Estratégia B funcionou como projetado.** No projeto 3 a skill manteve `models/`, `routes/` e `services/` no lugar, criou só o que faltava, reaproveitou `Task.is_overdue()` e as constantes órfãs de `utils/helpers.py` em vez de criar novas, e manteve `python seed.py` funcionando.
- **Falsos positivos tratados.** Na primeira execução, nos dois projetos sem SQL injection, a skill rodou o sinal, leu o trecho e descartou com justificativa na saída da sessão, em vez de inflar o relatório.
- **Honestidade na validação.** Em nenhum projeto a skill escreveu "zero anti-patterns"; cada uma listou resíduos justificados (ex.: `this.lastID` dentro do wrapper de Promises, f-string que interpola apenas placeholders `?`).
- **Adaptação a ambiente hostil.** Na primeira execução, as Fases 3 dos três projetos foram executadas em paralelo por engano. A skill do projeto 1 encontrou a porta 5000 ocupada pelo projeto 3, não matou o processo alheio (regra da referência de validação) e validou em portas alternativas, mantendo 5000 como default do contrato. A validação independente posterior confirmou os resultados na porta padrão.
- **Diferença entre Flask puro e SQLAlchemy.** No projeto 1 a camada de dados virou funções com SQL parametrizado e um `to_dict` por entidade; no projeto 3 os `db.Model` existentes foram mantidos e a correção foi em `to_dict`, cascatas e substituição de `Model.query.get` por `db.session.get`. O playbook cobre os dois casos.
- **Iterações.** Os três projetos passaram nos critérios de aceite na primeira execução completa. A avaliação apontou uma falha que esses critérios não pegavam: o finding de senha do projeto 2 foi dado como resolvido com o impacto ainda presente. Isso levou a uma segunda iteração da skill (PB-04, PB-10, PB-13, AP-04/AP-15 e conferência do Impact na Fase 3) e a uma nova execução completa no projeto 2. Os projetos 1 e 3 não têm fallback de senha literal (o sinal novo do AP-04 não encontra ocorrência), por isso não foram reexecutados.

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

Para repetir a validação completa de um projeto (sobe o servidor, bate em todos os endpoints com payloads válidos e inválidos, confere status, chaves e ausência de campos sensíveis, e derruba o processo), use o smoke test externo a partir da raiz do repositório:

```bash
python docs/validacao/smoke.py 1   # code-smells-project
python docs/validacao/smoke.py 2   # ecommerce-api-legacy
python docs/validacao/smoke.py 3   # task-manager-api (roda o seed antes)
```

Cada execução termina com uma linha `=== <projeto>: N/N OK ===` e confirma que a porta ficou livre.

### Reutilizar a skill em outro projeto

Copie a pasta `.claude/skills/refactor-arch/` para a raiz do projeto-alvo e rode `claude "/refactor-arch"` a partir dela. Nada na skill depende destes três projetos.
