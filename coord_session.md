# Coordinator LLM Session Notes (Week 7 OAuth Revision)
**Project:** Job Application Tracker  
**Team:** High Flyers  
**Coordinator:** Boma Okoli  
**Date:** May 26, 2026  
**LLM Used:** Claude

---

## Purpose

Revise `CONTRACTS.md` for Week 7 OAuth integration and agree on how contract
items map to implementation and tests across roles.

---

## Session Summary (Honest Transcript-Style)

**Boma (Coordinator):** We need to revise the contract for GitHub OAuth and
be explicit about what we can and cannot promise. Which parts are ours and
which parts are external?

**Claude:** You can contract your app's route behavior and local data handling,
but not GitHub's runtime behavior. Add `external_dependency: github.com` and
state that provider payload examples are representative only.

**Decision:** Added explicit dependency boundary section to contract.

---

**Aden (DB/Security):** For the callback, what provider fields are mandatory?
I need deterministic rules so we can test partial payloads and avoid crashes.

**Claude:** Require provider `id`; treat `login`, `email`, and `name` as
optional. Missing `id` means fail login. Missing optional fields should use
fallback defaults or null storage, never 500.

**Decision:** Contract now defines required vs optional provider fields and
fallback behavior.

---

**Darrell (Server-side):** We need a clear create-or-link algorithm. Otherwise
we may create duplicate local users or duplicate identity rows.

**Claude:** Decision tree should be:
1) if (`provider`, `provider_user_id`) exists, reuse linked local user;
2) if authenticated local user is linking account, attach new identity row;
3) else create local user and identity row.
Also require unique(`provider`, `provider_user_id`).

**Decision:** Added identity schema shape and unique constraints to contract.

---

**Aden (DB/Security):** Session contract has to be concrete for hardening.
What exactly should exist after callback?

**Claude:** State local login/session keys exist, transient OAuth keys are
removed, cookie flags are set (`HttpOnly`, `SameSite=Lax`, `Secure` in
production-like config), and lifetime is controlled by permanent session
settings/remember cookie.

**Decision:** Added post-callback session/cookie contract section.

---

**Boma (Coordinator):** For logout, should we also log users out of GitHub?

**Claude:** No provider logout is required for this assignment. Contract should
say local logout clears app session only; provider session remains outside app
control.

**Decision:** Added explicit local-vs-provider logout behavior.

---

**Cross-role test implications discussion**

**Boma:** How do we avoid truthy-fixture tests here?

**Claude:** Use Playwright for browser behavior and a test-login backdoor for
post-redirect authentication state. Document gap honestly: real hosted GitHub
authorization UI is not covered by automated tests in this assignment setup.

**Aden:** For my role test, I will verify protected page access is blocked when
logged out, allowed after test login, and blocked again after logout using DOM
assertions.

**Darrell:** I will cover callback error handling and identity reuse in server
tests.

**Decision:** Contract includes explicit test obligations and gap disclosure.

---

## Why this reflects real coordination (not just a to-do split)

- We resolved behavior ambiguities (`id` required vs optional fields fallback).
- We settled data ownership and duplication risks (identity linking rules).
- We aligned security config with route/session behavior to avoid role conflicts.
- We agreed on what automated tests can honestly claim and what must be a
  documented gap.
