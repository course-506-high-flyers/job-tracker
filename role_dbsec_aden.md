# Assignment 8 — Part C: Role-Specific (DB / Security)

**Author:** Aden
**Role:** DB-and-Security on a 3-person team (High Flyers).
Per the brief's role-collapse rule for 3-person teams, this slice owns the
deploy pipeline + secrets handling as well, so all 9 questions below are mine.
**Branch:** `aden-hardening` → `hardening` → `main`
**Companion artifacts in this PR:**
`nginx.conf`, `docker-compose.yml`, `tests/test_attack_paths.py`,
`attack_paths.json`, `scripts/make-dev-certs.sh`.

> Note: Q1 includes a local sidecar baseline (2026-06-01) for before/after
> comparison, plus production evidence re-run on the deployed docker-compose
> stack (2026-06-11). Production nginx keeps `access_log off` on attack-path
> locations, so the live proof is curl status codes plus a zero delta in the
> gunicorn access log — not nginx access-log lines for those paths.

---

## Q1 — nginx as a filter: prove you absorb attack traffic before Flask sees it

The claim: an unauthenticated probe for any path in `attack_paths.json` is
served entirely by nginx, returns 404, and never lands in the gunicorn
(today: `python app.py`) access log.

**Evidence rig.** Brought up the stack on 2026-06-01 with three pieces:
`docker compose up -d` for app + db on the `job-tracker_backend` network, then
`docker run -d --name nginx-test --network job-tracker_backend ... nginx:1.27-alpine`
mounting `nginx.conf` and `./certs/`. The nginx sidecar exposed `:8080` (http)
and `:8443` (https) on the host.

**Before nginx — direct Flask hits.** Six probes, port 5000, all reach Flask
and are 404'd by Flask's default route handler:

```
app-1 | 172.19.0.1 - - [01/Jun/2026 18:23:10] "GET /wp-login.php HTTP/1.1" 404 -
app-1 | 172.19.0.1 - - [01/Jun/2026 18:23:10] "GET /.env HTTP/1.1" 404 -
app-1 | 172.19.0.1 - - [01/Jun/2026 18:23:10] "GET /phpmyadmin/ HTTP/1.1" 404 -
app-1 | 172.19.0.1 - - [01/Jun/2026 18:23:10] "GET /backup.sql HTTP/1.1" 404 -
app-1 | 172.19.0.1 - - [01/Jun/2026 18:23:10] "GET /test/login/aden HTTP/1.1" 404 -
app-1 | 172.19.0.1 - - [01/Jun/2026 18:23:10] "GET /.env.save HTTP/1.1" 404 -
```

This is what Flask logs look like when there is no nginx in front. The 404
is correct, but every probe still consumes a Werkzeug worker turn and
pollutes our log.

**After nginx — same probes via the sidecar at https://localhost:8443.**

```
172.19.0.1 - - [01/Jun/2026:18:24:34 +0000] "GET /wp-login.php HTTP/2.0" 404 146 "-" "curl/8.5.0" "-" rt=0.000
172.19.0.1 - - [01/Jun/2026:18:24:34 +0000] "GET /.env HTTP/2.0" 404 146 "-" "curl/8.5.0" "-" rt=0.000
172.19.0.1 - - [01/Jun/2026:18:24:34 +0000] "GET /phpmyadmin/ HTTP/2.0" 404 146 "-" "curl/8.5.0" "-" rt=0.000
172.19.0.1 - - [01/Jun/2026:18:24:34 +0000] "GET /backup.sql HTTP/2.0" 404 146 "-" "curl/8.5.0" "-" rt=0.000
172.19.0.1 - - [01/Jun/2026:18:24:34 +0000] "GET /test/login/aden HTTP/2.0" 404 146 "-" "curl/8.5.0" "-" rt=0.000
172.19.0.1 - - [01/Jun/2026:18:24:34 +0000] "GET /.env.save HTTP/2.0" 404 146 "-" "curl/8.5.0" "-" rt=0.000
```

Flask's request counter delta across these 6 probes was **0**. The proof:

```
Flask request count BEFORE probes: 6
Flask request count AFTER  probes: 6
DELTA = 0  (zero means nginx absorbed every probe)
```

