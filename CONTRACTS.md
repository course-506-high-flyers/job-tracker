# Job Application Tracker — CONTRACTS.md

**Team:** High Flyers  
**Coordinator:** Boma Okoli  
**Project:** Job Application Tracker  
**Week:** 7 (updated from Week 6)  

This document is the authoritative spec. All role implementations follow it.
Week 7 additions are marked with `[Week 7]`.

---

## 1. Schema

### Existing tables (Week 6 — no changes)

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| `users` | `id` | INTEGER | PK, autoincrement |
| `users` | `username` | VARCHAR(80) | NOT NULL, UNIQUE |
| `users` | `password_hash` | VARCHAR(256) | NOT NULL |
| `users` | `created_at` | DATETIME | NOT NULL, default=now |

### `job_applications` (Week 6)

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PK, autoincrement |
| `user_id` | INTEGER | NOT NULL, FK → `users.id` ON DELETE CASCADE |
| `company` | VARCHAR(120) | NOT NULL |
| `position` | VARCHAR(120) | NOT NULL |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT `'applied'` |
| `applied_date` | DATE | NOT NULL |
| `notes` | TEXT | NULLABLE |
| `job_url` | VARCHAR(500) | NULLABLE |
| `created_at` | DATETIME | NOT NULL, default=now |
| `updated_at` | DATETIME | NOT NULL, default=now |

### `job_insights` (Week 6)

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PK, autoincrement |
| `company` | VARCHAR(120) | NOT NULL, UNIQUE |
| `rating` | FLOAT | NULLABLE |
| `review_count` | INTEGER | NULLABLE |
| `industry` | VARCHAR(120) | NULLABLE |
| `headquarters` | VARCHAR(200) | NULLABLE |
| `description` | TEXT | NULLABLE |
| `fetched_at` | DATETIME | NOT NULL, default=now |

### `oauth_identity` [Week 7]

Links external provider identities to local users.
One user may have multiple OAuth identities (one per provider).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `user_id` | INTEGER | NOT NULL, FK → `users.id` ON DELETE CASCADE | |
| `provider` | VARCHAR(50) | NOT NULL | e.g. `"github"` |
| `provider_user_id` | VARCHAR(255) | NOT NULL | GitHub numeric user ID |
| `provider_login` | VARCHAR(255) | NULLABLE | GitHub username/login |
| `provider_email` | VARCHAR(255) | NULLABLE | May be null if GitHub email is private |
| `created_at` | DATETIME | NOT NULL, default=now | |
| `updated_at` | DATETIME | NOT NULL, default=now | |

**Constraints:**
- UNIQUE on (`provider`, `provider_user_id`) — one identity per provider per user

---

## 2. Endpoint Contracts

### 2.1 Existing auth routes (Week 6)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/login` | None | Login form — now includes GitHub button [Week 7] |
| POST | `/login` | None | Password authentication |
| GET | `/register` | None | Registration form |
| POST | `/register` | None | Create user |
| GET/POST | `/logout` | Required | Clear session, redirect to home |

### 2.2 OAuth routes [Week 7]

#### `GET /login/github`
- **Auth:** None
- **Description:** Initiates GitHub OAuth flow via Authlib
- **Behavior:** Calls `oauth.github.authorize_redirect(callback_url)`
- **Response:** 302 redirect to GitHub authorization page
- **Error:** If `OAUTH_CLIENT_ID` is missing → 500 on startup (strict env load)

#### `GET /auth/github/callback`
- **Auth:** None (GitHub redirects here after user authorizes)
- **Description:** Handles OAuth callback, creates or links user
- **Query params:** `code` (from GitHub), `state` (CSRF token from Authlib)
- **Behavior:**
  1. Exchange `code` for access token via Authlib
  2. Fetch user info from `https://api.github.com/user`
  3. Look up `oauth_identity` by (`provider=github`, `provider_user_id`)
  4. If found → load linked `User`, call `login_user()`
  5. If not found → create `User` (username from login, fallback to id),
     create `OAuthIdentity`, call `login_user()`
- **Success:** Redirect to `/applications`
- **Error cases:**
  - GitHub returns error param → flash warning, redirect to `/login`
  - Token exchange fails → flash warning, redirect to `/login`
  - Missing `login` field in payload → use `f"github_{provider_user_id}"` as username
  - Missing `email` field → store `None` in `provider_email` (do not crash)

### 2.3 Test backdoor route [Week 7]

#### `GET /test/login/<username>`
- **Auth:** None
- **Availability:** Only when `app.config["TESTING"] is True` — returns 404 otherwise
- **Description:** Creates user if not exists, logs them in, redirects to `/applications`
- **Purpose:** Allows Playwright tests to bypass GitHub OAuth entirely

