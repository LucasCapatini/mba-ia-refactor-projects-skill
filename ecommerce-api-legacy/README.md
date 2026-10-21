# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC pela skill `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://127.0.0.1:3000`. O banco SQLite é em memória por padrão: schema e seeds são criados no boot, antes de a porta abrir.

Exemplos de requisições estão em `api.http`.

## Configuração

Todas as variáveis são opcionais (veja `.env.example`). Para usar um arquivo `.env` sem dependência extra:

```bash
node --env-file=.env src/app.js
```

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `HOST` | `127.0.0.1` | Interface de escuta (use `0.0.0.0` para expor na rede) |
| `DB_PATH` | `:memory:` | Caminho do banco SQLite |
| `APPROVED_CARD_PREFIX` | `4` | Gateway simulado: cartões com este prefixo são aprovados |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |

## Estrutura

```
src/
├── app.js            # createApp({ db }) + start() (guard require.main)
├── config/           # variáveis de ambiente
├── database/         # conexão única em Promises, transação, schema, seed
├── domain/           # constantes e erros de domínio
├── models/           # SQL parametrizado por entidade
├── services/         # checkout, pagamento simulado, relatório, usuário
├── validators/       # validação do body e dos parâmetros
├── controllers/      # HTTP ↔ services
├── routes/           # mapeamento método + path → controller
├── middlewares/      # asyncHandler e error handler central
└── utils/            # logger e hash de senha (scrypt)
```

## Observações

- O usuário semente e as contas criadas no checkout sem `pwd` recebem uma senha aleatória inutilizável (não há login por senha para elas).
- Remover um usuário remove também as matrículas e os pagamentos dele (`ON DELETE CASCADE`).