**Why this works.** The relevant blocks in `nginx.conf` are at the top of the
`:443` server, *before* any `proxy_pass` location:

```
location ~* ^/(\.env(\..*)?|\.git(/.*)?|\.svn(/.*)?|\.htaccess|\.htpasswd)$ { ... return 404; }
location ~* ^/(wp-login\.php|wp-admin|wp-config\.php|xmlrpc\.php) { ... return 404; }
location ~* ^/(phpmyadmin|pma|adminer)(/|$) { ... return 404; }
location ~* ^/(backup\.sql|dump\.sql|database\.sql|.*\.bak)$ { ... return 404; }
location ~* ^/test/login/ { ... return 404; }
```

Each carries `access_log off;` in production so the noise from internet-wide
scanning doesn't fill our disk. (For the evidence above I temporarily
re-enabled access logging on a sidecar copy; the production config keeps
`access_log off` for these paths.)

**Production re-run (2026-06-11, docker compose on EC2).** Team live URL:
`https://35.86.191.136`. Same six probes via `curl -sk https://localhost<path>`
on the deployed host with nginx, app, and db all Up:

```
/wp-login.php      code=404
/.env              code=404
/phpmyadmin/       code=404
/backup.sql        code=404
/test/login/aden   code=404
/.env.save         code=404
```

Gunicorn access-log delta across these six probes was **0** — no new lines
for any of the six paths appeared in `docker compose logs app` after the
run. Production nginx returns 404 at the edge; because `access_log off` is
set on these location blocks, the confirmation is status code + app-log
silence, not nginx access-log lines.

---

## Q2 — Attack-path test: automate it and report literally

The deliverable is `tests/test_attack_paths.py` plus `attack_paths.json`, both
shipped in this PR. The test is parametrized over the 16 entries in the JSON
file and asserts two things per path:

1. Status code is one of `{301, 302, 404}`.
2. Response body contains none of: `traceback`, `werkzeug`, `sqlalchemy`,
   `psycopg2`, `secret_key`, `postgres://`, `postgresql://`.

A third test asserts that the http-side of the base URL 301-redirects to
https.

**Run output (local, 2026-06-01):**

```
$ JOB_TRACKER_BASE_URL=https://localhost:8443 pytest tests/test_attack_paths.py -v
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-7.4.3, pluggy-1.6.0
collected 33 items

tests/test_attack_paths.py::test_attack_path_returns_safe_status[/.env]                       PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/.env.example]               PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/.env.save]                  PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/.env.save.bak]              PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/.git/config]                PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/wp-login.php]               PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/wp-admin/]                  PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/xmlrpc.php]                 PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/phpmyadmin/]                PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/adminer.php]                PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/admin]                      PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/backup.sql]                 PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/dump.sql]                   PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/test/login/aden]            PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/test/login/admin]           PASSED
tests/test_attack_paths.py::test_attack_path_returns_safe_status[/static/../app.py]           PASSED
tests/test_attack_paths.py::test_attack_path_body_does_not_leak_internals[/.env]              PASSED
... (15 more body-leak checks, all PASSED)
tests/test_attack_paths.py::test_https_only_root_redirects                                    PASSED

======================= 33 passed, 32 warnings in 2.46s ========================
```

The 32 warnings are `InsecureRequestWarning` from the self-signed dev cert —
expected and silenced via `JOB_TRACKER_VERIFY_TLS=true` once we point at a
Let's Encrypt host.

**Two repo-specific cases worth flagging out loud:**

- `/.env.save` and `/.env.save.bak` are not generic scanner targets. They're
  in `attack_paths.json` because this clone's history (`ADENDATA.md` Turn 21)
  shows a real near-miss where someone ran `cp .env .env.save` while editing.
  Test passes today; the real reason it passes is the regex
  `/\.env(\..*)?` in `nginx.conf` plus the `.env.save` / `.env.save.bak`
  entries in the new `.gitignore` block.
- `/test/login/aden` and `/test/login/admin` exercise the TESTING-gated
  backdoor at `app.py:354`. Flask itself returns 404 in production
  (`abort(404)` if `app.config["TESTING"]` is falsy), but I added an explicit
  nginx 404 above that line as belt-and-suspenders. If anyone ever flips
  `TESTING=True` in a prod env file by accident, nginx still returns 404
  before Flask gets the chance to hand out a session.

