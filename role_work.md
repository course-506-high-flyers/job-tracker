# role_work.md — Aden (DB-and-security)

## Files touched

- `app.py` — strict env loading, cookie hardening, remember-me lifetime,
  Flask-WTF CSRF wiring, test-login backdoor.
- `models.py` — added `OAuthIdentity` table linking external provider IDs to
  local users.
- `.env.example` — uncommented, OAuth + cookie keys documented.
- `templates/login.html` — CSRF hidden input, `Remember me` checkbox.
- `templates/register.html` — CSRF hidden input.
- `templates/applications/form.html` — CSRF hidden input, repaired cancel link.
- `templates/applications/detail.html` — CSRF hidden input on delete form.
- `requirements.txt` — added `Authlib`, `Flask-WTF`, `python-dotenv`,
  `playwright`, `pytest-playwright`.
- `tests/conftest.py` — seeds strict env vars before app import, disables CSRF
  for unit-test client fixture.
- `tests/test_auth.py`, `tests/test_db_security_contract.py` — CSRF disabled in
  their fixtures so prior assertions continue to hold. `test_db_security_contract.py`
  also gained `test_oauth_identity_schema_matches_contract`, which asserts the
  Week 7 table I own (column set, `UNIQUE(provider, provider_user_id)`, and
  FK cascade `user_id → users.id`).
- `tests/test_csrf_protection.py` — NEW. Asserts CSRF rejects tokenless POSTs
  on every state-changing form (`/login`, `/register`, `/applications/new`,
  `/applications/<id>/edit`, `/applications/<id>/delete`) and that the
  test-login backdoor 404s when `TESTING` is false.
- `CONTRACTS.md § 1` — added an "Implementation references" table mapping
  every schema row in the contract to the symbol that implements it
  (`models.py` model classes, `app.py` `create_all`, schema-conformance test,
  Alembic deferral). Keeps the contract and the code in lockstep.
- `tests/e2e/conftest.py` — Playwright live-server fixture (SQLite, TESTING=True).
- `tests/e2e/test_db_security_flow.py` — required individual Playwright test.

## What my Playwright test verifies

I adapted the Week 6 protected-route walkthrough by inserting the Week 7
test-login backdoor at the top. The test verifies the full DB-and-security
access lifecycle through a real browser DOM: a logged-out user is redirected
from `/applications` to `/login`, the same user becomes authenticated via
`/test/login/aden` and sees `Hello, aden` plus the `My Applications` heading,
and after clicking `Log out` the protected page is blocked again. It also
inspects the live session cookie and asserts `HttpOnly` and `SameSite=Lax`,
which catches regressions in the cookie-flag config that no BeautifulSoup
test could see. Regressions this test would catch: removing `@login_required`,
breaking `logout_user()`/session clearing, accidentally flipping
`SESSION_COOKIE_HTTPONLY` off, or weakening `SESSION_COOKIE_SAMESITE`.

## Schema / migration approach

The project still uses `SQLModel.metadata.create_all(engine)` at app import as
the schema bootstrap path. That decision was already made in Week 6 (see
CONTRACTS.md "Aden role-specific note"). For Week 7 I am committing the
`oauth_identity` schema change cleanly through that mechanism rather than
introducing Alembic mid-assignment. Migrating to Alembic remains my role's
documented future work; the contract calls this out explicitly.

## Known gaps (honest disclosure)

- **`OAuthIdentity` is defined and created in the schema but not yet wired
  into a route.** Implementing the create-or-link logic and `/login/github`
  + `/auth/github/callback` is the server-side role's slice. My contract
  contribution defines the table shape, unique constraints, and link
  semantics so that work can plug in without schema churn.
- **`SESSION_COOKIE_SECURE` is asserted only via configuration, not via the
  E2E cookie check.** The Playwright fixture serves over plain HTTP, so the
  browser never receives a `Secure`-flagged cookie. In production-like config
  (`SESSION_COOKIE_SECURE=true`) the flag is set; verifying that end-to-end
  would require HTTPS in the test fixture, which is out of scope this week.
- **Session-expiry behavior is configured (`PERMANENT_SESSION_LIFETIME`,
  `REMEMBER_COOKIE_DURATION`) but is not exercised by my individual test.**
  This is covered by the team's full-lifecycle Playwright suite (Part 3,
  scenario 4).
- **The real GitHub authorization UI is not driven by any automated test.**
  The test-login backdoor stands in for everything after the redirect lands
  at our callback. This is the same disclosure the assignment asks for.
