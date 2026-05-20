# Coordinator LLM Session Transcript
**Project:** Job Application Tracker  
**Team:** High Flyers  
**Coordinator:** Boma Okoli  
**Date:** May 20, 2026  
**Tool used:** Claude (Anthropic)

---

## Purpose

This transcript documents the LLM session used to produce CONTRACTS.md and
the four test files for Week 6. The session was used to surface design
decisions, clarify role boundaries, and identify gaps before implementation
began.

---

## Session Summary

### Opening — Project scope and stack confirmation

**Boma:** I need to produce CONTRACTS.md and four failing test files for our
Job Application Tracker. Our stack is Flask, SQLModel, Postgres, Bootstrap.
Our external API is Clearbit for company data enrichment.

**Claude:** Before writing the contract, I need to understand your data model.
What are the core entities? What does a job application record contain?

**Boma:** Company name, position, status (applied/interviewing/offered/
rejected/withdrawn), date applied, notes, job URL. Each application belongs
to a user.

**Claude:** That gives us a clear ownership model. One design decision to make
upfront: when a non-owner tries to access another user's application via
direct URL, should they get 403 (forbidden) or 404 (not found)?

**Boma:** What's the difference in practice?

**Claude:** 403 confirms the resource exists but the user can't access it —
that leaks information about which IDs are valid. 404 is the OWASP-recommended
approach for ownership-restricted resources: it prevents enumeration attacks.
A malicious user can't tell whether ID 42 exists or just isn't theirs.

**Boma:** Use 404 then. That makes sense for a multi-user app.

*[Decision recorded: OWASP-style 404 for non-owner access — added to
Authorization Rules section of CONTRACTS.md]*

---

### Schema design

**Claude:** Do you want a separate table for company insights, or store them
inline on the application record?

**Boma:** Separate table — multiple applications could be at the same company,
so we should cache the insight once per company, not per application.

**Claude:** Good call. That means `job_insights` has `company` as a unique
key and a `fetched_at` timestamp for cache invalidation. How long should
the cache be valid?

**Boma:** 24 hours seems reasonable for company data.

*[Decision recorded: `job_insights` table with 24-hour cache — added to
Schema section]*

---

### Endpoint design — pushback on insight route

**Claude:** For the insight refresh, I'd suggest `GET /applications/<id>/insight`
that triggers a fetch and redirects back to the detail page. This keeps it
simple — no separate JSON API needed.

**Boma:** Why GET and not POST? We're modifying data.

**Claude:** That's a fair pushback. Strictly speaking, a state-changing
operation should be POST. However, for a cache refresh triggered by a user
clicking a link, GET is pragmatic — links can't POST without JavaScript.
If you want to be REST-correct, use POST and add a small form with a button.

**Boma:** Let's keep it as GET for now and note it as a known limitation.

*[Decision recorded: GET for insight refresh, noted as REST deviation in
Known Limitations]*

---

### External API failure modes

**Boma:** What failure modes do we need to handle for the Clearbit API?

**Claude:** At minimum: timeout, HTTP error (4xx/5xx), malformed JSON, and
rate limiting (429). The key question is what the user sees in each case —
do you flash a warning, silently fail, or show a degraded state?

**Boma:** Flash a warning and show the detail page without insight data.
Don't crash the page.

**Claude:** That's the right call — the insight is enrichment, not core
functionality. The app should work fine without it.

*[Decision recorded: All API failures return None, flash warning to user,
no 500 errors — added to External API Contract section]*

---

### Role boundaries — clarification needed

**Boma:** I'm covering both coordinator and client-side roles because our
coordinator left the team. How do I handle role boundaries when I'm
doing both?

**Claude:** Document it honestly in CONTRACTS.md — note that coordinator
duties were absorbed by the client-side role due to team change. The
boundaries still apply: your client-side work stays in templates/, your
coordinator work is CONTRACTS.md and test files. Keep them in separate
commits so the grader can see the distinction.

*[Decision recorded: Role boundaries table updated to reflect Boma covering
both coordinator and client-side]*

---

### Test file design — pushback on test scope

**Claude:** For the client-side tests, I'll assert on HTML structure and
CSS selectors — form field names, element IDs, nav links. Not on text
content, so you can freely change labels and copy.

**Boma:** Why not test text content? Wouldn't that catch more bugs?

**Claude:** Text content tests are brittle — they break every time someone
changes "Add Application" to "New Application". The contract cares about
structure: does the form have a `name="company"` input? Does the status
dropdown have all five enum values? Those are structural guarantees that
don't change with copy edits.

*[Decision recorded: Client-side tests assert on selectors and field names
only, not text content]*

---

### Integration test scope

**Boma:** What should the integration test cover?

**Claude:** The integration test should exercise the full flow: register →
login → create application → view list → view detail → edit → delete. It
should only pass when all three roles have shipped — server-side routes,
db models, and client-side templates all need to be in place.

**Boma:** What about the external API in the integration test?

**Claude:** Mock it. The integration test verifies that the pieces connect,
not that the external service is up. The e2e walk (not pytest) is where you
hit the real API.

*[Decision recorded: Integration test mocks external API, exercises full
CRUD flow]*

---

## Key Decisions Summary

| Decision | Rationale |
|---|---|
| 404 for non-owner access | OWASP enumeration prevention |
| Separate `job_insights` table | Cache per company, not per application |
| 24-hour insight cache | Reasonable freshness for company data |
| GET for insight refresh | Pragmatic — links can't POST without JS |
| Flash warning on API failure | Insight is enrichment, not core feature |
| Tests assert on structure not text | Avoids brittle copy-dependent tests |
| Integration test mocks external API | Pytest verifies connections, e2e verifies real service |

---

## What this session surfaced that I didn't know going in

- The OWASP 404-vs-403 distinction for ownership-restricted resources
- Separating the insight cache into its own table rather than denormalizing
- The difference between pytest integration tests (mock API) and e2e walks
  (real API) — these test different things and both are needed
- Why text-content assertions in client-side tests are an antipattern
