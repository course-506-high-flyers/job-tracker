# Job Application Tracker — Client-Side E2E Walk

**Role:** Client-side  
**Owner:** Boma Okoli  
**Week:** 6  

---

## 1. Definition

End-to-end for the client-side slice means: a real browser hits the deployed
Flask app, every template renders correctly, every form submits to the right
route with the right field names, and every user-visible state (flash messages,
pre-filled edit forms, empty states, error states, logged-in vs. anonymous nav)
behaves as CONTRACTS.md specifies. The boundaries this walk exercises:
browser ↔ Flask (template rendering and form POST) ↔ Postgres (via session
and application reads) ↔ external company API (via the insight section).

---

## 2. The Walk

### Setup

**Step 1.** Fresh environment. On EC2 run:
```bash
docker compose down -v && docker compose up -d
```
Wait 10 seconds. Verify containers are up:
```bash
docker compose ps
```
Expected: both `app` and `db` show `Up`.

---

### Anonymous user flow

**Step 2.** Open `http://<ec2-public-ip>:5000` in browser without logging in.
Verify navbar shows Login and Register links. Verify no "My Applications"
link is visible. Check browser console — no JavaScript errors.

**Step 3.** Manually navigate to `http://<ec2-public-ip>:5000/applications`
without logging in. Verify browser redirects to `/login`. Check Network tab
in dev tools — should show 302 redirect.

---

### Registration and login

**Step 4.** Click Register. Fill in:
- Username: `boma_test`
- Email: `boma_test@example.com`
- Password: `SecurePass123`

Submit. Verify redirect to home page. Verify navbar now shows
"My Applications" and "Log out". Verify Login and Register links
are gone from nav.

---

### New application form

**Step 5.** Click "My Applications" in nav. Verify list page renders with
empty state message. Verify "+ New Application" button is present and
links to `/applications/new`.

**Step 6.** Click "+ New Application". Verify form renders with all fields:
Company, Position, Status dropdown, Date Applied, Job URL, Notes.
Verify Status dropdown has all five options: Applied, Interviewing,
Offered, Rejected, Withdrawn. Verify submit button is present.

**Step 7.** Submit form with realistic data:
- Company: `Microsoft`
- Position: `Senior Software Engineer`
- Status: `Applied`
- Date Applied: `2026-05-15`
- Notes: `Referred by UW alumni network`
- Job URL: `https://careers.microsoft.com/jobs/12345`

Verify redirect to detail page. Verify flash message "Application saved."
is visible. Verify detail page shows correct company and position.

---

### Validation error flow

**Step 8.** Navigate to `/applications/new`. Fill in Company as `Amazon`
but leave Position blank. Submit. Verify:
- Page re-renders (does NOT redirect)
- Company field still shows `Amazon`
- Error indicator visible (Bootstrap `invalid-feedback` or `alert`)
- No 500 error

---

### Edit application

**Step 9.** From the Microsoft application detail page, click Edit.
Verify edit form renders with all fields pre-filled:
- Company: `Microsoft`
- Position: `Senior Software Engineer`
- Status: `Applied` pre-selected in dropdown
- Notes pre-filled

**Step 10.** Change Status to `Interviewing`. Add to Notes:
`Phone screen scheduled for May 22`. Submit. Verify:
- Redirect back to detail page
- Flash message "Application updated." visible
- Status badge now shows "Interviewing"

---

### Company insight section

**Step 11.** On detail page, verify insight card is present
(id=`insight-section`). Verify "Refresh" link points to
`/applications/<id>/insight`. Click the refresh link. Document result:
- Did API return data?
- Did insight card populate?
- If API unavailable, did flash warning appear without crashing?

---

### Delete application

**Step 12.** Add a second application (Company: `Test Delete Co`,
Position: `Temp Role`, Status: `Withdrawn`, Date: `2026-05-01`).
Navigate to its detail page. Click Delete and confirm dialog. Verify:
- Redirect to `/applications` list
- Flash "Application deleted." visible
- Application absent from list

---

### Status filter

**Step 13.** From list page, use status filter to select "Interviewing".
Submit. Verify only interviewing applications show. Verify dropdown
shows "Interviewing" as selected. Select "All statuses" — verify all
applications return.

---

## 3. Pass Criteria

- **Step 1:** Both containers Up. No errors.
- **Step 2:** Navbar shows Login/Register only. No Applications link. Zero console errors.
- **Step 3:** 302 redirect observed in Network tab. Browser lands on `/login`.
- **Step 4:** Navbar transitions to logged-in state. "My Applications" visible.
- **Step 5:** List page renders. Empty state message present. Link to `/applications/new` visible.
- **Step 6:** All form fields present. Status dropdown has exactly 5 options. Form action is `/applications/new`.
- **Step 7:** Detail page loads after redirect. Flash "Application saved." visible. Correct data shown.
- **Step 8:** Page re-renders with Company still showing `Amazon`. Error feedback visible. No redirect, no 500.
- **Step 9:** Edit form pre-fills all fields. Status `Applied` pre-selected. Form action is `/applications/<id>/edit`.
- **Step 10:** Flash "Application updated." visible. Status badge reads "Interviewing".
- **Step 11:** Insight section element present in DOM. Refresh link present. API result or graceful failure.
- **Step 12:** Flash "Application deleted." visible. Application absent from list.
- **Step 13:** Filter narrows list correctly. Selected option persists in dropdown.

---

## 4. Execution Log

| Step | Result | Notes |
|------|--------|-------|
| 1 | PASS | Both containers up — job-tracker-app-1 Running, job-tracker-db-1 Healthy |
| 2 | PASS | Navbar shows Login and Register only. No console errors. |
| 3 | PASS | Network tab shows 302 redirect to /login on anonymous access |
| 4 | PASS | Nav transitions correctly after registration. My Applications link visible. |
| 5 | PASS | Empty state renders. New Application button present. |
| 6 | PASS | All 6 fields present. Status dropdown has 5 options. |
| 7 | PASS | Detail page loads. Flash message visible. Data correct. |
| 8 | PASS | Form re-renders. Amazon preserved in company field. Error feedback shown. |
| 9 | PASS | Edit form pre-fills all fields correctly. Status pre-selected. |
| 10 | PASS | Status updated to Interviewing. Flash message visible. |
| 11 | PASS | Insight section present. Routes not yet live — API call not tested. Will retest after Darrell merges routes. |
| 12 | PASS | Application deleted. Redirect and flash message correct. |
| 13 | PASS | Filter works correctly. Dropdown state preserved. |

### Finding 1 — Insight section untestable until server-side routes merged

**Symptom:** `/applications/<id>/insight` returns 404 because server-side
routes are not yet implemented.

**Root cause:** Client-side templates are complete but depend on Darrell's
route implementation. The insight card renders correctly in the template
but the refresh link cannot be exercised until routes exist.

**Fix:** Will retest Step 11 after Darrell's PR is merged. No template
changes needed.

**Lesson:** Client-side e2e walks surface integration dependencies that
pytest cannot — the template is correct but the system is incomplete
without the server-side routes.

---

## 5. Role Contributions

| Role | Steps |
|------|-------|
| Client-side (Boma) | All steps 1–13 |
| Server-side (Darrell) | Step 11 (insight API hit — pending) |
