# Referência — Validação da Fase 3

Receitas para provar que a aplicação sobe e que o contrato de endpoints foi preservado. Use a mesma receita duas vezes: **antes** de refatorar (baseline, seção 3.0 do SKILL.md) e **depois** (validação final). Compare os dois resultados.

## 0. Princípios

- Sempre encerre o servidor que você subiu, mesmo quando algo falhar. Processo órfão segura a porta e trava arquivos `.db`.
- Nunca mate um processo que você não iniciou. Se a porta estiver ocupada, aborte e informe.
- Nunca aceite 5xx como "esperado".
- Não afirme nada que não tenha observado na saída de um comando.

## 1. Checar porta livre

| Ambiente | Comando |
|---|---|
| PowerShell | `Get-NetTCPConnection -LocalPort <porta> -State Listen -ErrorAction SilentlyContinue` (vazio = livre) |
| cmd/Git Bash no Windows | `netstat -ano \| findstr :<porta>` |
| Linux/macOS | `lsof -i :<porta>` ou `ss -ltnp \| grep :<porta>` |

Se a configuração permitir (`PORT` via ambiente depois do PB-01), você pode validar numa porta alternativa, mas o **default do contrato** deve continuar o original.

## 2. Checagem estática (sem abrir porta)

**Python**
```bash
python -m compileall -q <pacotes ou arquivos>          # sintaxe
python -c "import app"                                  # import do entry point; não pode abrir porta nem criar tabela implicitamente
python -c "from src.app import create_app; create_app()"   # se houver factory
```
Se `import app` subir o servidor, a factory/guard não está correta.

**Node**
```bash
node --check src/app.js            # repetir para cada arquivo .js novo
node -e "require('./src/app')"     # deve terminar sem ficar escutando (exige guard require.main)
```
Se o comando não retornar, falta o guard `if (require.main === module)`.

## 3. Seed / migração

- Se o projeto tem script de seed: `python seed.py` ou `node src/database/seed.js` deve terminar com código 0 e imprimir contagens.
- Se o esquema de senha mudou (texto puro/MD5 → hash com salt), o banco local antigo é inválido. Remova **apenas** o arquivo de banco do próprio projeto (ex.: `loja.db`, `tasks.db`, que estão no `.gitignore`) e avise o usuário na saída final.
- Bancos em memória: nada a fazer; schema + seed rodam no boot e devem ser aguardados antes do `listen`.

## 4. Subir o servidor em background

Desligue o reloader/debug na validação (`FLASK_DEBUG=0`, `use_reloader=False`, ou `DEBUG=false` via ambiente). Com reloader ligado o Flask cria um processo filho que sobrevive ao `kill` do pai.

**Bash (inclusive Git Bash no Windows)** — preferir a ferramenta Bash com `run_in_background`:
```bash
cd <projeto> && DEBUG=false PORT=5000 python app.py      # ou: npm start
```
Guarde o id da tarefa para encerrar depois.

**PowerShell 5.1** (sem `&&`, `curl` é alias de `Invoke-WebRequest`):
```powershell
$env:DEBUG = "false"
$proc = Start-Process python -ArgumentList "app.py" -WorkingDirectory "<projeto>" -PassThru -NoNewWindow
# Node:
# $proc = Start-Process node -ArgumentList "src/app.js" -WorkingDirectory "<projeto>" -PassThru -NoNewWindow
```

**Espera ativa** (até ~15 s):
```bash
for i in $(seq 1 15); do curl.exe -s -o /dev/null -w "%{http_code}" http://localhost:<porta>/health && break; sleep 1; done
```
```powershell
1..15 | ForEach-Object { try { (Invoke-WebRequest -UseBasicParsing http://localhost:<porta>/health).StatusCode; break } catch { Start-Sleep 1 } }
```
Use `/health` se existir; senão `/` ou o primeiro GET do contrato.

## 5. Smoke de endpoints (baseline e final)

Para **cada linha** da tabela de endpoints:

- **GET**: chamar direto; registrar status e chaves de topo do JSON.
- **POST/PUT**: payload derivado (nesta ordem) dos exemplos `*.http`, dos validadores do controller, ou do schema do model. Registrar status e chaves. Repetir com payload inválido para confirmar 400 (não 500).
- **DELETE**: usar um registro criado no próprio smoke, nunca os seeds que outros endpoints usam.
- Rotas perigosas desabilitadas por flag: devem responder 403 com a flag desligada.

```bash
curl.exe -s -w "\n%{http_code}" http://localhost:<porta>/<path>
curl.exe -s -w "\n%{http_code}" -X POST http://localhost:<porta>/<path> -H "Content-Type: application/json" -d '{"campo":"valor"}'
```
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:<porta>/<path> -ContentType "application/json" -Body '{"campo":"valor"}'
```

Chaves de topo: `python -c "import json,sys; print(sorted(json.load(sys.stdin)))"` ou `node -e "let d='';process.stdin.on('data',c=>d+=c).on('end',()=>console.log(Object.keys(JSON.parse(d)).sort()))"`.

Registre numa tabela:

| Method | Path | Baseline status | Baseline keys | After status | After keys | OK? |
|---|---|---|---|---|---|---|

Critério: mesmo status; mesmas chaves, **exceto** campos sensíveis removidos de propósito (listar em `Intentional Behavior Changes`).

Para Express, se existir `api.http`, reproduza **todos** os blocos dele, inclusive os de falha esperada (ex.: pagamento recusado → 400).

## 6. Encerrar o servidor

```bash
kill <pid>            # Bash; ou encerrar a tarefa em background
```
```powershell
Stop-Process -Id $proc.Id -Force
```
Confirme que a porta ficou livre (seção 1). Se um processo filho sobreviveu (reloader), encerre-o também — ele é seu, pois você o iniciou.

## 7. Re-scan do catálogo

Rode novamente os sinais de detecção dos APs que estavam no relatório. Para cada ocorrência restante, escreva uma justificativa (ex.: "print em seed.py — script de CLI, fora do escopo") ou corrija. Nunca escreva "zero anti-patterns" sem este re-scan.

## 8. Diff do contrato

**Flask**
```bash
python -c "from app import app; print('\n'.join(sorted(f'{sorted(r.methods - {\"HEAD\",\"OPTIONS\"})} {r.rule}' for r in app.url_map.iter_rules() if r.endpoint != 'static')))"
```
**Express 4**
```bash
node -e "const {createApp}=require('./src/app'); /* se createApp precisar de db, use um stub */" 
```
Se não for prático listar as rotas programaticamente no Express, o smoke completo da seção 5 é o oráculo.

Compare com a tabela da Fase 1: nenhuma rota pode sumir ou mudar de método.

## 9. Checklist final (copiar para a saída da Fase 3)

```
  ✓/✗ Static check (compile/import sem efeitos colaterais)
  ✓/✗ Seed/migration (exit 0)
  ✓/✗ Application boots without errors
  ✓/✗ All endpoints respond as baseline (<N>/<N>)
  ✓/✗ Dangerous routes disabled by default (403)
  ✓/✗ Sensitive fields absent from responses
  ✓/✗ Catalog signals re-scan (<resíduos justificados>)
  ✓/✗ Server process terminated, port free
```
