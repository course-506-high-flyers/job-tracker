# Assignment 8 — Part A: Team Evidence

**Team:** High Flyers
**Members:**
- Boma (Client-side / Frontend)
- Aden (DB-and-Security)
- Darrell (Server-side / Backend)

**Submission note:** Per the assignment brief ("can be the same file
submitted by all team members"), this is one shared file. All three
teammates submit an identical copy of it inside their own Canvas zip.
The file is checked into the team repo at the root, with no per-person
suffix, so all three teammates can edit it without naming collisions.

---

## Repo

GitHub organization: `course-506-high-flyers`
Repo: `job-tracker`
URL: https://github.com/course-506-high-flyers/job-tracker

---

## Links the rubric asks for

### 1. `main` with the stack committed

> **TODO before submission:** replace with the direct link to `main`
> after `hardening` has been merged in.
> Format:
> `https://github.com/course-506-high-flyers/job-tracker/tree/main`
> Verification before submission: visit the link, confirm `nginx.conf`,
> `docker-compose.yml`, and `gunicorn.conf.py` are all present at the
> tree root.

Link: https://github.com/course-506-high-flyers/job-tracker/tree/main

### 2. Merged `hardening` branch

> **TODO before submission:** push `hardening` to origin (currently
> exists locally only on Aden's clone), merge all three personal
> branches into it via PRs, then merge `hardening` → `main`.
> Format:
> `https://github.com/course-506-high-flyers/job-tracker/tree/hardening`

Link: https://github.com/course-506-high-flyers/job-tracker/tree/hardening

### 3. Per-student `<name>-hardening` branches

Each personal branch was the working surface for one teammate's
hardening slice. The brief specifies: "Don't delete the personal
branches. They're part of the evidence."

| Owner | Branch | Status | Link |
|---|---|---|---|
| Boma   | `boma-hardening`    | TODO — Boma to push | https://github.com/course-506-high-flyers/job-tracker/tree/boma-hardening |
| Aden   | `aden-hardening`    | **On origin.** Tracking commit `b5c028e` (Part A slice). | https://github.com/course-506-high-flyers/job-tracker/tree/aden-hardening |
| Darrell | `darrell-hardening` | TODO — Darrell to push | https://github.com/course-506-high-flyers/job-tracker/tree/darrell-hardening |

---

## Per-slice ownership (for reviewer context)

The hardening surface was split per the brief's role boundaries:

| Layer | File(s) | Owner |
|---|---|---|
| Network edge — TLS termination, rate-limit zones, attack-path 404s | `nginx.conf` (server block + `:443` block + attack-path locations) | Aden |
| Network edge — security headers, `/static/` block | `nginx.conf` (security-headers block + `/static/` location) | Boma |
| Python process — WSGI server config | `gunicorn.conf.py` | Darrell |
| Python process — TLS-trust glue | `app.py` (`ProxyFix` middleware) | Darrell |
| Container topology — `db:` service hardening | `docker-compose.yml` (`db:` service: no public ports, named volume, healthcheck) | Aden |
| Container topology — `nginx:` and `app:` wiring | `docker-compose.yml` (`nginx:` service + `app:` gunicorn swap + frontend network) | Darrell |
| Cert generation | `scripts/make-dev-certs.sh` | Aden |
| Dockerfile swap to gunicorn | `Dockerfile` | Darrell |
| Secrets hygiene | `.gitignore` (Assignment 8 block: `certs/`, `.env.save*`, `*.key`, `*.crt`, `*.pem`) | Aden |
| Production-stack docs | `README.md` "Running the production stack" section | Team (TODO) |

The merge structure (each personal branch landing on `hardening` via
PR) preserves the per-slice attribution in git history for the
reviewer.

---

## How to verify the stack runs from `main`

Per the brief's "What 'done' looks like" criteria:

1. Clone the repo and `cd job-tracker`.
2. Copy the env template: `cp .env.example .env`.
3. Populate `.env` (see `.env.example` for required keys —
   `SECRET_KEY`, `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
   `POSTGRES_DB`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`).
4. Generate dev certs: `bash scripts/make-dev-certs.sh`.
5. Bring up the stack: `docker compose up -d`.
6. Verify:
   - `curl -k https://localhost/` returns HTTP 200.
   - `curl -k https://localhost/healthz` (if implemented by Darrell) returns 200.
   - `curl http://localhost/` is redirected (301) to `https://`.
7. Tear down without losing data: `docker compose down` (volume
   retained); or `docker compose down -v` to wipe.

The full README section with copy-pasteable commands lives in the
"Running the production stack" section of `README.md`.

---

## PRs into `hardening`

> **TODO before submission:** list each PR by number with link, in
> merge order.
> Suggested format:

| # | PR | Slice | Merged | Link |
|---|---|---|---|---|
| 1 | TODO | Boma — frontend hardening   | TODO date | TODO link |
| 2 | TODO | Aden — DB/sec hardening     | TODO date | TODO link |
| 3 | TODO | Darrell — backend hardening | TODO date | TODO link |
| 4 | TODO | `hardening` → `main`        | TODO date | TODO link |

---

## Conflict-resolution log (the "composition problem" lived in our repo)

The brief notes that merge conflicts surface the composition problem.
For grading transparency, list any non-trivial conflicts that came up
during the merge sequence above.

> **TODO before submission:** fill in if any non-trivial conflicts
> arose. If no conflicts arose, write "No non-trivial conflicts; each
> slice touched a distinct file region per the per-slice ownership
> table above."

---

*End of team_evidence.md.*
