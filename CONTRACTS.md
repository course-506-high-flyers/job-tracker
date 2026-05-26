# Job Application Tracker — CONTRACTS.md

**Team:** High Flyers  
**Coordinator:** Boma Okoli  
**Project:** Job Application Tracker  
**Week:** 7 (OAuth + Playwright revision)

This document is the authoritative spec for Week 7 behavior. Implementation
and tests must match this contract.

---

## 1. OAuth Dependency Boundary

- `external_dependency: github.com`
- This contract specifies what **our code** does with provider responses.
- This contract does **not** specify GitHub's exact behavior or payload
  guarantees.
- Representative payload shape may be used in tests/docs, but tests must not
  claim GitHub is contractually required to return that exact shape.

---

## 2. OAuth Routes Contract

### 2.1 `GET /login/github`

- **Auth requirement:** anonymous or authenticated users may hit route.
- **Input:** query string optional `next` (string path, default `/`).
- **Behavior:**
  - stores OAuth state token and post-login redirect target in session
  - initiates provider authorization redirect
- **Output on success:** HTTP 302 redirect to provider authorization URL.
- **Output on failure:** flash auth error and redirect to `/login`.

### 2.2 `GET /auth/github/callback`

- **Auth requirement:** none (provider redirects here).
- **Input:** provider callback query params (`code`, `state`, possible `error`).
- **Precondition:** `state` must match server-side session state.
- **Behavior:**
  - exchanges `code` for token
  - requests provider user info
  - validates required fields (see Section 3)
  - executes create-or-link logic (see Section 4)
  - logs local user in
- **Output on success:** HTTP 302 redirect to stored `next` or `/dashboard`.
- **Output on failure:** clear transient OAuth session keys, flash error,
  redirect to `/login`.

---

## 3. Provider User Info Requirements

Fields our app tries to read from provider user info:

- `id` (required): external provider user ID, normalized to string.
- `login` (optional): preferred username/display handle.
- `email` (optional): email from provider profile.
- `name` (optional): full display name.

Missing-field handling:

- If `id` missing/null: abort callback flow, no login, redirect `/login` with
  flash error.
- If `login` missing/null: fallback username seed is `github_<id>`.
- If `email` missing/null: store `NULL` email; do not crash.
- If `name` missing/null: fallback display name to `login` or `github_<id>`.

---

## 4. Local Identity Model and Linking Contract

### 4.1 Local user record shape after first-time OAuth login

`users` row includes:

- `id: int` (PK)
- `username: str` (non-empty; generated from `login` or fallback)
- `password_hash: str` (for OAuth-created users, a non-login placeholder hash is
  allowed)
- `created_at: datetime`

### 4.2 External identity link shape

`oauth_identity` row includes:

- `id: int` (PK)
- `user_id: int` (FK -> `users.id`)
- `provider: str` (e.g., `"github"`)
- `provider_user_id: str` (normalized external `id`)
- `provider_login: str | null`
- `provider_email: str | null`
- `created_at: datetime`
- `updated_at: datetime`

Constraints:

- unique(`provider`, `provider_user_id`) to prevent duplicate external identity rows
- one local user may have multiple identity rows (one per provider or account link)

### 4.3 Create-or-link decision rules

- If (`provider`, `provider_user_id`) exists:
  - load linked local user and log in (returning OAuth user path).
- Else if existing local user is authenticated and chooses add-provider flow:
  - create identity row linked to current local user (link path).
- Else:
  - create local user, then create identity row (first-time OAuth user path).

---

## 5. Session and Cookie Contract After Successful OAuth Callback

Session dictionary and login state:

- `session["user_id"]`: local integer user ID (Flask-Login session key behavior)
- OAuth transient keys (`oauth_state`, temporary redirect target) are removed
  after callback handling.
- `session.permanent`: set from remember-me decision.

Cookie expectations:

- session cookie exists after login
- `SESSION_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SAMESITE = "Lax"`
- `SESSION_COOKIE_SECURE = True` in production-like config
- lifetime controlled by `PERMANENT_SESSION_LIFETIME`
- remember-me uses Flask-Login remember cookie with configured duration

---

## 6. Logout Contract

Route: `GET|POST /logout` (existing route retained)

Local clear behavior:

- `logout_user()` called
- local session keys removed (`user_id` and transient auth keys)
- session cookie invalidated/rotated per Flask session behavior

Provider behavior:

- app does **not** log the user out of GitHub
- no provider-side revoke/logout call is made by default

---

## 7. Security Contract

- CSRF protection is enabled on all state-changing form submissions.
- Protected routes redirect anonymous users to `/login?next=<path>`.
- Ownership-restricted resources continue returning 404 for non-owners.
- Test-only login backdoor route exists only when `app.config["TESTING"]` is
  true; returns 404 otherwise.

---

## 8. Test Obligations Derived From This Contract

Required contract-enforcement tests:

- Unit/integration:
  - callback fails when provider `id` missing
  - callback with partial payload (`email` missing) still succeeds without crash
  - returning OAuth login reuses existing `oauth_identity` row
  - logout clears local session state
- Playwright (browser E2E):
  - logged-out user cannot access protected page
  - login via test backdoor reaches authenticated UI state
  - logout returns user to unauthenticated behavior

Gap disclosure required in walkthrough/docs:

- tests do not drive the real GitHub hosted authorization UI end-to-end
- tests intentionally mock/stand in for post-redirect flow via test-login path
