# Darrell Allen - Week 7 Server-Side OAuth Work

## Completed Tasks
- Added GitHub OAuth authentication using Authlib
- Added secure environment variable loading with python-dotenv
- Updated session security configuration
- Added GitHub OAuth login route (/login/github)
- Added GitHub OAuth callback route (/auth/github/callback)
- Added OAuthIdentity SQLModel table for provider identity mapping
- Added GitHub login button to login template
- Added test login helper route for Playwright E2E testing
- Added Playwright end-to-end test for OAuth login workflow
- Updated pytest fixtures to support live server browser testing
- Updated requirements.txt with OAuth and Playwright dependencies
- Updated .env.example with required OAuth environment variables

## Test Results
- OAuth Playwright E2E test: PASSED
- Full regression suite: 59/59 PASSED

## Files Modified
- app.py
- models.py
- templates/login.html
- tests/conftest.py
- tests/e2e/test_server_oauth_login.py
- requirements.txt
- .env.example

---

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
  every schema row in the contract to the symbol that implements it.
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
  - `9d600cd` — this `role_work.md` update describing the new coverage
- Full suite at submission time: **79 passed, 0 failed, 0 skipped**
  (65 unit/integration + 14 Playwright e2e, including all four Part 3
  full-lifecycle scenarios).

---

# role_work.md — Boma Okoli (Client-side + Coordinator)

## Role: Client-side

## Files touched

- `templates/login.html` — added "Sign in with GitHub" button above the
  password form; kept password form and Remember me checkbox intact alongside
  it. GitHub button links to `/login/github`. Added divider between OAuth
  and password sections.
- `tests/e2e/test_client_e2e.py` — NEW. Nine Playwright tests covering
  the client-side OAuth login flow and post-login UI state.

## What my Playwright test verifies

I adapted the Week 6 client-side e2e walkthrough by inserting the test-login
backdoor at the top. The test suite covers nine user-visible behaviors:

1. The Sign in with GitHub button is visible on the login page
2. The password form coexists with the GitHub button (both methods present)
3. The Remember me checkbox is present and unchecked by default
4. The GitHub button href points to `/login/github`
5. Anonymous users are redirected from `/applications` to `/login`
6. After backdoor login, the navbar shows the username and My Applications link
7. After login, the user can navigate to `/applications` successfully
8. After logout, the navbar reverts to anonymous state
9. GitHub button renders above the password form

## Known gaps (honest disclosure)

- The real GitHub redirect is not driven by any automated test.
- The GitHub button is not clickable end-to-end — requires live credentials.
- Remember me session lifetime not tested in individual test.

---

## Role: Coordinator (covering for Olga who left in Week 6)

## Coordinator files produced

- `CONTRACTS.md` — updated with OAuth flow sections
- `coord_session.md` — updated with Week 7 planning transcript
- `tests/e2e/test_full_lifecycle.py` — team full-lifecycle Playwright suite
- `team_walkthrough.md` — explains what the suite verifies and its gaps

## What the coordinator Playwright test verifies

`tests/e2e/test_full_lifecycle.py` covers four scenarios:
1. First-time OAuth login via backdoor — user row created
2. Returning OAuth login — existing row reused, not duplicated
3. CSRF protection — tokenless POST rejected with 400
4. Session lifecycle — protected page inaccessible after logout
