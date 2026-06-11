# Job Application Tracker - DB-and-Security E2E Walk

**Role:** DB-and-security  
**Owner:** Aden  
**Week:** 6

---

## 1. Definition

End-to-end for the DB-and-security slice means the deployed Flask app uses the
real Postgres schema, real database constraints, and Flask-Login session state.
This walk verifies that security behavior is enforced by the running system,
not only by pytest fixtures or SQLModel objects in memory.

---

## 2. The Walk

**Step 1.** Start from a clean deployed environment and verify both containers are running:
```bash
docker compose down -v && docker compose up -d
docker compose ps
```

**Step 2.** Exec into Postgres and inspect the schema:
```bash
docker compose exec db psql -U app -d app
\d users
\d job_applications
\d job_insights
```
Verify columns, types, NOT NULL rules, foreign keys, and UNIQUE constraints
match `CONTRACTS.md`.

**Step 3.** Insert one test user and one job application directly in SQL. Insert
the same `(user_id, company, position)` twice and verify Postgres rejects the
second insert with a UNIQUE constraint error.

**Step 4.** Delete the test user from Step 3, then query `job_applications` for
that user's rows. Verify the rows are gone through `ON DELETE CASCADE`.

**Step 5.** Browser auth walk: register, log out, then log back in. In dev
tools, inspect the session cookie and verify Flask-Login stores `_user_id`, not
the old raw `user_id` key.

**Step 6.** Anonymous route probe: log out, then directly open
`/applications`, `/applications/new`, and `/applications/1/edit`. Verify each
request redirects to `/login?next=...` and does not return 500.

**Step 7.** Ownership probe: log in as user A and create a job application.
Copy its application ID from the URL. Log out, log in as user B, and directly
open `/applications/<user-a-application-id>` and
`/applications/<user-a-application-id>/edit`.

**Step 8.** Confirm the ownership response is `404`, not `403` and not `200`.
The page must not reveal whether the application ID belongs to another user.

---

## 3. Pass Criteria

- **Step 1:** Containers are running and the app can reach Postgres.
- **Step 2:** `users`, `job_applications`, and `job_insights` match the schema in `CONTRACTS.md`.
- **Step 3:** Duplicate `(user_id, company, position)` insert fails in Postgres itself.
- **Step 4:** Deleting a test user removes that user's test applications.
- **Step 5:** Register, logout, and login work; session uses Flask-Login `_user_id`.
- **Step 6:** Anonymous application routes redirect to login with `next=`.
- **Step 7:** User B can directly request User A's application URL.
- **Step 8:** User B receives `404`; no cross-user data is displayed.

## 4. Execution Log

- **Commit tested:** `0aea273` (EC2 deploy; local `main` may be ahead)
- **Step 1:** PASS - On EC2 (2026-06-11), `docker compose ps` shows `job-tracker-nginx-1`, `job-tracker-app-1`, and `job-tracker-db-1` all Up; db healthy; nginx publishing :80 and :443.
- **Step 2:** PASS - On EC2, schema metadata test passed in Docker: `1 passed in 0.61s`. Direct Postgres `\d users`, `\d job_applications`, and `\d job_insights` inspection confirmed required tables, NOT NULL columns, `job_applications_user_id_fkey` with `ON DELETE CASCADE`, unique `(user_id, company, position)`, and unique `job_insights.company`. One typo (`jon_applications`) returned no relation, then the correct table name passed.
- **Step 3:** PASS - Direct SQL duplicate test on EC2 used test user id `2`. First `job_applications` insert succeeded; second identical `(user_id, company, position)` insert failed with `duplicate key value violates unique constraint "uq_job_applications_user_company_position"`. An initial `<USER_ID>` placeholder attempt caused a syntax error and was corrected to `2`.
- **Step 4:** PASS - Direct SQL cascade test on EC2 deleted disposable user id `2` with `DELETE 1`; `SELECT * FROM job_applications WHERE user_id = 2` returned `(0 rows)`, confirming `ON DELETE CASCADE` removed the owned application row.
- **Step 5:** PARTIAL PASS - Browser register, logout, and re-login worked on EC2. Flask-Login code path uses `login_user`/`logout_user` and pytest session evidence showed `_user_id`; browser session cookie is signed, so `_user_id` was not directly readable in dev tools.
- **Steps 6-8:** BLOCKED - application route handlers and ownership checks depend on server-side routes.
