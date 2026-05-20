# Job Application Tracker — CONTRACTS.md

**Team:** High Flyers  
**Coordinator:** Boma Okoli  
**Project:** Job Application Tracker  
**Week:** 6  

This document is the authoritative spec for Week 6. All role implementations follow it.
If a question arises about how something should behave, the answer is here.
If the answer isn't here, raise it in the team channel — the coordinator updates this doc and the tests.

---

## 1. Schema

### Existing skeleton tables (from Week 5 — no changes this week)

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| `users` | `id` | INTEGER | PK, autoincrement |
| `users` | `username` | VARCHAR(80) | NOT NULL, UNIQUE |
| `users` | `password_hash` | VARCHAR(256) | NOT NULL |
| `users` | `created_at` | DATETIME | NOT NULL, default=now |

### New tables added in Week 6

#### `job_applications`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `user_id` | INTEGER | NOT NULL, FK → `users.id` ON DELETE CASCADE | Owner |
| `company` | VARCHAR(120) | NOT NULL | |
| `position` | VARCHAR(120) | NOT NULL | |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT `'applied'` | Enum: `applied`, `interviewing`, `offered`, `rejected`, `withdrawn` |
| `applied_date` | DATE | NOT NULL | |
| `notes` | TEXT | NULLABLE | |
| `job_url` | VARCHAR(500) | NULLABLE | |
| `created_at` | DATETIME | NOT NULL, default=now | |
| `updated_at` | DATETIME | NOT NULL, default=now, onupdate=now | |

**Constraints:**
- UNIQUE on (`user_id`, `company`, `position`) — prevents duplicate applications to same role.

#### `job_insights` (populated from external API)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `company` | VARCHAR(120) | NOT NULL, UNIQUE | Cached lookup key |
| `rating` | FLOAT | NULLABLE | From API |
| `review_count` | INTEGER | NULLABLE | From API |
| `industry` | VARCHAR(120) | NULLABLE | From API |
| `headquarters` | VARCHAR(200) | NULLABLE | From API |
| `description` | TEXT | NULLABLE | From API |
| `fetched_at` | DATETIME | NOT NULL, default=now | Cache timestamp |

---

## 2. Endpoint Contracts

All routes require login unless noted. Non-authenticated requests redirect to `/login`.

### Standard response and error shapes

| Route type | Success shape | Error shape |
|------------|---------------|-------------|
| HTML GET route | Render the named template with the documented template data | Redirect to `/login?next=<url>` when anonymous; return 404 when the record is not owned by the user |
| HTML POST route | Redirect after successful create, update, or delete; flash a success message | Re-render the form with `errors={field: message}`, status 400 for validation errors |
| Duplicate create/update | N/A | Re-render the form with `errors={"duplicate": message}`, status 409 |
| External API enrichment | Redirect back to the application detail page after fetch/cache attempt | Flash a warning and redirect back; do not return 500 for expected API failures |

### 2.1 Auth routes (existing skeleton — no changes)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/login` | None | Login form |
| POST | `/login` | None | Authenticate; redirect to `/` on success |
| GET | `/register` | None | Registration form |
| POST | `/register` | None | Create user; redirect to `/` on success |
| GET | `/logout` | Required | Log out; redirect to `/login` |

### 2.2 Application routes (new this week)

#### `GET /applications`
- **Auth:** Required
- **Description:** List all applications belonging to current user
- **Query params:** `status` (optional filter)
- **Response:** Renders `applications/list.html`
- **Template data:**
  - `applications`: list of JobApplication rows for current user
  - `status_filter`: active filter value or None
  - `status_choices`: `["applied","interviewing","offered","rejected","withdrawn"]`

#### `GET /applications/new`
- **Auth:** Required
- **Response:** Renders `applications/form.html`
- **Template data:** `form_action="/applications/new"`, `application=None`, `errors={}`

#### `POST /applications/new`
- **Auth:** Required
- **Request body:** `company`, `position`, `status`, `applied_date`, `notes`, `job_url`
- **Success:** Insert row, redirect to `GET /applications/<id>`, flash `"Application saved."`
- **Failure:** Re-render form with `errors` dict, status 400
- **Error cases:**
  - 400 — validation failure
  - 409 — duplicate (user_id, company, position)

#### `GET /applications/<id>`
- **Auth:** Required
- **Ownership:** 404 if not owned by current user
- **Response:** Renders `applications/detail.html`
- **Template data:** `application`, `insight` (may be None)

