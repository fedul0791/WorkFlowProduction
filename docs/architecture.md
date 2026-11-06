# Initial architecture

- `frontend/`: Next.js App Router and TypeScript. Locale is part of the URL (`/de`, `/ru`, `/en`).
- `backend/`: FastAPI REST API. Routers, schemas, models, database access and services are separated.
- `database/`: local PostgreSQL runtime notes. PostgreSQL data is stored in a named Docker volume.
- SQLAlchemy 2.x is the persistence layer; Alembic owns schema migrations.
- Frontend exact dependencies are locked in `frontend/package-lock.json`; Python direct pins are listed in `backend/requirements.txt` and the tested transitive set in `backend/requirements.lock`.
- The initial migration is intentionally empty apart from Alembic's version bookkeeping. Business entities are deferred until the domain model is approved for implementation.
- Docker Compose runs PostgreSQL, applies migrations before starting the API, then starts the frontend.

No manufacturing process, permissions, employee records, QR behavior or demo dataset is modeled in this foundation stage.