---

## Q3 — Hardening test strategies: what an LLM suggested and what I picked

I asked an LLM for "three different ways to test that my hardened nginx
config actually filters attack traffic." Five suggestions came back. My
triage:

| Strategy | What it does | Why I did / didn't pick it |
|---|---|---|
| **pytest parametrize** (what I shipped) | Static list of paths; 33 assertions, runs in 2.5s, deterministic. | Picked. Cheap, lives in our existing pytest harness, runs in CI without extra infra. |
| **OWASP ZAP automated scan** | Crawls the live app, runs ~50 active rules (SQLi, XSS, header checks). | Did not ship. Adds a Java runtime to CI and ZAP false-positives on the framework boilerplate. Worth running once manually before submission as a cross-check; would not gate every commit on it. |
| **nuclei** with community templates | YAML-driven, ~7000 templates, very fast. | Did not ship. Same gating concern as ZAP. Worth running once manually against the deployed host; templates for `wordpress-detect` and `exposed-env` would catch what my static list misses. |
| **AFL-style fuzzer / wfuzz** | Random / dictionary-based path enumeration. | Rejected for this assignment. The point of the static list is to have a regression suite a marker can read. A fuzzer's output is "no findings", not "we explicitly tested these 16 paths". |
| **Behavioral test: 6 failed `/login` posts → expect 429** | Verifies the rate-limit zone, not just the 404 list. | Considered, kept *separate* from `test_attack_paths.py`. The attack-path test is read-only GETs; rate-limit verification needs POSTs and a clean rate window between runs, which is a different flakiness profile. A standalone `test_rate_limit.py` is the example shape if this is ever picked up; not in scope for this PR. |

