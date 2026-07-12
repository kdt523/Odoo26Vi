# AssetFlow — Enterprise Asset & Resource Management System

AssetFlow tracks, allocates, and maintains physical assets and shared resources (equipment,
furniture, vehicles, rooms) across any organisation. It covers:

- **Asset lifecycle** tracking (Available → Allocated → UnderMaintenance → Retired/Disposed)
- **Allocation & transfer** with conflict handling
- **Time-slot resource booking** with overlap validation
- **Maintenance approval** workflow
- **Structured audit cycles**
- **Role-based dashboards** and notifications

> Explicitly **out of scope**: purchasing, invoicing, accounting.

---

## Architecture — Two-Service Monorepo

```
assetflow/
├── frontend/          React + Vite (client-side only)
├── backend/
│   ├── core-api/      FastAPI  — auth, assets, allocations, bookings, maintenance, audits
│   └── reports-api/   Flask    — reports, analytics, notifications, activity log
├── .env.example
└── README.md
```

Both backend services **share one PostgreSQL database**.
`core-api` owns the schema migrations (Alembic).
`reports-api` connects in **read-heavy** mode (sync SQLAlchemy) and mirrors only the models it needs.

### Auth split
- JWT is **issued** by `core-api` (`/api/auth/login`)
- `reports-api` **validates** the same JWT using the shared `JWT_SECRET` — no separate login

---

## Roles

| Role | Promoted by |
|---|---|
| Employee | Self-signup (default) |
| Department Head | Admin only |
| Asset Manager | Admin only |
| Admin | Admin only |

---

## Quick Start (local dev)

### 1 — Prerequisites
- PostgreSQL installed locally
- Python 3.11+
- Node 20+

### 2 — Environment
```bash
cp .env.example .env
# Edit .env — at minimum change JWT_SECRET
```


### 4 — core-api
```bash
cd backend/core-api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
# Swagger UI → http://localhost:8000/docs
```

### 5 — reports-api
```bash
cd backend/reports-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask run --port 8001 --reload
# Routes → http://localhost:8001/api/reports/...
```

### 6 — Frontend
```bash
cd frontend
npm install
npm run dev
# App → http://localhost:5173
```



---

## API Overview

### core-api (FastAPI) — `http://localhost:8000`

| Prefix | Module |
|---|---|
| `/api/auth` | Signup, login, JWT |
| `/api/org` | Departments, categories, employee directory |
| `/api/assets` | Asset registry + search |
| `/api/allocations` | Allocate, transfer, return |
| `/api/bookings` | Resource booking + calendar |
| `/api/maintenance` | Maintenance requests + workflow |
| `/api/audits` | Audit cycles + items |

Interactive docs: `http://localhost:8000/docs`

### reports-api (Flask) — `http://localhost:8001`

| Prefix | Module |
|---|---|
| `/api/reports` | Utilization, maintenance freq, allocation summary, heatmap, export |
| `/api/notifications` | List + mark-read for current user |
| `/api/activity-log` | Read-only audit trail |

---

## Database Migrations

Only `core-api` manages migrations:

```bash
cd backend/core-api
alembic revision --autogenerate -m "your message"
alembic upgrade head
alembic downgrade -1
```

---


