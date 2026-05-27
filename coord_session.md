# Coordinator LLM Session Transcript — Week 7
**Project:** Job Application Tracker  
**Team:** High Flyers  
**Coordinator:** Boma Okoli  
**Date:** May 27, 2026  
**Tool used:** Claude (Anthropic)

---

## Purpose

This transcript documents the Week 7 planning session used to revise
CONTRACTS.md for OAuth, design the Playwright test suite, and surface
cross-role implications before implementation began.

---

## Session Summary

### Opening — OAuth scope and stack confirmation

**Boma:** We need to add GitHub OAuth to our Job Application Tracker.
Our stack is Flask, SQLModel, Postgres, Bootstrap, Flask-Login.
Aden already added the `oauth_identity` table and CSRF protection.
Darrell is implementing the OAuth routes. I'm doing client-side
(GitHub button on login page) and coordinator work.

**Claude:** Before writing the contract, three design decisions need
to be made upfront. First: when a user logs in with GitHub for the
first time, do you create a new local user or require them to link
to an existing password account?

**Boma:** Create a new local user automatically. We don't want to
force people to create a password account first.

**Claude:** Good. Second decision: what username do you assign the
new user if GitHub doesn't return a login field?

**Boma:** Fall back to `github_<provider_user_id>`. That way we
always have a unique username even if the payload is partial.

*[Decision recorded: username fallback = `f"github_{provider_user_id}"`]*

---

### OAuth callback failure modes

**Claude:** What does your app do if the GitHub callback returns an
error — for example, the user clicks "Deny" on the GitHub auth page?

**Boma:** Flash a warning and redirect back to the login page. Don't
crash.

**Claude:** And if the email field is missing — GitHub lets users
hide their email — do you require it?

**Boma:** No. Store None in `provider_email`. The app doesn't need
email to function.

**Claude:** That's the right call. Email as optional enrichment, not
a required field. I'd recommend noting this explicitly in the contract
so Darrell knows not to crash on a null email.

*[Decision recorded: `provider_email` nullable, null = store None]*

---

### Logout behavior — pushback on clearing GitHub session

**Claude:** For logout, should you also clear the GitHub session so
the user is fully signed out of GitHub?

**Boma:** Can we do that?

**Claude:** Not easily — and you shouldn't. Clearing the GitHub
session would log the user out of all GitHub tabs and apps, which
is not what they expect when they click "Log out" of your app.
Standard OAuth behavior is to clear your local session only. The
user stays logged into GitHub. This should be documented in the
contract so it's not treated as a bug.

**Boma:** Makes sense. Add it to the known limitations.

*[Decision recorded: logout clears local session only, not GitHub
session — documented in Authorization Rules section]*

---

### Playwright test design — backdoor rationale

**Boma:** The assignment says we need Playwright tests but we can't
actually drive the real GitHub login UI. How does the backdoor work?

**Claude:** The test-login backdoor is a Flask route — `/test/login/<username>`
— that's only available when `app.config["TESTING"]` is True. Your
Playwright test navigates to that URL instead of clicking the real
GitHub button. It bypasses the OAuth redirect entirely. The gap is
named explicitly: we don't test the real GitHub redirect, and we
document that in `team_walkthrough.md`.

**Boma:** So the GitHub button on the login page — how do we test
that it exists and points to the right route?

**Claude:** That's actually testable — Playwright can navigate to
`/login`, find the button by its text, and assert its `href` contains
`/login/github`. What it can't do is click that link and complete
the GitHub flow. Those are two different assertions.

*[Decision recorded: client-side test asserts button exists + href,
does not click through to GitHub]*

---

### Cross-role implications surfaced

**Boma:** Aden's `role_work.md` says `OAuthIdentity` is defined but
not yet wired into a route. Does that affect the Playwright tests?

**Claude:** Yes — the full-lifecycle test (Test 1) tries to assert
that an `oauth_identity` row was created after first login. But the
backdoor route creates a `User` row only, not an `OAuthIdentity` row.
If Darrell's OAuth callback isn't implemented yet, that DB assertion
will fail.

**Boma:** So the full-lifecycle test depends on Darrell's work?

**Claude:** Test 1 and Test 2 do, yes. Tests 3 and 4 (CSRF and
session lifecycle) are independent of the OAuth routes and should
pass as soon as Aden's CSRF work is merged. This is worth noting
in `team_walkthrough.md` so the grader understands the dependency.

*[Decision recorded: Tests 1 and 2 depend on Darrell's callback
implementation; Tests 3 and 4 are independent]*

---

### Secrets management

**Boma:** Do we need to create a GitHub OAuth app for this?

**Claude:** Yes — someone on the team needs to create a GitHub OAuth
app in the team's GitHub org. The callback URL should be
`http://<ec2-public-ip>:5000/auth/github/callback`. The client ID
and secret go in `.env` (gitignored) and `.env.example` documents
the variable names with placeholders. The coordinator typically
handles this setup.

**Boma:** What if we don't have the credentials yet when we submit?

**Claude:** Document it honestly in the contract and in
`team_walkthrough.md`. The grader expects you to note what's
pending. Missing credentials don't invalidate the contract or
the tests — they just mean the real OAuth flow can't be manually
verified yet.

*[Decision recorded: GitHub OAuth app setup documented as pending
in known limitations if not completed before submission]*

---

## Key Decisions Summary

| Decision | Rationale |
|---|---|
| Auto-create user on first OAuth login | No forced account linking — simpler UX |
| Username fallback = `github_<id>` | Always unique even with partial payload |
| `provider_email` nullable | GitHub allows private email — don't crash |
| Logout clears local session only | Standard OAuth behavior — not a bug |
| Playwright uses backdoor, not real GitHub | External dependency — named gap |
| Client-side test asserts button + href only | Can't drive real GitHub UI |
| Tests 1+2 depend on Darrell's callback | Cross-role dependency surfaced early |

---

## What this session surfaced that I didn't know going in

- The logout behavior — I assumed we should clear the GitHub session
  too, but that would log the user out of all GitHub tabs. Standard
  OAuth only clears local state.
- The cross-role dependency between the full-lifecycle Playwright test
  and Darrell's OAuth callback implementation. Tests 1 and 2 can't
  pass until the callback route exists.
- The difference between testing that the GitHub button exists (easy,
  Playwright can do it) vs testing the actual OAuth flow (impossible
  without real credentials and GitHub's UI).
