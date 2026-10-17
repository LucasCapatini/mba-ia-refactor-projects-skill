# Referência — Template do relatório de auditoria (Fase 2)

O relatório impresso no chat e o arquivo salvo devem ser **idênticos** e seguir este esqueleto. Substitua tudo entre `<>`. Não adicione seções fora das previstas; não omita seções (use "nenhum" quando vazio).

## Regras de preenchimento

1. **Ordenação:** CRITICAL → HIGH → MEDIUM → LOW. Dentro da severidade, por arquivo (ordem alfabética) e depois por linha.
2. **Numeração:** findings numerados sequencialmente (`#1`, `#2`, ...) na ordem final.
3. **Localização:** sempre `arquivo:linha` ou `arquivo:início-fim`, caminho relativo à raiz do projeto. Múltiplas ocorrências do mesmo anti-pattern ficam num só finding, listadas em `Locations`.
4. **ID do catálogo:** cada finding referencia o `AP-xx` e o(s) `PB-xx` que o resolve(m).
5. **Descrição:** o que está errado, em 1 a 3 frases, citando o trecho relevante.
6. **Impact:** consequência concreta (segurança, manutenção, performance).
7. **Recommendation:** ação objetiva, nomeando a camada de destino quando for mudança estrutural.
8. **Summary:** as contagens devem bater com a lista.
9. **APIs deprecated:** sempre presente, mesmo que vazia.
10. **Endpoints:** copie a tabela da Fase 1 como anexo; ela é o contrato que a Fase 3 deve preservar.

## Esqueleto

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <linguagem> + <framework> <versão>
Files:   <N> analyzed | ~<LOC> lines of code
Date:    <AAAA-MM-DD>
Architecture: <classificação da Fase 1>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>
Total: <n> findings

## Findings

### #<n> [<SEVERIDADE>] <Nome do anti-pattern> (AP-<xx>)
File: <arquivo:início-fim>
Locations: <lista adicional "arquivo:linhas — contexto curto", ou omitir se só uma>
Description: <o que está errado>
Impact: <consequência>
Recommendation: <ação> → PB-<xx>

### #<n+1> ...

## Deprecated APIs
| API | Location(s) | Modern equivalent |
|---|---|---|
| <api> | <arquivo:linha, ...> | <substituto> |
(ou: "Nenhuma API deprecated detectada.")

## Endpoint Contract (from Phase 1)
| # | Method | Path | Handler | Location |
|---|--------|------|---------|----------|
| 1 | <GET> | </path> | <handler> | <arquivo:linha> |

## Refactoring Strategy Preview
Strategy: <A — criar camadas | B — realocar responsabilidades>
Rationale: <uma linha baseada na classificação>

================================
Total: <n> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Mini-exemplo (fictício, para calibrar o nível de detalhe)

```
### #1 [CRITICAL] SQL Injection (AP-02)
File: repositorio.py:41-44
Locations: repositorio.py:41-44 — busca por id; repositorio.py:88-91 — login
Description: Queries montadas por concatenação de strings com valores vindos de `request` ("SELECT * FROM clientes WHERE id = " + str(id)). No login, email e senha entram direto na cláusula WHERE.
Impact: Leitura e alteração arbitrária do banco; bypass de autenticação com `' OR '1'='1`.
Recommendation: Substituir por bind parameters (`?`) em todas as queries do módulo e mover para `models/cliente_model.py` → PB-02
```
