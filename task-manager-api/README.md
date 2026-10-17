# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Após a refatoração para MVC, a estrutura é:

```
app.py            # create_app() (composition root) + entry point
seed.py           # recria o schema e popula dados de exemplo
config/           # leitura de variáveis de ambiente
database.py       # instância do ORM, init_db(), commit()
domain/           # constantes, exceções e relógio UTC
models/           # entidades e serialização (to_dict)
validators/       # validação de entrada
services/         # regras de negócio e consultas
controllers/      # request -> validator -> service -> resposta
routes/           # blueprints que só mapeiam path -> controller
middlewares/      # error handler central
utils/            # utilitários puros
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # opcional; ajuste as variáveis
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` por padrão. O `seed.py` recria o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot** e sempre que atualizar o projeto, pois as senhas passaram a usar hash com salt e bancos antigos (MD5) não permitem login.

## Variáveis de ambiente (`.env.example`)

| Variável | Default | Descrição |
|---|---|---|
| `SECRET_KEY` | `dev-only-change-me` | Chave de sessão do Flask. Troque em produção. |
| `DEBUG` | `false` | Liga o debugger/reloader do Flask. |
| `HOST` | `127.0.0.1` | Interface de bind. Use `0.0.0.0` para expor na rede. |
| `PORT` | `5000` | Porta HTTP. |
| `LOG_LEVEL` | `INFO` | Nível do `logging`. |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI SQLAlchemy. |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | `localhost` / `587` / vazio / vazio | Credenciais do `NotificationService`. |

Usuários do seed: `joao@email.com` / `1234`, `maria@email.com` / `abcd`, `pedro@email.com` / `pass`.