The honest summary: my static-list test is the floor, not the ceiling. It
catches regressions in `nginx.conf` ("did someone delete the `wp-login`
location block?") cheaply. ZAP/nuclei catch what the static list doesn't
think to ask. They are complements, not alternatives.

---

## Q4 — DB trust boundary: what does it protect, what doesn't it?

The hardening I shipped on `db:` in `docker-compose.yml`:

- No `ports:` published. `5432` is not bound on any host interface.
- `db:` is attached only to the `backend` docker network.
- Credentials come from `.env` via `${POSTGRES_USER:?msg}` strict syntax;
  `docker compose up` aborts if any are missing.
- Healthcheck uses the runtime-resolved user/db (`pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`).

I verified the boundary holds locally:

```
$ /dev/tcp/localhost/5432
bash: connect: Connection refused
PORT CLOSED ON HOST  (good - db trust boundary holds)
```

| What this protects against | What this does NOT protect against |
|---|---|
| External port scans against EC2:5432 | SQL injection from an authenticated user |
| Lateral movement from a compromised neighbor on EC2 | A compromised `app:` container with a valid `DATABASE_URL` |
| `kubectl port-forward`-style accidental exposure | A weak `POSTGRES_PASSWORD` in the team's shared `.env` |
| Stray `psql` from a developer's laptop with the prod DSN | A developer running `pg_dump` over the public internet |

The trust boundary is a *network* control. It is necessary but insufficient.

**What's already in this repo as application-layer defense in depth:**

- `models.py:24` — `UniqueConstraint("user_id", "company", "position", name="uq_job_applications_user_company_position")` blocks an authenticated user from inflating their own row count.
- `models.py:28` and `models.py:59` — `ForeignKey(..., ondelete="CASCADE")` on `applications.user_id` and `oauth_identity.user_id`. Deleting a user atomically deletes their data, no orphan rows survive an account close-out.
- `models.py:16` — `unique=True, index=True` on `users.username`. Eliminates a TOCTOU race on registration.
- All queries go through SQLModel/SQLAlchemy `select()`, never string concat. SQLAlchemy parameterizes every literal — SQLi via legitimate routes is blocked at the ORM layer, not the DB layer.

**Production upgrade path I deferred** (and why): flipping `internal: true`
on `networks.backend` blocks all internet egress from `app:` and `db:`. That
neutralizes data exfil from a compromised app container. I did not turn it
on in this PR because `/applications/<id>/insight` legitimately fans out to
Clearbit and API Ninjas; flipping the flag would break that endpoint until
Darrell either routes those calls through a forward proxy or attaches `app:`
to a `frontend` network alongside nginx.

---

## Q5 — Rate limits per route

Concrete table from `nginx.conf`. Justification per row:

| Route(s) | Zone | Rate | Burst | Justification |
|---|---|---|---|---|
| `/login`, `/register` | `auth_zone` | 5 r/m | 3 | Credential surface. 5 r/m allows typo retries on a real password but is brutal against credential stuffing (3000 attempts/IP/10h). |
| `/login/github`, `/auth/github/callback` | `oauth_zone` | 10 r/m | 5 | Slightly looser; OAuth flow involves user-driven redirects on flaky networks. Burst 5 absorbs a single user's "click button → loading → click again" pattern. |
| `/applications/<id>/insight` | `insight_zone` | 30 r/m | 5 | Each call fans out to Clearbit + API Ninjas (free tiers). 30 r/m matches our worst-case external quota burn before either upstream throttles us. |
| catch-all `/` | `general_zone` | 60 r/m | 20 | One legitimate user clicking around can hit ~30 routes/min easily. 60 with burst 20 absorbs a reload-spam. |
| (per-IP cap) | `conn_per_ip` | 20 concurrent | — | Independent of rate. Cheap DoS guardrail. |

All four `limit_req_zone` declarations key on `$binary_remote_addr`. Every
zone is `10m` of memory (~64k unique IPs).

**Tradeoff analysis I asked an LLM about, then verified.** Too low blocks
typo retries (a user gets locked out after one bad password and a corrected
re-attempt). Too high defeats the rate limit against a stuffing botnet
(50 zombies × 1 r/s = 50 r/s, which laughs at 60 r/m). The auth zone at
5 r/m + burst 3 is the floor — any tighter and our own QA breaks; any
looser and a single-IP attacker gets >300 attempts/h.

**Verified locally on 2026-06-01.** Hammered `/login` 8 times in 1 second
through the nginx sidecar:

```
attempt 1 -> HTTP 200      (allowed - inside burst)
attempt 2 -> HTTP 200      (allowed - inside burst)
attempt 3 -> HTTP 200      (allowed - inside burst)
attempt 4 -> HTTP 200      (allowed - inside burst, last slot)
attempt 5 -> HTTP 429      (rate limited)
attempt 6 -> HTTP 429
attempt 7 -> HTTP 429
attempt 8 -> HTTP 429
```

nginx error log on the same run:

```
2026/06/01 18:27:57 [warn] 33#33: *56 limiting requests, excess: 3.990
   by zone "auth_zone", client: 172.19.0.1, server: _,
   request: "GET /login HTTP/2.0", host: "localhost:8443"
```

`limit_req_status 429;` in the http context made nginx return 429 instead of
the default 503, which matters because clients (including our future
e2e tests) treat 429 as "back off and retry" while 503 reads as "service
broken".

---

## Q6 — LLM full-surface probe (high-level)

The full LLM transcript lives in `llm_probe_dbsec_aden.md` (separate deliverable
in this submission). Summary of method here:

I used the §24 combined prompt template from the brief and pasted four
context blocks into the model:

1. The full `nginx.conf` from this PR.
2. `attack_paths.json` (so the model can see what we already cover).
3. The team's actual current release flow today: `ssh ec2-user@<host>`
   followed by `cd /opt/job-tracker && git pull && docker compose up -d`.
   No CI deploy yet.
4. The 3-collaborators-with-commit fact for `course-506-high-flyers`.

Asked the model: "What classes of attack does this stack still leave open?"
Triaged the response in `llm_probe_dbsec_aden.md`. The honest items I did
something about in this PR are already captured in this file (Q1–Q5);
the items I deferred are listed there.

---

## Q7 — Secrets in three places (and the fourth where they leak)

Walking `OAUTH_CLIENT_SECRET` end-to-end.

1. **Generated** at https://github.com/settings/developers → "OAuth Apps" →
   New OAuth App. The secret is shown exactly once; copy or regenerate.
2. **Stored** as a GitHub Actions secret at
   https://github.com/course-506-high-flyers/job-tracker/settings/secrets/actions
   (one of the three pre-flight items I'm raising in coord_session: we don't
   have a deploy workflow yet, so this storage doesn't exist *today* — it
   becomes the right answer the moment Darrell or I add `.github/workflows/deploy.yml`).
3. **Used** at runtime via `docker compose --env-file .env up`. The secret
   is read by `app.py` at import time via `os.environ["OAUTH_CLIENT_SECRET"]`
   (strict, per the comment in `.env.example`). The container sees it; the
   image does not bake it.

**Fourth place, the leak surface:** `.env.save` and `.env.save.bak`. Per
`ADENDATA.md` Turn 21, this clone's history shows a real near-miss where a
maintainer ran `cp .env .env.save` while doing manual edits. The `.gitignore`
block I shipped in this PR closes that:

```
# Backup .env files. We had a near-miss (.env.save / .env.save.bak in the
# clone history); these patterns make sure a stray
# `cp .env .env.save` never lands in a commit again.
.env.save
.env.save.bak
.env.*.local
.env.*.bak
```

`tests/test_attack_paths.py` includes `/.env.save` and `/.env.save.bak` so
even if the gitignore is bypassed, nginx returns 404 before the file ever
serves over the wire.

**A separate concrete leak path I want to call out:** the `.env` file
itself, if checked in by accident (line 8 of `.gitignore` blocks it, but the
defense is one line of regex away from being deleted). `git secret` or
`pre-commit` with `detect-secrets` would catch this; deferred for now.

---

## Q8 — Tag-driven release

**For:**

- Explicit. Anyone reading the Git history can answer "what did we deploy
  on Tuesday?" by reading `git tag`.
- Reproducible rollback. `git checkout v0.4.1 && docker compose up -d`
  brings back exactly the previous bits, without arguing about which `main`
  SHA was running.
- Forces a human pause. You don't accidentally tag.

**Against:**

- Ceremony. For a 3-person class project, manual `git tag` + push is a
  step everyone forgets.
- Sequential bottleneck. Today our release flow is `ssh + git pull on EC2`;
  whoever last merged to `main` is what's running. Adding tags doesn't
  change the bottleneck, it just renames the SHA.
- Tags on a class project lie if not enforced. We have three people with
  push access; nothing in the workflow stops me from tagging a SHA that
  isn't actually deployed.

**Honest take for this team, this assignment:** I would not adopt
tag-driven release this week. I would pin EC2 to a specific SHA in the
`docker compose pull` step (or pin the image digest in `docker-compose.yml`)
because that's the same thing the tag is for, but it doesn't require
remembering to run `git tag`. When CI grows past the "one-EC2-instance"
phase, tags become the right answer.

---

## Q9 — When CI goes red, what do I ask the LLM (and what do I not)?

The principle: ask the LLM about *general patterns*, never about *our specific
code* or *team-private context*.

**Good LLM questions (general):**

- "GitHub Actions workflow runs `pytest` and exits 0, but the matrix view
  shows 'red'. What workflow-level issues cause that?"
- "What's the difference between `runs-on: ubuntu-latest` and a service
  container's image, and which one decides Python version?"
- "For pytest, when does `conftest.py` placement affect test collection?"
- "What does `actions/checkout@v4` do that `@v3` doesn't?"

**Bad LLM questions (specific to our repo):**

- "Why is my `tests/conftest.py` failing?" — without pasting the file. The
  LLM will hallucinate a fixture name.
- "What env vars does my app need at test time?" — the answer is in
  `.env.example` and a 30-second read; don't outsource it.
- "Why does my GitHub Actions secret not work in this team's repo?" — team-
  specific authorization rules; the LLM cannot see the org settings.
- "Pin our image to a digest" — the LLM doesn't know which digest is current;
  it will make one up. I'd run `docker manifest inspect postgres:16-alpine`
  myself.

**What I actually feed the LLM when CI is red:**

1. The full failing job log (copied from GitHub Actions).
2. The `.github/workflows/<name>.yml` file verbatim.
3. The `pyproject.toml` / `requirements.txt` / `Dockerfile` if relevant.

What I do *not* feed: any file that contains a secret, including
`.env.example` after I've populated it locally; `tests/conftest.py` if it
contains environment defaulting logic that mentions a secret name; the
team's coord doc.

The LLM is a senior engineer who showed up today and has not seen our repo.
Treat it that way.

---

*End of role_dbsec_aden.md.*
