# role_work_boma.md — Boma Okoli (Client-side + Coordinator)

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

- `CONTRACTS.md` — updated with OAuth flow sections (routes, user record
  shape, oauth_identity link, session state, logout behavior)
- `coord_session.md` — updated with Week 7 planning transcript and
  post-submission integration log
- `tests/e2e/test_full_lifecycle.py` — team full-lifecycle Playwright suite
- `team_walkthrough.md` — explains what the suite verifies and its gaps

## What the coordinator Playwright test verifies

`tests/e2e/test_full_lifecycle.py` covers four required scenarios:
1. First-time OAuth login via backdoor — user row created
2. Returning OAuth login — existing row reused, not duplicated
3. CSRF protection — tokenless POST rejected with 400
4. Session lifecycle — protected page inaccessible after logout

## Integration log

Caught and resolved during final audit: `app.py` originally used
`os.environ.get()` for OAuth credentials instead of strict `os.environ[]`.
Surfaced to Darrell and Aden for fix before final tag. See `coord_session.md`
post-submission log for full details.

## Known gaps

- Real GitHub redirect not tested — backdoor stands in for full OAuth flow
- SQLite used in Playwright fixture instead of Postgres — documented in
  `team_walkthrough.md`
- `SESSION_COOKIE_SECURE` not verified end-to-end — plain HTTP in test fixture
