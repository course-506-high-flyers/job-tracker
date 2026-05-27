# role_work_aden.md — Aden (DB-and-security)

**Role:** DB-and-security
**Week:** 7

## Files touched

- `app.py` — strict env loading for `SECRET_KEY` and `DATABASE_URL`, cookie
  hardening (`SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE`), remember-me lifetime
  (`PERMANENT_SESSION_LIFETIME`, `REMEMBER_COOKIE_DURATION`), Flask-WTF CSRF
  wiring (`CSRFProtect(app)`), and the test-login backdoor route
  (`/test/login/<username>` with `TESTING` guard).
- `models.py` — added `OAuthIdentity` table linking external provider IDs to
  local users (`UNIQUE(provider, provider_user_id)`, FK cascade
  `user_id → users.id`).
- `.env.example` — documented the required env vars with placeholder values
  (`SECRET_KEY`, `DATABASE_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, and
  optional cookie/session overrides).
- `templates/login.html` — CSRF hidden input, `Remember me` checkbox.
- `templates/register.html` — CSRF hidden input.
- `templates/applications/form.html` — CSRF hidden input, repaired cancel link.
- `templates/applications/detail.html` — CSRF hidden input on delete form.
- `requirements.txt` — added `Authlib`, `Flask-WTF`, `python-dotenv`,
  `playwright`, `pytest-playwright`.
- `tests/conftest.py` — seeds strict env vars before app import, disables CSRF
  for the unit-test client fixture.
- `tests/test_auth.py`, `tests/test_db_security_contract.py` — CSRF disabled in
  their fixtures so prior assertions continue to hold.
  `test_db_security_contract.py` also gained
  `test_oauth_identity_schema_matches_contract`, which asserts the Week 7 table
  I own (column set, `UNIQUE(provider, provider_user_id)`, and FK cascade
  `user_id → users.id`).
- `tests/test_csrf_protection.py` — NEW. Asserts CSRF rejects tokenless POSTs
  on every state-changing form (`/login`, `/register`, `/applications/new`,
  `/applications/<id>/edit`, `/applications/<id>/delete`) and that the
  test-login backdoor 404s when `TESTING` is false.
- `CONTRACTS.md § 1` — added an "Implementation references" table mapping
  every schema row in the contract to the symbol that implements it.
- `tests/e2e/conftest.py` — Playwright live-server fixture (SQLite,
  `TESTING=True`).
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
breaking `logout_user()` / session clearing, accidentally flipping
`SESSION_COOKIE_HTTPONLY` off, or weakening `SESSION_COOKIE_SAMESITE`.

## Schema / migration approach

The project still uses `SQLModel.metadata.create_all(engine)` at app import as
the schema bootstrap path. That decision was already made in Week 6 (see
`CONTRACTS.md` "Aden role-specific note"). For Week 7 I am committing the
`oauth_identity` schema change cleanly through that mechanism rather than
introducing Alembic mid-assignment. Migrating to Alembic remains my role's
documented future work; the contract calls this out explicitly.

## LLM conversation — how the work was scoped

I drove the role-specific work in a Cursor chat with Claude. The conversation
covered:

- **Schema design for `OAuthIdentity`** — I asked the LLM to compare a
  separate `oauth_identity` table versus columns on `users`. We landed on a
  separate table so one local user can hold multiple provider identities
  later. The `UNIQUE(provider, provider_user_id)` constraint and the
  `user_id → users.id ON DELETE CASCADE` foreign key both came out of that
  conversation; the LLM also recommended documenting these explicitly in the
  contract so the server-side role could plug in without schema churn.
- **Cookie hardening** — I asked the LLM which Flask config keys map to the
  cookie flags the assignment requires. It produced the
  `SESSION_COOKIE_SECURE / HTTPONLY / SAMESITE` block, the matching
  `REMEMBER_COOKIE_*` block, and the env-driven overrides
  (`_env_bool` helper) so the e2e fixture can run over plain HTTP without
  silently weakening production defaults.
- **CSRF wiring** — I asked the LLM the smallest correct way to add
  Flask-WTF CSRF protection without breaking existing unit tests.
  We agreed on `CSRFProtect(app)` globally + `csrf_token()` hidden inputs in
  every state-changing form + `WTF_CSRF_ENABLED=False` only inside the unit
  test client fixture. The new `tests/test_csrf_protection.py` came directly
  out of that conversation: I asked for tests that would actually fail if I
  ever removed `CSRFProtect`.
- **Test-login backdoor** — I asked the LLM to review the route I drafted
  against the assignment's safety story. It pushed back on a version that
  raised 403 instead of 404 (since 404 prevents enumeration), and that became
  the version in `app.py`. The companion test
  (`test_test_login_404s_when_not_testing`) was also LLM-suggested.
- **Strict env loading** — I asked the LLM to compare `os.environ[...]`
  versus `os.environ.get(...)`. It restated the assignment's argument
  ("missing secret should crash on startup, not surface as a confusing
  runtime error two minutes later") and I applied it to `SECRET_KEY` and
  `DATABASE_URL` in `app.py`. I also wrote the corresponding contract clause
  in `CONTRACTS.md § 6`.
- **Pre-submission audit** — In a final review pass the LLM cross-checked
  the repo against the full assignment rubric. It flagged that the
  server-side `oauth.register(...)` call still uses
  `os.environ.get(..., "")` for `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET`,
  which contradicts the strict-env clause in `CONTRACTS.md § 6` that I
  authored. That is a server-side fix (Darrell owns `oauth.register(...)`
  per `CONTRACTS.md § 5`), not mine to push, but the conversation surfaced
  it as the one remaining contract↔code drift before submission.

## Known gaps (honest disclosure — my slice only)

- **`OAuthIdentity` is defined and created in the schema but not yet wired
  into a route from my slice.** Implementing the create-or-link logic and
  `/login/github` + `/auth/github/callback` is the server-side role's
  deliverable. My contract contribution defines the table shape, unique
  constraints, and link semantics so that work can plug in without schema
  churn.
- **`SESSION_COOKIE_SECURE` is asserted only via configuration, not via the
  E2E cookie check.** The Playwright fixture serves over plain HTTP, so the
  browser never receives a `Secure`-flagged cookie. In production-like
  config (`SESSION_COOKIE_SECURE=true`) the flag is set; verifying that
  end-to-end would require HTTPS in the test fixture, which is out of scope
  this week.
- **Session-expiry behavior is configured (`PERMANENT_SESSION_LIFETIME`,
  `REMEMBER_COOKIE_DURATION`) but is not exercised by my individual test.**
  This is covered by the team's full-lifecycle Playwright suite (Part 3,
  scenario 4).
- **The real GitHub authorization UI is not driven by any automated test.**
  The test-login backdoor stands in for everything after the redirect lands
  at our callback. This is the same disclosure the assignment asks for.

## Submission

Final test coverage delivered via pull request rather than direct commits to
`main`, so the additions get a normal review trail:

- Branch: `aden/week7-db-security-test-hardening`
- PR: #8 — *test(db-security): assert oauth_identity schema and CSRF on
  application forms*
- Commits in the PR:
  - `4943762` — adds the two new test functions
    (`test_oauth_identity_schema_matches_contract`,
    `test_applications_{new,edit,delete}_post_without_csrf_token_is_rejected`)
  - `9d600cd` — `role_work.md` update describing the new coverage
- Full suite at submission time: **79 passed, 0 failed, 0 skipped**
  (65 unit/integration + 14 Playwright e2e, including all four Part 3
  full-lifecycle scenarios).
