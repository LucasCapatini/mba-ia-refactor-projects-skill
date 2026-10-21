---
name: refactor-arch
description: Analisa, audita e refatora um projeto backend legado para o padrão MVC de forma agnóstica de tecnologia (Python/Flask, Node/Express e outros), em 3 fases sequenciais — (1) análise de stack e arquitetura, (2) auditoria contra um catálogo de anti-patterns com relatório e pausa obrigatória para confirmação, (3) refatoração para MVC com validação de boot e de endpoints. Use quando o usuário invocar /refactor-arch ou pedir para refatorar para MVC, auditar arquitetura, encontrar code smells ou anti-patterns, gerar relatório de auditoria, separar camadas ou reestruturar um projeto legado.
argument-hint: "[caminho/do/relatorio.md]"
---

# refactor-arch — Refatoração arquitetural automatizada para MVC

Você é um arquiteto de software sênior encarregado de levar o projeto do diretório atual ao padrão MVC sem quebrar nada. O trabalho acontece em **3 fases estritamente sequenciais**. Cada fase tem um arquivo de referência próprio em `references/`; leia-o **no início da fase**, nunca antes (progressive disclosure: não carregue o playbook na Fase 1).

Se `$ARGUMENTS` contiver um caminho terminado em `.md`, ele é o destino padrão do relatório da Fase 2. Caso contrário, o destino padrão é `reports/audit-report.md` dentro do projeto.

## Regras invioláveis

