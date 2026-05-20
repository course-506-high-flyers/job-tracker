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

- **Step 1:** PENDING - needs to be rerun on the deployed EC2/Docker environment.
- **Step 2:** PARTIAL PASS - SQLModel metadata test passes locally in Docker; deployed Postgres inspection still needed.
- **Step 3:** PENDING - direct duplicate insert must be run against deployed Postgres.
- **Step 4:** PENDING - cascade behavior must be verified with disposable test rows.
- **Step 5:** PENDING - browser cookie check must be run after deployment.
- **Steps 6-8:** BLOCKED - application route handlers and ownership checks depend on server-side routes.
