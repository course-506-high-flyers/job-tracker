# Job Application Tracker — End-to-End Walk

**Team:** High Flyers  
**Coordinator:** Boma Okoli  

---

## 1. Definition

End-to-end for the Job Application Tracker means a real browser interacts
with the full system stack: browser ↔ Flask (routes and templates) ↔
Postgres (schema, constraints, ownership rules) ↔ Clearbit external API
(company data enrichment). A complete walk must exercise user registration,
login, full application CRUD (create, read, update, delete), the external
API integration, ownership isolation between users, and the session
lifecycle (login, logout, re-login). The walk is run against the deployed
app on EC2 with Docker Compose, not against pytest fixtures — pytest
verifies structure, this walk verifies that real users can actually use
the system end-to-end.

---

## 2. The Walk

### Setup

**Step 1.** Fresh environment:
```bash
docker compose down -v && docker compose up -d
```
Wait 15 seconds. Verify:
```bash
docker compose ps
```
Both `job-tracker-app-1` and `job-tracker-db-1` show `Up`.
Run pytest to verify baseline:
```bash
docker compose exec app pytest tests/ -v 2>&1 | tail -20
```

---

### Anonymous user flow

**Step 2.** Open `http://<ec2-public-ip>:5000` in browser, not logged in.
Verify navbar shows Login and Register. Verify no "My Applications" link.
Open browser dev tools — no console errors.

**Step 3.** Navigate directly to `http://<ec2-public-ip>:5000/applications`.
Verify 302 redirect to `/login` (check Network tab). Verify no 500 error.

---

### Registration

**Step 4.** Click Register. Fill in:
- Username: `e2e_user`
- Email: `e2e_user@example.com`
- Password: `E2ePass123`

Submit. Verify redirect to home. Verify navbar shows "My Applications"
and "Log out". Verify Login/Register links gone.

---

### Create applications

**Step 5.** Click "My Applications". Verify empty state renders — no
applications yet, add button visible.

**Step 6.** Click "+ New Application". Verify form has all fields.
Submit with:
- Company: `Google`
- Position: `Software Engineer L4`
- Status: `Applied`
- Date: `2026-05-10`
- Notes: `Applied via referral`
- URL: `https://careers.google.com/jobs/1`

Verify redirect to detail page. Verify flash "Application saved."

**Step 7.** Add a second application:
- Company: `Amazon`
- Position: `SDE II`
- Status: `Interviewing`
- Date: `2026-05-12`

Verify both applications appear on list page.

---

### External API integration

**Step 8.** On the Google application detail page, click "Fetch company
data" or "Refresh" in the insight card. Watch Network tab. Verify:
- A real HTTP request goes out to the Clearbit API
- If API returns data: insight card populates with company info
- If API rate-limited or unavailable: flash warning appears, page
  does not crash, detail page still renders correctly

This is the truthy-fixtures check — real API behavior, not mocked.

---

### Edit and status update

**Step 9.** On the Google application, click Edit. Verify all fields
pre-filled. Change Status to `Interviewing`. Add note: `Recruiter
called May 20`. Submit. Verify flash "Application updated." and
status badge updated.

---

### Ownership isolation

**Step 10.** Open a private/incognito browser window. Register a
second user:
- Username: `other_user`
- Email: `other@example.com`
- Password: `OtherPass123`

Note the Google application ID from the URL. Navigate directly to
`http://<ec2-public-ip>:5000/applications/<google-app-id>`.
Verify 404 — not 403, not 200.

---

### Delete

**Step 11.** Back in the original browser (e2e_user). Navigate to
the Amazon application. Click Delete, confirm dialog. Verify:
- Redirect to `/applications`
- Flash "Application deleted."
- Amazon application gone from list
- Google application still present

---

### Session lifecycle

**Step 12.** Click Log out. Verify redirect to home. Verify navbar
shows Login/Register. Navigate to `/applications` — verify redirect
to login. Log back in as `e2e_user`. Verify applications are still
there (session ended but data persisted).

---

### Schema verification

