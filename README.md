# Finance Data Processing and Access Control Backend

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> A production-grade, async REST API for financial data processing with role-based access control, dashboard analytics, and exact monetary precision.

---

## Feature Highlights

| Feature | Details |
|---------|---------|
| **Authentication** | Stateless JWT with bcrypt password hashing |
| **RBAC** | Three-tier roles — Viewer, Analyst, Admin |
| **Exact Precision** | Integer-cents storage with Decimal API boundaries |
| **Dashboard Analytics** | Income/expense totals, category breakdown, monthly trends |
| **Search** | Case-insensitive ILIKE across descriptions and categories |
| **Soft Delete** | Records are marked, never destroyed |
| **Rate Limiting** | 100 requests/minute per IP via SlowAPI |
| **Pagination** | Cursor-based with total counts and page metadata |
| **Tested** | Unit + integration tests with Pytest |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) — async, type-safe, auto-documented |
| Database | [PostgreSQL](https://www.postgresql.org/) via [asyncpg](https://github.com/MagicStack/asyncpg) |
| ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async mapped columns) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Auth | [python-jose](https://github.com/mpdavis/python-jose) (JWT) + [bcrypt](https://github.com/pyca/bcrypt) |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) with strict field constraints |
| Rate Limiting | [SlowAPI](https://github.com/laurentS/slowapi) |
| Testing | [Pytest](https://docs.pytest.org/) + [HTTPx](https://www.python-httpx.org/) |

---

## Architecture & Design Decisions

### 1. Integer-Cents Monetary Storage

> **Problem**: Floating-point arithmetic causes silent rounding errors in financial calculations.
> `0.1 + 0.2 = 0.30000000000000004`

**Solution**: A three-layer precision pipeline that eliminates floating-point entirely:

```
API Input (Decimal)  →  Service Layer (× 100)  →  Database (Integer cents)
   "5000.50"                500050                     500050
                                                         ↓
API Output (Decimal) ←  Schema Layer (÷ 100)  ←  Database (Integer cents)
   "5000.50"                500050                     500050
```

- **Input**: Pydantic validates `Decimal` with `@field_validator` enforcing ≤ 2 decimal places
- **Storage**: PostgreSQL `BIGINT` column — no rounding, no precision loss, no locale issues
- **Output**: `cents_to_dollars()` utility converts back using exact `Decimal` arithmetic
- **Bonus**: PostgreSQL `CHECK(amount > 0)` constraint acts as a database-level guard rail

### 2. Role-Based Access Control (RBAC)

Three roles with escalating privileges, enforced at two levels:

```
Viewer    →  View own records, own dashboard
Analyst   →  View own records, own dashboard, access insights
Admin     →  Full CRUD on all records, global dashboard, user management
```

**Implementation**: A reusable `RequireRole` dependency injected into route handlers:
```python
@router.post("/records/")
async def create_record(
    user: User = Depends(RequireRole(Role.ADMIN)),  # ← Enforced here
):
```

**Data scoping** happens at the repository layer — non-admins automatically get a `WHERE user_id = :id` filter applied to every query. This means access control is enforced at the SQL level, not just the API level.

### 3. Safety-First Soft Deletion

Records are never physically deleted. A boolean `is_deleted` flag is set, and all queries automatically filter with `WHERE is_deleted IS FALSE`. This provides:
- **Audit trail** — historical data is always recoverable
- **Referential integrity** — no orphaned foreign keys
- **Compliance readiness** — financial data retention requirements

### 4. Layered Architecture

```
Router  →  Service  →  Repository  →  Database
  ↑          ↑            ↑
Schema    Business     Raw SQL
Validation  Logic      Queries
```

Each layer has a single responsibility:
- **Routers**: HTTP concerns only (status codes, query params, response wrapping)
- **Services**: Business rules, access control, data transformation
- **Repositories**: Pure data access — no business logic, easily testable/mockable

---

## Local Development & Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Make (optional, for convenience commands)

### 1. Clone & Setup
```bash
git clone https://github.com/0bVdnt/fin-dashboard-api.git
cd fin-dashboard-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start PostgreSQL
```bash
docker-compose up -d
```

### 3. Run Migrations
```bash
alembic upgrade head
```

### 4. Start the Server
```bash
uvicorn app.main:app --reload
```

**Swagger UI** → [http://localhost:8000/docs](http://localhost:8000/docs)
**ReDoc** → [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Run Tests
```bash
pytest -v
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auth/register` | — | Register a new user (default: viewer) |
| `POST` | `/api/v1/auth/login` | — | Login and receive JWT |
| `GET` | `/api/v1/auth/me` |  | Get current user profile |

### User Management *(Admin only)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/users/` | List users (filter by role, status) |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `PATCH` | `/api/v1/users/{id}/role` | Change user role |
| `PATCH` | `/api/v1/users/{id}/status` | Activate / deactivate user |

### Financial Records
| Method | Endpoint | Roles | Description |
|--------|----------|-------|-------------|
| `POST` | `/api/v1/records/` | Admin | Create income/expense record |
| `GET` | `/api/v1/records/` | All | List records (paginated, filterable, searchable) |
| `GET` | `/api/v1/records/{id}` | All | Get single record |
| `PATCH` | `/api/v1/records/{id}` | Admin | Partial update |
| `DELETE` | `/api/v1/records/{id}` | Admin | Soft-delete |

**Query Parameters** for `GET /records/`:
| Param | Type | Example | Description |
|-------|------|---------|-------------|
| `type` | string | `income` | Filter by `income` or `expense` |
| `category` | string | `Salary` | Exact category match |
| `search` | string | `April` | ILIKE search on description & category |
| `date_from` | date | `2026-01-01` | Start date (inclusive) |
| `date_to` | date | `2026-12-31` | End date (inclusive) |
| `page` | int | `1` | Page number |
| `per_page` | int | `20` | Items per page (max 100) |

### Dashboard
| Method | Endpoint | Roles | Description |
|--------|----------|-------|-------------|
| `GET` | `/api/v1/dashboard/summary` | All | Full analytics summary |

**Response includes:**
- Total income, expenses, net balance
- Expense breakdown by category
- Monthly income vs. expense trends
- 5 most recent transactions

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check with DB connectivity status |

---

## Project Structure

```
app/
├── config.py                     # Environment settings (Pydantic BaseSettings)
├── database.py                   # Async engine, session factory, get_db dependency
├── main.py                       # Application factory with middleware registration
│
├── core/
│   ├── jwt.py                    # JWT creation and decoding
│   └── security.py               # Bcrypt password hashing
│
├── errors/
│   ├── exceptions.py             # AppException → NotFound, Forbidden, Conflict, etc.
│   └── handlers.py               # Global exception → JSON response handlers
│
├── middleware/
│   ├── auth.py                   # get_current_user dependency (JWT → User)
│   └── rbac.py                   # RequireRole dependency (role enforcement)
│
├── models/
│   ├── user.py                   # User model (roles, status, timestamps)
│   └── record.py                 # FinancialRecord model (cents, soft-delete)
│
├── repositories/
│   ├── user_repository.py        # User CRUD + listing with filters
│   ├── record_repository.py      # Record CRUD + search + pagination
│   └── dashboard_repository.py   # Aggregation queries (SUM, GROUP BY)
│
├── routers/
│   ├── auth.py                   # /auth/register, /auth/login, /auth/me
│   ├── users.py                  # /users/ (admin management)
│   ├── records.py                # /records/ (CRUD + search)
│   ├── dashboard.py              # /dashboard/summary
│   └── health.py                 # /health
│
├── schemas/
│   ├── common.py                 # ApiResponse[T], Meta, ErrorDetail
│   ├── user.py                   # Role enum, Register/Login/Token schemas
│   ├── record.py                 # Create/Update/Response + RecordType enum
│   └── dashboard.py              # Summary, CategoryTotal, TrendData
│
├── services/
│   ├── auth_service.py           # Register, login, token generation
│   ├── user_service.py           # Role/status updates with business rules
│   ├── record_service.py         # Record CRUD with RBAC + cent conversion
│   └── dashboard_service.py      # Aggregation orchestration
│
└── utils/
    └── money.py                  # dollars_to_cents(), cents_to_dollars()
```

---

## Assumptions & Tradeoffs

### Design Choices

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| **Integer cents storage** | Eliminates all floating-point precision bugs | Requires conversion at API boundaries; amounts limited to 2 decimal places |
| **Soft delete over hard delete** | Preserves audit trail and allows recovery | Increases storage over time; queries must always filter `is_deleted` |
| **JWT with DB re-fetch** | Role/status changes take effect immediately | Adds one DB query per authenticated request (mitigated by connection pooling) |
| **Global rate limiting** | Simple to implement and reason about | Doesn't allow endpoint-specific rate policies (e.g., stricter on `/auth/login`) |
| **Sync Alembic with async app** | Alembic's migration runner is inherently synchronous | Requires `run_async()` bridge in `env.py`; no impact on runtime performance |
| **Viewer as default role** | Principle of least privilege — safest default | Requires admin intervention to promote users; no self-service role escalation |

### Security Considerations

- **Password hashing**: bcrypt with automatic salt generation (12 rounds)
- **JWT secrets**: Configurable via environment variables; defaults are for development only
- **Email enumeration prevention**: Login returns identical errors for "user not found" and "wrong password"
- **Self-modification guards**: Admins cannot change their own role or deactivate themselves (prevents lockout)
- **Input validation**: Pydantic `model_config = {"extra": "forbid"}` rejects unknown fields

### What I'd Add With More Time

- **Refresh tokens** — Currently only short-lived access tokens; a refresh token flow would improve UX
- **Email verification** — Validate email ownership before activating accounts
- **Caching** — Redis-backed caching for dashboard aggregations (they're read-heavy)
- **Structured logging** — JSON logging with correlation IDs for observability
- **CI/CD** — GitHub Actions pipeline for lint + test + Docker build
- **Export** — CSV/PDF export of financial records and reports

---