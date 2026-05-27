# Job Application Tracker — Team Walkthrough (Week 7)

**Team:** High Flyers  
**Coordinator:** Boma Okoli  
**Week:** 7  

---

## Overview

This document explains what the Week 7 Playwright suite verifies, what
regressions each test would catch, and what the suite deliberately does
not cover. A new teammate should be able to understand the team's e2e
coverage in ten minutes by reading this document.

The suite lives in `tests/e2e/test_full_lifecycle.py`. It exercises the
full OAuth login lifecycle as one user would experience it — from first
visit through login, application use, and logout — using a real Chromium
browser driven by Playwright. The test-login backdoor stands in for the
real GitHub redirect; this gap is named explicitly in the gaps section.

---

## Test 1 — First-time OAuth login

**File:** `tests/e2e/test_full_lifecycle.py::test_first_time_oauth_login`

**User-visible behavior exercised:**
A user with no existing local account visits the login page, clicks
"Sign in with GitHub", completes login via the test-login backdoor,
and arrives at the applications list page with their username visible
in the navbar. A new row exists in both the `users` table and the
`oauth_identity` table.

**What regression this catches:**
If someone broke the create-or-link branch by always crashing on a
new user (missing INSERT for the User row, or missing INSERT for the
OAuthIdentity row), this test would fail because the backdoor would
either 500 or the navbar would not show the username. If the
`oauth_identity` table was dropped or the FK constraint was wrong,
the DB assertion at the end would fail.

---

## Test 2 — Returning OAuth login

**File:** `tests/e2e/test_full_lifecycle.py::test_returning_oauth_login`

**User-visible behavior exercised:**
The same user from Test 1, now logged out, logs in again via the
backdoor. They arrive at the applications list page. The `oauth_identity`
table still has exactly one row for this user — no duplicate was created.

**What regression this catches:**
If someone broke the create-or-link branch by always inserting a new
row instead of finding the existing one, this test would fail because
the second login would find a duplicate `oauth_identity` row and the
count assertion would return 2 instead of 1. This is the canonical
regression the assignment asks us to verify.

---

## Test 3 — CSRF protection

**File:** `tests/e2e/test_full_lifecycle.py::test_csrf_protection`

**User-visible behavior exercised:**
A logged-in user's POST to a state-changing endpoint (`/logout`) without
a CSRF token is rejected with a 400 response. The same POST with a valid
CSRF token succeeds.

**What regression this catches:**
If someone accidentally disabled Flask-WTF CSRF protection (e.g. set
`WTF_CSRF_ENABLED=False` globally, or removed `csrf = CSRFProtect(app)`),
a tokenless POST would succeed instead of being rejected. This test
catches that regression. It uses Playwright's request context to send
a raw POST without going through the browser form, which is the only
way to send a tokenless request reliably.

---

## Test 4 — Session lifecycle

**File:** `tests/e2e/test_full_lifecycle.py::test_session_lifecycle`

**User-visible behavior exercised:**
A user logs in, accesses `/applications` successfully, then logs out.
After logout, navigating to `/applications` redirects to `/login`.
The protected page is inaccessible again — the session was fully cleared.

**What regression this catches:**
If `logout_user()` or `session.clear()` was removed or broken, the
user would remain authenticated after clicking Log out. The protected
page would still be accessible, and this test would fail because it
expects a redirect to `/login` after logout. This also catches regressions
in `@login_required` being removed from `applications_list`.

---

## Gaps — What the suite does not cover

**The real GitHub authorization redirect.**
The test-login backdoor (`/test/login/<username>`) stands in for
everything after `authorize_redirect()` hands off to GitHub and the
user authorizes there. We don't drive the actual GitHub UI because
it requires live OAuth credentials, a real GitHub account, and
network access to github.com — none of which are appropriate for
an automated test suite. The backdoor is an explicit, named mock.
Verify the real redirect manually once when wiring up Authlib.

**SQLite vs Postgres behavioral differences.**
The Playwright fixture uses SQLite (via `tests/e2e/conftest.py`) for
hermetic, container-free test runs. SQLite and Postgres differ in some
constraint semantics (e.g. certain FK behaviors, JSON operations). For
this app's operations the behavior is identical, but any Postgres-specific
feature would need a separate integration test against real Postgres.
`testcontainers` is the standard tool for that — out of scope this week.

**SESSION_COOKIE_SECURE flag verification.**
The Playwright fixture serves over plain HTTP, so the browser never
receives a Secure-flagged cookie. The flag is set in config
(`SESSION_COOKIE_SECURE=true` in production) but cannot be verified
end-to-end without HTTPS in the test fixture.

**Remember me session expiry under real time.**
The session lifetime is configured (`PERMANENT_SESSION_LIFETIME`,
`REMEMBER_COOKIE_DURATION`) and the config is asserted in unit tests,
but we do not actually wait for the lifetime to expire in any automated
test. Verifying this end-to-end would require either a very short
test-only lifetime (seconds) and a `time.sleep()`, or Playwright's
clock controls — deferred to a future week.

**The actual GitHub user-info payload shape.**
We cannot specify or test GitHub's actual response — it lives on a
server we don't control. Our contract specifies what our code does
with the response (field mapping, null handling, create-or-link logic),
not what the response will be. The representative payload shape is
documented in CONTRACTS.md section 3 for reference only.

---

## How to run the suite

```bash
# Install Playwright browsers (first time only)
docker compose exec app playwright install chromium

# Run the full lifecycle suite
docker compose exec app pytest tests/e2e/test_full_lifecycle.py -v

# Run all e2e tests
docker compose exec app pytest tests/e2e/ -v
```
