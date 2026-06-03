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

Link: https://github.com/course-506-high-flyers/job-tracker/tree/main

As of submission (Jun 3, 2026), `main` HEAD is `571c211`. The tree
contains the full production stack — `nginx.conf` (256 lines, hardened
TLS + rate-limit zones + attack-path 404s + Boma's security headers
and `/static/` block), `docker-compose.yml`, and `gunicorn.conf.py`
— plus all Part B + Part C per-person documents.

### 2. Merged `hardening` branch

Link: https://github.com/course-506-high-flyers/job-tracker/tree/hardening

`hardening` HEAD is `a40c3ac` — the result of merging `boma-hardening`
into `hardening` via PR #12 (merged 2026-06-03 14:57 UTC by @okolib).
`hardening` was then merged into `main` via PR #13 (merged
2026-06-03 17:31 UTC by @okolib).

### 3. Per-student `<name>-hardening` branches

Each personal branch was the working surface for one teammate's
hardening slice. The brief specifies: "Don't delete the personal
branches. They're part of the evidence."

| Owner | Branch | Status | Link |
|---|---|---|---|
| Boma   | `boma-hardening`    | **On origin.** HEAD `afea3ef`. Frontend Part A + Part B + Part C; merged to `main` via PR #12 → PR #13. | https://github.com/course-506-high-flyers/job-tracker/tree/boma-hardening |
| Aden   | `aden-hardening`    | **On origin.** HEAD `3b6a8ff` (`b5c028e` Part A + `3b6a8ff` Part B/C). Merged to `main` via recovery PR #14 — see conflict-resolution log below. | https://github.com/course-506-high-flyers/job-tracker/tree/aden-hardening |
| Darrell | `darrell-hardening` | **On origin.** HEAD `7e10ff4`. Part A `ProxyFix` middleware + Part C backend documentation. Not yet merged to `main` as of submission window. | https://github.com/course-506-high-flyers/job-tracker/tree/darrell-hardening |

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
| Production-stack docs | `README.md` "Running the production stack" section | Boma (landed via PR #12, commit `306ec1d`) |

The merge structure preserves the per-slice attribution in git history
for the reviewer (each personal branch is still on origin per the
brief's preservation requirement).

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

## PRs

The full merge sequence, in chronological order:

| # | PR | Slice | Merged (UTC) | Merged by | Link |
|---|---|---|---|---|---|
| 1 | #12 | Boma — frontend hardening (`boma-hardening` → `hardening`) | 2026-06-03 14:57 | @okolib | https://github.com/course-506-high-flyers/job-tracker/pull/12 |
| 2 | #13 | `hardening` → `main` (carries Boma's slice; `week8-final` tag landed at `37341a9`) | 2026-06-03 17:31 | @okolib | https://github.com/course-506-high-flyers/job-tracker/pull/13 |
| 3 | #14 | Aden — DB/sec hardening + Part B + Part C (`aden-hardening-into-main` → `main`); recovery PR after Draft PR #11 was bypassed | 2026-06-03 18:06 | @okolib | https://github.com/course-506-high-flyers/job-tracker/pull/14 |
| 4 | (follow-up commit `571c211`, not a PR) | Boma activated her security headers + `/static/` block inside the `=== BOMA ===` slot Aden's `nginx.conf` left for her | 2026-06-03 18:21 | @okolib | https://github.com/course-506-high-flyers/job-tracker/commit/571c211 |

PRs not in the `main` lineage:

| # | PR | Slice | State | Link |
|---|---|---|---|---|
| — | #11 | Aden — original Draft PR (`aden-hardening` → `hardening`), opened 2026-06-02 16:11 UTC | CLOSED (superseded by PR #14) | https://github.com/course-506-high-flyers/job-tracker/pull/11 |

Darrell's PR is pending as of the submission window. His `app.py`
ProxyFix and `role_backend.md` / `llm_probe_backend.md` documents
exist on `darrell-hardening` but have not yet landed on `main`
via PR.

---

## Conflict-resolution log (the "composition problem" lived in our repo)

The Assignment 8 merge sequence on Jun 3, 2026 surfaced one
non-trivial composition issue: a Draft PR was bypassed in the team
merge pass, and a follow-up recovery PR carried the bypassed work in
afterward.

**Timeline:**

1. **2026-06-02 16:11 UTC** — Aden opens PR #11 (`aden-hardening` →
   `hardening`) as **Draft**. Intent: coordinate the merge order with
   Boma and Darrell before flipping the PR to "Ready for review."

2. **2026-06-03 14:57 UTC** — Boma (acting as coordinator) merges
   PR #12 (`boma-hardening` → `hardening`). PR #11 is skipped because
   the Draft flag deprioritized it in the merge queue.

3. **2026-06-03 17:31 UTC** — Boma merges PR #13 (`hardening` →
   `main`) and the `week8-final` tag lands at commit `37341a9`.
   PR #11 still not merged. Aden's Part A nginx hardening (rate-limit
   zones, attack-path 404s, TLS hardening, attack-path test fixture
   and pytest suite, dev-cert generator) and the `_aden`-suffixed
   Part B + Part C deliverables are NOT in `main` or the tag.

4. **2026-06-03 17:43 UTC** — Aden opens recovery PR #14
   (`aden-hardening-into-main` → `main`). PR #14 is a merge commit of
   `aden-hardening` (Aden's work) and `main` HEAD (Boma's merged
   state), with four conflict resolutions documented in the PR body:
   - `.gitignore`: kept Aden's 42-line superset (Aden adds A8
     cert/secret ignore rules on top of Boma's 17 baseline lines).
   - `nginx.conf`: kept Aden's 262-line hardened config with explicit
     `=== BOMA ===` placeholder slots for her security headers and
     `/static/` block; her actual values to be re-applied in a
     follow-up commit (see step 6).
   - `team_evidence.md`: kept Aden's 137-line version (this file)
     over Boma's 24-line stub, since Aden's matches the Pattern A
     structure the brief asks for.
   - `docker-compose.yml`: kept Boma's 43-line version (already
     deployed in `week8-final`); deliberately did NOT apply Aden's
     stricter env-var requirement, backend-only network, or restart
     policy in this PR to avoid breaking the deployed stack. Those
     improvements remain on `aden-hardening` as a follow-up candidate.

5. **2026-06-03 18:06 UTC** — Boma reviews and merges PR #14. Commit
   `407e258` brings Aden's work onto `main`.

6. **2026-06-03 18:21 UTC** — Boma pushes commit `571c211`
   "Activate Boma security headers and static block in nginx.conf",
   porting her real `add_header` directives (HSTS, X-Frame-Options,
   X-Content-Type-Options, Referrer-Policy, Content-Security-Policy)
   and `/static/` block into the `=== BOMA ===` slots Aden's
   `nginx.conf` left for her. This resolves the only regression risk
   introduced by PR #14 — without this commit, `main` would have had
   commented placeholders where Boma's working headers previously
   lived.

**Lesson recorded:** Draft PRs need an explicit "ready by X" comment
on the PR body itself, not just a team-channel signal. Without that
explicit pin, the Draft flag becomes "don't merge" indefinitely, and
the work gets stranded. The team's merge protocol going forward should
treat Draft PRs as opt-out of the next coordinated merge unless the
PR body says otherwise.

The `week8-final` tag intentionally remains pointing at the
pre-PR-#14 state (`37341a9`) as a record of what was originally
submitted at that moment. The post-recovery state lives on `main`
HEAD (`571c211`) and is the canonical "as-graded" team output.

---

*End of team_evidence.md.*
