# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.
Refatorada para o padrão MVC (estratégia A: criação de camadas em `src/`).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # opcional: todos os valores têm default seguro
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado e populado
com produtos e usuários de exemplo no primeiro boot (schema e seeds rodam apenas em `python app.py`,
nunca no import).

Usuários de exemplo (senhas armazenadas com hash): `admin@loja.com` / `admin123`,
`joao@email.com` / `123456`, `maria@email.com` / `senha123`.

Se você já tinha um `loja.db` da versão anterior, apague-o: o esquema de senha e as chaves
estrangeiras mudaram.

### Variáveis de ambiente (`.env.example`)

| Variável | Default | Uso |
|---|---|---|
| `SECRET_KEY` | `dev-only-change-me` | Chave da aplicação Flask (troque fora de desenvolvimento) |
| `DEBUG` | `false` | Debug/reloader do Flask |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `DB_PATH` | `loja.db` | Caminho do SQLite |
| `APP_ENV` | `development` | Valor exibido em `ambiente` no `/health` |
| `LOG_LEVEL` | `INFO` | Nível do `logging` |
| `ADMIN_SQL_ENABLED` | `false` | Libera `POST /admin/query` (SQL arbitrário). Desligado responde 403 |
| `ADMIN_RESET_ENABLED` | `false` | Libera `POST /admin/reset-db`. Desligado responde 403 |

## Estrutura

```
app.py                      # entry point: create_app() + init_db() + seed_db() + app.run()
src/
├── app.py                  # create_app(): config, CORS, conexão por requisição, blueprints, error handlers
├── config/settings.py      # Config lida de variáveis de ambiente
├── database.py             # get_connection() via flask.g, transaction(), init_db(), seed_db()
├── domain/                 # constants.py (categorias, status, faixas) e exceptions.py
├── models/                 # SQL parametrizado + serialização por entidade (produto, usuario, pedido, relatorio, sistema)
├── services/               # regras de negócio (pedido, relatório, auth, notificação, admin)
├── validators/             # validação de entrada, lança ValidationError
├── controllers/            # HTTP <-> serviços, sem SQL nem regra
├── views/routes.py         # Blueprints: método + path -> controller
└── middlewares/error_handler.py
```

Smoke rápido: `curl http://127.0.0.1:5000/health`.
