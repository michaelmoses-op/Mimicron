# TimescaleDB migrations

Plain SQL files in `migrations/` applied in lexical order by `migrate.sh`.

Local apply (infra running):

```bash
make migrate
```

Connection settings come from `.env` (see `.env.example`).
