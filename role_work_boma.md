# role_work_boma.md — Boma Okoli (Client-side + Coordinator)

## Role: Client-side

## Files touched

- `templates/login.html` — added "Sign in with GitHub" button above the
  password form; kept password form and Remember me checkbox intact alongside
  it. GitHub button links to `/login/github` (server-side route owned by
  Darrell). Added divider between OAuth and password sections.
- `tests/e2e/test_client_e2e.py` — NEW. Eight Playwright tests covering
  the client-side OAuth login flow and post-login UI state.

## What my Playwright test verifies

I adapted the Week 6 client-side e2e walkthrough by inserting the test-login
backdoor at the top. The test suite covers eight user-visible behaviors:

1. The Sign in with GitHub button is visible on the login page
2. The password form coexists with the GitHub button (both methods present)
3. The Remember me checkbox is present and unchecked by default
4. The GitHub button href points to `/login/github`
5. Anonymous users are redirected from `/applications` to `/login`
6. After backdoor login, the navbar shows the username and My Applications link
7. After login, the user can navigate to `/applications` successfully
8. After logout, the navbar reverts to anonymous state

The tests exercise the rendered DOM through a real browser (Playwright
Chromium), not BeautifulSoup. This catches regressions that BeautifulSoup
cannot — visual ordering of elements, nav state transitions, and click
interactions.

The Week 6 walkthrough adapted: `e2e/client_side.md` steps 2-5 and 9-12.
The OAuth login step (backdoor) replaces the manual registration step at
the top of the walk.

## Known gaps (honest disclosure)

- **The real GitHub redirect is not driven by any automated test.** The
  test-login backdoor stands in for everything after the OAuth redirect
  lands at our callback. This is the named gap for the whole team.
- **The "Sign in with GitHub" link is not clickable end-to-end in tests**
  because `/login/github` initiates the real GitHub OAuth flow which
  requires live credentials and a real browser session with GitHub.
  The test verifies the button exists and has the correct href; the
  actual redirect is verified manually.
- **Remember me session lifetime is not tested in my individual test.**
  This is covered in the team's full-lifecycle Playwright suite (Part 3).

---

## Role: Coordinator (covering for Olga who left in Week 6)

## Coordinator files produced

- `CONTRACTS.md` — updated with OAuth flow sections (routes, user record
  shape, oauth_identity link, session state, logout behavior)
- `coord_session.md` — updated with Week 7 planning transcript
- `tests/e2e/test_full_lifecycle.py` — team full-lifecycle Playwright suite
- `team_walkthrough.md` — explains what the suite verifies and its gaps

## What the coordinator Playwright test verifies

`tests/e2e/test_full_lifecycle.py` covers four scenarios as required:
1. First-time OAuth login via backdoor — user row and oauth_identity row created
2. Returning OAuth login — existing row reused, not duplicated
3. CSRF protection — tokenless POST rejected
4. Session lifecycle — protected page inaccessible after logout

## Known gaps

- Same GitHub redirect gap as client-side — backdoor stands in for real OAuth
- SQLite used in test fixture instead of Postgres — documented in
  team_walkthrough.md gaps section