### 2.4 Application routes (Week 6 — unchanged)

All `/applications/*` routes unchanged from Week 6 CONTRACTS.md.

---

## 3. External API Contract

### GitHub OAuth [Week 7]

**External dependency:** `github.com` — behavior not under our control.
We specify what our code does with the response, not what the response will be.

**Authorization endpoint:** `https://github.com/login/oauth/authorize`
**Token endpoint:** `https://github.com/login/oauth/access_token`
**User info endpoint:** `https://api.github.com/user`

**Required scopes:** `read:user` (for login/id), `user:email` (for email)

**Representative user info payload shape** (for reference — not a guarantee):
```json
{
  "id": 12345678,
  "login": "okoliboma",
  "name": "Boma Okoli",
  "email": "boma@example.com",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345678"
}
```

**Field mapping:**

| GitHub field | Local field | If missing/null |
|---|---|---|
| `id` (integer) | `provider_user_id` (string) | Required — abort if absent |
| `login` (string) | `provider_login`, `username` | Use `f"github_{id}"` as username |
| `email` (string) | `provider_email` | Store `None` — do not crash |

**What we cannot specify:** GitHub's actual response shape, rate limits,
or behavior during outages. These are external dependencies.

### Clearbit Company API (Week 6 — unchanged)

See Week 6 CONTRACTS.md section 3.

---

## 4. Authorization Rules

### OAuth session state [Week 7]

After a successful `/auth/github/callback`:
- `login_user(user)` is called — Flask-Login sets `_user_id` in session
- `session.permanent = False` (no remember-me for OAuth in Week 7)
- Session cookie flags: `HttpOnly=True`, `SameSite=Lax`, `Secure=True` (prod)

### Logout behavior [Week 7]

- `logout_user()` clears Flask-Login session state
- `session.clear()` clears all session data locally
- **We do not clear the GitHub session** — the user remains logged into
  GitHub. This is standard OAuth behavior. Users who want to fully
  sign out of GitHub must do so at github.com.

### Ownership rules (Week 6 — unchanged)

| Action | Who | Non-authorized response |
|--------|-----|------------------------|
| View/edit/delete application | Owner only | 404 |
| View insight | Owner only | 404 |

**OWASP-style 404 rule:** Non-owners get 404, not 403.

---

## 5. Role Boundaries

| Role | Owns | Does not touch |
|------|------|----------------|
| Coordinator (Boma) | `CONTRACTS.md`, `coord_session.md`, `team_walkthrough.md`, `tests/e2e/test_full_lifecycle.py` | Route handlers, models |
| Server-side (Darrell) | `/login/github`, `/auth/github/callback` in `app.py`, `services/` | Templates, models |
| Client-side (Boma) | `templates/login.html` GitHub button, `tests/e2e/test_client_e2e.py` | `app.py`, `models.py` |
| DB-and-security (Aden) | `models.py` `OAuthIdentity`, cookie config, CSRF, `tests/e2e/test_db_security_flow.py` | Route handlers, templates |

---

## 6. Secrets Management [Week 7]

All secrets loaded via `python-dotenv` at app startup.
`.env` is gitignored — never committed.
`.env.example` is committed with placeholder values.

Required environment variables:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Signs session cookies — generate 32 random bytes |
| `DATABASE_URL` | Yes | Postgres connection string |
| `OAUTH_CLIENT_ID` | Yes | GitHub OAuth app client ID |
| `OAUTH_CLIENT_SECRET` | Yes | GitHub OAuth app client secret |
| `SESSION_COOKIE_SECURE` | No | Default `true` in prod, `false` in test |
| `PERMANENT_SESSION_LIFETIME_SECONDS` | No | Default 1209600 (14 days) |

Missing `SECRET_KEY`, `DATABASE_URL`, `OAUTH_CLIENT_ID`, or
`OAUTH_CLIENT_SECRET` → app crashes on startup (strict `os.environ[key]`).

---

## 7. Known Limitations (Deliberate)

| Limitation | Reason |
|---|---|
| Real GitHub redirect not tested | External dependency — use backdoor in tests, verify manually once |
| SQLite in Playwright fixture | Hermetic tests; Postgres-specific features need testcontainers |
| No Alembic migrations | Deferred — using `create_all` for classroom skeleton |
| No pagination on applications list | Deferred to Week 8 |
| OAuth `remember_me` not wired | Deferred to Week 8 |
| `SESSION_COOKIE_SECURE` not verified in e2e | Plain HTTP in test fixture — needs HTTPS to verify |