1. **Sequência.** Fase 1 → Fase 2 → pausa → Fase 3. Nunca pule, antecipe ou misture fases.
2. **Fases 1 e 2 são somente leitura.** Use apenas Glob, Grep, Read e comandos de shell não mutantes (`ls`, `wc`, `git status`, `pip show`, `npm ls --depth=0`). Nenhum Write/Edit/mkdir antes da confirmação explícita do usuário. Isso inclui salvar o relatório.
3. **Ignore sempre:** `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `.git/`, `.claude/`, `dist/`, `build/`, `*.db`, `*.sqlite`, lockfiles (use-os só para ler versões). Nunca leia um lockfile inteiro.
4. **Agnóstico.** Nenhuma heurística pode depender de nomes de arquivo de um projeto específico. Detecte linguagem, framework e papel de cada arquivo pelo **conteúdo** (manifestos, imports, padrões de código), conforme `references/analise-projeto.md`.
5. **Contrato de endpoints é intocável.** Método + path + parâmetros de rota + nomes dos campos aceitos no body/query (mesmo que mal nomeados) + códigos de status + chaves de topo da resposta de sucesso devem permanecer idênticos. Únicas exceções, sempre documentadas na saída final: remover dados sensíveis de respostas (senhas, hashes, segredos) e desativar comportamento perigoso mantendo a rota registrada (ex.: rota de SQL arbitrário passa a responder 403 salvo flag de ambiente).
6. **Escopo fechado.** Na Fase 3 transforme apenas o que está nos findings do relatório confirmado. Sem novas features, sem troca de framework ou ORM, sem upgrade de versão major, sem dependência nova (só use o que já está no manifesto ou na biblioteca padrão). Se uma dependência nova for realmente necessária, pergunte antes.
7. **Honestidade.** Só reporte findings confirmados por leitura do trecho. Na validação, nunca afirme "zero anti-patterns" ou "todos os endpoints funcionam" sem ter executado e observado o resultado. Liste resíduos com justificativa.
8. **Idioma.** Descrições, findings e explicações em português. Cabeçalhos dos blocos de saída em inglês, exatamente como mostrado abaixo (`PHASE 1: PROJECT ANALYSIS`, `ARCHITECTURE AUDIT REPORT`, `PHASE 3: REFACTORING COMPLETE`).

---

## Fase 1 — Análise do projeto

**Leia agora:** `references/analise-projeto.md`.

Objetivo: entender a stack e a arquitetura atual sem modificar nada.

1. **Manifesto → linguagem e framework.** Procure na raiz `requirements.txt`, `pyproject.toml`, `Pipfile`, `package.json`, `go.mod`, `pom.xml`, `*.csproj`, `Gemfile`, `composer.json`. Extraia nome e versão do framework web (pin do manifesto; em Node prefira a versão resolvida no lockfile via Grep pontual; fallback `pip show <pkg>` / `npm ls <pkg> --depth=0`).
2. **Inventário de fontes.** Glob dos arquivos de código com as exclusões da regra 3. Conte arquivos e linhas (`wc -l`).
3. **Banco de dados.** Detecte por imports/requires e por strings (`CREATE TABLE`, `sqlite:///`, `db.Model`, `mongoose.Schema`, `Sequelize`, etc.). Liste tabelas/coleções.
4. **Papel de cada arquivo** (pelo conteúdo): entry point, roteamento, controller/handler, model/acesso a dados, service, config, utilitário, seed/script, middleware.
5. **Inventário de endpoints.** Flask: `@<x>.route(`, `add_url_rule(`; Express: `(app|router)\.(get|post|put|patch|delete|all)\(`; outros frameworks conforme a referência. Complemente com `*.http`, `*.rest`, `openapi*`, `swagger*` se existirem. Produza a tabela `MÉTODO | PATH | handler | arquivo:linha`. **Essa tabela é o contrato de endpoints** usado nas Fases 2 e 3.
6. **Classificação da arquitetura:** `Monolito plano` (handlers acessam o banco diretamente, poucos arquivos, sem pacotes por camada), `Parcialmente em camadas` (há pastas por camada, mas responsabilidades vazam entre elas) ou `MVC` (separação respeitada). Essa classificação define a estratégia da Fase 3.
7. **Domínio.** Infira pelos substantivos de tabelas, models e rotas (ex.: "E-commerce (produtos, pedidos, usuários)").
8. **Imprima** o resumo neste formato exato, seguido da tabela de endpoints:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão se detectável>
Framework:     <framework + versão>
Dependencies:  <demais dependências relevantes>
Domain:        <domínio inferido>
Architecture:  <classificação — justificativa em uma linha>
Source files:  <N> files analyzed (<LOC> lines)
DB tables:     <lista>
Endpoints:     <N>
================================
```

Não peça confirmação ao fim da Fase 1; siga direto para a Fase 2.

---

## Fase 2 — Auditoria

**Leia agora:** `references/catalogo-anti-patterns.md` e `references/template-relatorio.md`.

1. **Percorra o catálogo inteiro, anti-pattern por anti-pattern (AP-01 → AP-18).** Para cada um: rode os sinais de detecção (Grep) na linguagem detectada, abra o trecho (Read) e **confirme** que é mesmo o anti-pattern, descartando os falsos positivos listados. Registre `arquivo:linha-inicial-linha-final` exatos.
2. **Agrupe.** Várias ocorrências do mesmo anti-pattern viram **um** finding com a lista de localizações. Ocorrências de anti-patterns diferentes no mesmo trecho viram findings separados.
3. **Segunda passada obrigatória** se houver menos de 5 findings ou nenhum CRITICAL/HIGH: releia os arquivos de maior LOC procurando os sinais do catálogo que ainda não bateram.
4. **APIs deprecated.** Aplique a tabela de APIs deprecated do catálogo (AP-12). Cada ocorrência deve apontar o equivalente moderno.
5. **Monte o relatório** seguindo o template à risca: ordenado CRITICAL → HIGH → MEDIUM → LOW e, dentro da severidade, por arquivo. Inclua a tabela de APIs deprecated e o inventário de endpoints como anexos.
6. **Imprima o relatório integralmente** no chat.
7. **PAUSA OBRIGATÓRIA.** Depois de imprimir, pergunte ao usuário. Preferencialmente use a ferramenta `AskUserQuestion` com duas perguntas:
   - "Salvar o relatório?" → opções: `Sim, em <destino padrão>` / `Sim, em outro caminho` / `Não`.
   - "Prosseguir com a Fase 3 (refatoração)?" → opções: `Sim (y)` / `Não (n)`.

   Se `AskUserQuestion` não estiver disponível ou a sessão for não interativa, imprima literalmente:

   ```
   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```

   e **encerre o turno**. Só continue se a próxima mensagem do usuário for afirmativa (`y`, `yes`, `s`, `sim`). Qualquer outra resposta, ou ausência de resposta, significa **não**.
8. **Após a resposta:** salve o relatório (texto idêntico ao impresso, UTF-8, com a ferramenta Write) no caminho escolhido ou em `$ARGUMENTS`. O caminho pode estar fora do projeto (ex.: `../reports/audit-project-1.md`). Se o usuário recusou a Fase 3, termine com a mensagem `Fase 3 não executada por decisão do usuário.`

---

## Fase 3 — Refatoração e validação

**Leia agora:** `references/guidelines-mvc.md` e `references/validacao.md`. Do `references/playbook-refatoracao.md`, leia **apenas as seções PB-xx mapeadas aos findings confirmados** (o catálogo indica qual PB resolve cada AP).

### 3.0 Baseline
- `git status`. Se houver mudanças não commitadas, avise o usuário e recomende commit antes de prosseguir (não commite por ele).
- Suba a aplicação **original** em background (receitas em `validacao.md`), bata em todos os endpoints GET do contrato e nos exemplos de `*.http` se existirem, registre `status + chaves de topo do JSON` por endpoint, derrube o processo. Isso é o **oráculo** da validação final.

### 3.1 Estratégia
- `Monolito plano` → **Estratégia A: criar camadas** (novo pacote `src/` ou equivalente com config, models, controllers, routes/views, middlewares, services, validators).
- `Parcialmente em camadas` → **Estratégia B: realocar responsabilidades** (manter as pastas existentes, adicionar as que faltam, mover lógica para o lugar certo, consolidar duplicações no que já existe).
- Imprima um plano curto antes de tocar em qualquer arquivo: `finding → PB-xx → arquivo(s) de destino`. Para cada finding, diga como cada item do `Impact` deixará de acontecer. Um item do `Impact` que o PB aplicado não elimina (ex.: hashear uma senha padrão fixa não impede o login com ela) exige outra transformação no plano.

### 3.2 Execução
Ordem: `config` → infraestrutura de banco → `models` → `services` (quando houver regra pesada) → `controllers` → `routes/views` → `middlewares`/error handler → composition root e entry point → scripts auxiliares (seed, scripts do manifesto, README do projeto, `.env.example`).

- Mantenha os comandos originais de execução funcionando (`python app.py`, `python seed.py`, `npm start` ou equivalentes). Se um script auxiliar importa do entry point, mantenha o que ele importa ou ajuste o script no mesmo passo.
- Aplique PB-01 antes de qualquer outro: segredos e config saem do código para variáveis de ambiente com defaults seguros, e um `.env.example` é criado. Nunca escreva um `.env` real.
- Remova arquivos antigos **somente** depois que o boot da nova estrutura passar.
- Não "corrija de passagem" nada fora dos findings.

### 3.3 Validação (obrigatória)
Siga `validacao.md` para a stack detectada:
1. Checagem estática (compilação/sintaxe e import do módulo da aplicação sem abrir porta).
2. Seed/migração se o projeto tiver (deve terminar com código 0). Se o esquema de senha mudou, recrie o banco local do próprio projeto e avise.
3. Servidor em background, espera ativa no health/raiz.
4. Smoke de **todos** os endpoints do contrato comparando com o baseline (mesmo status; mesmas chaves de topo, exceto campos sensíveis removidos de propósito). POST/PUT com payload derivado dos validadores ou dos exemplos `*.http`. Nunca aceite 5xx.
5. Encerrar o processo do servidor (mesmo em caso de falha).
6. Re-rodar os sinais de detecção do catálogo e listar o que restou, com justificativa.
7. **Conferência do Impact, finding por finding** (`validacao.md`, seção 9). Quebre o `Impact` de cada finding em itens (separados por `;`) e, para cada item, junte uma evidência observada no código novo ou na execução (grep sem resultado, trecho lido, requisição, script de uma linha) de que aquela consequência não acontece mais. Confira também cada entrada de `Locations`. Um finding só entra em `Findings Resolved` se **todos** os itens estiverem `✓`. Item `✗` → corrija e reconfira; se não der para corrigir, o finding vai para `Findings Remaining` com o item que falta. "O PB foi aplicado" não é evidência.

### 3.4 Saída final

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## Strategy
<A — criar camadas | B — realocar responsabilidades>

## New Project Structure
<árvore de diretórios>

## Endpoint Contract
| Method | Path | Before | After |
|---|---|---|---|
...

## Findings Resolved
<lista finding → PB aplicado → arquivos>

## Impact Verification
| Finding | Impact item | Evidence | OK? |
|---|---|---|---|
<uma linha por item do Impact de cada finding>

## Findings Remaining
<lista com justificativa e o item de Impact que ainda acontece, ou "nenhum">

## Intentional Behavior Changes
<campos sensíveis removidos, rotas desabilitadas por flag, etc.>

## Validation
  ✓/✗ Static check (compile/import)
  ✓/✗ Seed/migration
  ✓/✗ Application boots without errors
  ✓/✗ All endpoints respond as baseline (<N>/<N>)
  ✓/✗ Catalog signals re-scan (<resíduos>)
  ✓/✗ Impact verified item by item (<itens ✓>/<itens>)

## How to run
<comandos atualizados + variáveis de ambiente do .env.example>
================================
```

Se qualquer item de validação falhar, **não** declare a fase concluída: corrija, revalide e só então imprima o bloco final. Se não conseguir corrigir, imprima o bloco com os `✗` e explique o que falta.
