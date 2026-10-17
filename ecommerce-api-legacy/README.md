# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. Por padrão o banco SQLite é em memória e os seeds são carregados automaticamente no boot.

Exemplos de requisições estão em `api.http`.

### Variáveis de ambiente

Todas são opcionais e estão documentadas em `.env.example`:

| Variável | Default | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DB_PATH` | `:memory:` | Caminho do arquivo SQLite (`:memory:` recria schema e seeds a cada boot) |
| `PAYMENT_GATEWAY_KEY` | vazio | Credencial do gateway de pagamento (simulado) |
| `APPROVED_CARD_PREFIX` | `4` | Prefixo de cartão aprovado pelo gateway simulado |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |

Para usar um arquivo `.env` (nunca versionado): `cp .env.example .env` e `node --env-file=.env src/app.js`.

Seed manual (útil com `DB_PATH` apontando para arquivo): `node src/database/seed.js`.

## Estrutura

```
src/
├── app.js            # createApp({ db }) + start(); guard require.main
├── config/           # variáveis de ambiente com defaults seguros
├── database/         # conexão única (Promises + transação), schema, seed
├── domain/           # constantes e erros de domínio
├── models/           # SQL parametrizado por entidade
├── services/         # regras de negócio (checkout, pagamento, relatório, usuário)
├── validators/       # validação de entrada (mantém os nomes de campos do contrato)
├── controllers/      # HTTP ↔ domínio
├── routes/           # mapeamento método + path → controller
├── middlewares/      # asyncHandler e error handler central
└── utils/            # logger e hash de senha (scrypt)
```
