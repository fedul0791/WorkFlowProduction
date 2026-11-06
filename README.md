# WorkFlow Production

WorkFlow Production с локализованным интерфейсом, FastAPI, PostgreSQL, структурой предприятия, сотрудниками и управлением доступом.

## Требования

- Docker Desktop с запущенным Linux engine и Docker Compose v2.
- Git — для работы с репозиторием.
- Для запуска через Docker Node.js и Python на хосте не требуются: они входят в контейнеры.
- Для запуска frontend/backend вне Docker используйте Node.js 24 LTS и Python 3.13.

## Установка и настройка

Откройте PowerShell в папке проекта и создайте локальную конфигурацию:

```powershell
Copy-Item .env.example .env
```

Значения из `.env.example` предназначены только для локальной разработки. Файл `.env` исключён из Git. Не используйте эти значения в общей сети или production.

## Запуск

```powershell
docker compose up --build
```

После готовности сервисов:

- Интерфейс: <http://localhost:3001/de> (также `/ru` и `/en`).
- API: <http://localhost:8001>.
- OpenAPI/Swagger UI: <http://localhost:8001/docs>.
- Состояние API и подключения к БД: <http://localhost:8001/health>.

При запуске backend автоматически применяет Alembic миграции до запуска API.

Если порты 3001 или 8001 заняты, измените `FRONTEND_PORT` или `BACKEND_PORT` в локальном `.env`. Остановка без удаления данных:

```powershell
docker compose down
```

Команда `docker compose down -v` удаляет volume базы данных и все локальные данные; используйте её только если действительно хотите сбросить БД.

## Проверка работоспособности

```powershell
docker compose ps
Invoke-RestMethod http://localhost:8001/health
docker compose exec backend alembic current
```

Ожидаемый health-ответ при доступной БД содержит `status: ok` и `database: connected`. При недоступной базе `/health` возвращает HTTP 503. Если порт 8001 занят, измените `BACKEND_PORT` в локальном `.env`.

## Структура проекта

```text
frontend/       Next.js App Router, TypeScript, локализованные экраны
backend/        FastAPI, конфигурация, API, сервисы, SQLAlchemy, Alembic
database/       Материалы локальной базы и пояснения по volume
docs/           Архитектурные заметки и проектные решения
docker-compose.yml
.env.example
```

## Запуск frontend/backend без Docker

Frontend требует Node.js 24:

```powershell
cd frontend
npm ci
npm run dev
```

В отдельном терминале frontend можно проверить командами `npm run typecheck` и `npm run build`.

Backend требует Python 3.13 и доступную PostgreSQL. Из корня проекта:

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
$env:DATABASE_URL = "postgresql://user:password@localhost/dbname"
alembic upgrade head
uvicorn app.main:app --reload
```

## Структура предприятия

Раздел доступен по адресам `/de/betrieb`, `/ru/betrieb` и `/en/betrieb`. Создайте предприятие, затем добавляйте площадки, подразделения, участки и рабочие места. Оборудование можно создавать и назначать рабочим местам; смена рабочего места закрывает текущий период и создаёт новую запись истории. Удаление не выполняется: архивируйте элементы снизу вверх.

Структура хранится в PostgreSQL. Идентификатор предприятия одновременно служит `tenant_id`; связи дочерних сущностей проверяются составными внешними ключами. Изменения структуры и назначения пишутся в `audit_events`. API описан в OpenAPI по адресу <http://localhost:8001/docs>. Миграция `0002_enterprise_structure` применяется автоматически при старте backend.

## Доступ и сотрудники

Все API, кроме `/health`, требуют входа. Чтобы создать первое предприятие и администратора, сначала запустите сервисы, затем выполните в PowerShell:

```powershell
docker compose exec backend python -m app.bootstrap
```

Команда интерактивно запросит название предприятия, email и пароль администратора (минимум 12 символов). Если предприятие Stage 2 уже существует без учётных записей, команда создаст Administrator для него и сохранит дерево. Для нового пустого экземпляра она сначала создаст предприятие. Команда не сбрасывает и не удаляет данные. Дополнительные аккаунты создаются администратором в разделе Benutzerverwaltung и могут быть связаны с сотрудником.

Вход: `/de/anmelden`, `/ru/anmelden` или `/en/anmelden`. Сессия хранится сервером в PostgreSQL; cookie содержит только случайный opaque-токен, защищена HttpOnly и SameSite=Strict; изменяющие запросы требуют CSRF-токен. Пароли хешируются scrypt. Все изменения привязаны к пользователю в `audit_events`. Подробности см. в [STAGE_3_ACCESS.md](docs/STAGE_3_ACCESS.md).

Сотрудники, должности, квалификации, допуски, стандартные роли и настраиваемые permissions реализованы. Заказы/детали, QR, учёт времени, станочные циклы, планирование, аналитика и ИИ не входят в этот этап.