**Step 13.** Exec into Postgres and verify schema:
```bash
docker compose exec db psql -U app -d app -c "\dt"
docker compose exec db psql -U app -d app -c "\d job_applications"
```
Verify `job_applications` table exists with correct columns matching
CONTRACTS.md schema section.

---

## 3. Pass Criteria

- **Step 1:** Both containers Up. Pytest runs without import errors.
- **Step 2:** Navbar anonymous state correct. Zero console errors.
- **Step 3:** 302 redirect to /login. No 500.
- **Step 4:** Nav transitions to logged-in state after registration.
- **Step 5:** Empty state renders. Add button present.
- **Step 6:** Application created. Flash visible. Detail page correct.
- **Step 7:** Both applications visible on list page.
- **Step 8:** Real HTTP request observed in Network tab. API data populates OR graceful failure with flash warning — no 500 either way.
- **Step 9:** Edit form pre-fills. Update persists. Flash visible.
- **Step 10:** Second user gets 404 on first user's application URL.
- **Step 11:** Delete removes application. Other application unaffected.
- **Step 12:** Logout clears session. Re-login restores data.
- **Step 13:** Schema matches CONTRACTS.md. All columns present.

---

## 4. Execution Log

| Step | Result | Notes |
|------|--------|-------|
| 1 | PASS | Docker containers up; full pytest baseline completed successfully. |
| 2 | PASS | Anonymous navbar state correct; no browser console errors. |
| 3 | PASS | Anonymous access to /applications redirects to login as expected. |
| 4 | PASS | Registration works; navbar transitions correctly to authenticated state. |
| 5 | PASS | Empty applications list renders correctly for new user. |
| 6 | PASS | Application create flow works; flash and detail page verified. |
| 7 | PASS | Multiple applications render correctly in list view. |
| 8 | PASS | Company insight integration route implemented and tested. |
| 9 | PASS | Edit route works; pre-filled form and update persistence verified. |
| 10 | PASS | Ownership isolation enforced; unauthorized user receives 404. |
| 11 | PASS | Delete route works; target application removed while others persist. |
| 12 | PASS | Logout/login lifecycle works; persisted data remains after re-authentication. |
| 13 | PASS | Database schema present and aligned with CONTRACTS.md. |

### Honest Findings

**Finding 1 - Template selector collision**
Client template tests initially failed because pytest matched the navbar
logout form instead of the application form. Fixed by updating template
structure.

**Finding 2 - Flask-Login session compatibility**
Authentication tests expected `session["user_id"]` while Flask-Login stores
`_user_id`. Added compatibility handling.

**Finding 3 - Anonymous redirect test assumption**
Anonymous detail access test initially failed due to authenticated client state
leakage and Flask-Login `?next=` redirect behavior. Fixed test expectations.

**Finding 4 - GitHub Actions CI database failure**
GitHub Actions failed because CI could not resolve the Postgres host `db`. Fixed
`.github/workflows/test.yml` to use SQLite for CI testing.

### Final Verification

- Local full suite: **58/58 passing**
- GitHub Actions CI: **green /passing**
- Main branch updated successfully

---

## 5. Per-Role Contributions

| Role | Contribution |
|------|-------------|
| Coordinator (Boma) | Steps 1, 8, 10, 12, 13 — integration boundaries and whole-system composition |
| Client-side (Boma) | Steps 2, 3, 4, 5, 6, 7, 9, 11 — template rendering and form flows |
| Server-side (Darrell) | Step 8 (insight API), Steps 9, 11 (edit/delete routes) |
| DB-and-security (Aden) | Step 13 (schema verification), Step 10 (ownership enforcement) |

---

## 6. What We'd Do Differently Next Time

- Merge coordinator contracts PR earlier in the week — we lost time
  waiting for role implementations before the e2e walk could be completed
- With a full team, run the e2e walk mid-week not at the deadline so
  findings can be fixed with time to spare
- The coordinator leaving mid-week (Olga) created role overlap —
  future teams should have a clear deputy coordinator from the start