#### `GET /applications/<id>/edit`
- **Auth:** Required
- **Ownership:** 404 if not owned
- **Response:** Renders `applications/form.html` with application pre-filled

#### `POST /applications/<id>/edit`
- **Auth:** Required
- **Ownership:** 404 if not owned
- **Success:** Update row, redirect to `GET /applications/<id>`, flash `"Application updated."`
- **Failure:** Re-render form with errors

#### `POST /applications/<id>/delete`
- **Auth:** Required
- **Ownership:** 404 if not owned
- **Success:** Delete row, redirect to `GET /applications`, flash `"Application deleted."`

#### `GET /applications/<id>/insight`
- **Auth:** Required
- **Ownership:** 404 if not owned
- **Description:** Fetch/refresh company insight, redirect to detail page
- **On API failure:** Flash warning, redirect back — no 500

---

## 3. External API Contract

**Service:** Clearbit Company API (primary) / API Ninjas Company Lookup (backup)  
**Auth:** API key in header  
**Rate limit:** ~50 requests/month free tier  
**Timeout:** 5 seconds  

| Source | Endpoint URL | Auth header | Use |
|--------|--------------|-------------|-----|
| Clearbit Company API | `https://company.clearbit.com/v2/companies/find?domain={domain}` | `Authorization: Bearer <CLEARBIT_API_KEY>` | Primary company enrichment lookup |
| API Ninjas Company Lookup | `https://api.api-ninjas.com/v1/company?name={company}` | `X-Api-Key: <API_NINJAS_KEY>` | Backup lookup if Clearbit is unavailable |

**Normalized response shape stored by our app:**

| Field | Type | Source/Meaning |
|-------|------|----------------|
| `company` | string | Company lookup key |
| `rating` | float/null | Company rating when provided by API |
| `review_count` | integer/null | Number of reviews when provided by API |
| `industry` | string/null | Company industry/category |
| `headquarters` | string/null | Company headquarters/location |
| `description` | string/null | Company description/profile text |
| `fetched_at` | datetime | Time this insight was cached |

**What our code does on failure:**

| Failure mode | Behavior |
|---|---|
| Timeout (>5s) | Catch `requests.Timeout`; return None; flash warning |
| HTTP 4xx/5xx | Return None; flash warning |
| Malformed JSON | Catch `json.JSONDecodeError`; return None; flash warning |
| Rate limit (429) | Return None; flash `"Company data temporarily unavailable."` |
| Empty results | Return None; no flash |

**Caching:** After successful fetch, store in `job_insights`. Serve from cache if `fetched_at` less than 24 hours old.

---

## 4. Authorization Rules

| Action | Who can do it | Non-authorized response |
|--------|--------------|------------------------|
| List applications | Current user (own rows only) | N/A |
| View detail | Owner only | 404 |
| Edit | Owner only | 404 |
| Delete | Owner only | 404 |
| View insight | Owner only | 404 |
| Refresh insight | Owner only | 404 |

**OWASP-style 404 rule:** Non-owners get 404, not 403. Prevents ID enumeration.

**Login requirement:** All `/applications/*` routes redirect to `/login?next=<url>` when accessed without session.

---

## 5. Role Boundaries

| Role | Owns | Does not touch |
|------|------|----------------|
| Coordinator (Boma) | `CONTRACTS.md`, `tests/test_client_templates.py`, `tests/test_integration.py` | Route handlers, models |
| Server-side (Darrell) | `app.py` route handlers, `services/company_api.py` | Templates, models |
| Client-side (Boma) | `templates/applications/`, `templates/base.html` nav | `app.py`, `models.py` |
| DB-and-security (Aden) | `models.py`, future `migrations/`, future `alembic.ini`, Flask-Login setup in `app.py` | Route handlers, templates |

**Aden role-specific note:** During active development, the app may still use
`SQLModel.metadata.create_all(engine)` as a development-only schema helper.
Once the schema is finalized, Aden owns upgrading the database path to Alembic
migrations and making `alembic upgrade head` the official schema update command.

---

## 6. Known Limitations (Deliberate)

| Limitation | Reason |
|---|---|
| No pagination on `/applications` list | Deferred to Week 7 |
| No file upload (resume attach) | Out of scope |
| Insight cache is time-based only | Acceptable for Week 6 |
| No email notifications | Out of scope |
| Status not enforced at DB level | SQLModel validation only; CHECK constraint deferred to Week 7 |
| Company API not load-tested | Rate-limit handling coded but unverified under concurrent load |
| Alembic migrations not active yet | Development uses automatic table creation until the schema is finalized |
