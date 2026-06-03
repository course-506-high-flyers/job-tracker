# Assignment 8 — Part B: Common Questions

**Author:** Aden (DB-sec slice, 3-person team)
**Branch:** `aden-hardening` → `hardening` → `main`
**Submission:** individual file. Each teammate writes their own; this is mine.

> Note to self: the seven questions below are paraphrased from the brief.
> Before submission, replace each question heading with the verbatim wording
> from the assignment PDF. Answers are anchored to concrete files / routes /
> commits in this repo (`course-506-high-flyers/job-tracker`) so a marker can
> click through.

---

## Q1 — Why nginx in front of Flask? Why not just run Flask directly?

**Concept.** Flask (and Python WSGI in general) is built to handle one request at a time per worker, in plaintext, with no awareness of TLS, no rate limiting, and no static-asset cache. nginx is a reverse proxy that owns the public network surface and does the things Flask was never meant to do.

**In this repo.** Three concrete jobs land on nginx in our `nginx.conf`, *none* of which can live inside `app.py`:

1. **TLS termination.** nginx holds the cert (mounted from `./certs/` in dev, Let's Encrypt material in prod) and speaks TLS 1.2/1.3 with Mozilla intermediate ciphers. Flask never sees the handshake.
2. **Rate limiting at the IP layer.** Four `limit_req_zone` declarations key on `$binary_remote_addr`: 5 r/m on `/login` and `/register`, 10 r/m on the GitHub OAuth pair, 30 r/m on `/applications/<id>/insight` (the external-API fan-out), 60 r/m everywhere else. Flask can't see traffic that nginx already returned 429 for.
3. **Attack-path absorption.** Probes for `/.env`, `/.git`, `/wp-login.php`, `/phpmyadmin/`, `/backup.sql`, plus the project-specific `/test/login/<username>` are returned as 404 by nginx without ever reaching Flask. Flask's logs stay readable.

**Artifact.** `nginx.conf` lines for `limit_req_zone` (http context) and the `location ~* ^/(\.env|\.git|...)` blocks inside the `:443` server block.

---

## Q2 — Why gunicorn instead of `flask run`?

**Concept.** `flask run` (and `python app.py`) spins up Werkzeug's development server: single process, single thread, no graceful restart, debug mode hot-reload, no production safeguards. gunicorn is a pre-fork WSGI server: N workers, configurable timeouts, worker recycling, signal handling, logs to stdout for the container runtime.

**In this repo.** Our slowest endpoint is `app.py:549` `/applications/<id>/insight`. It serializes Clearbit + API Ninjas calls (see `services/company_api.py`) — both synchronous external HTTP. Under `flask run`, a single user hitting that route blocks the entire process; everyone else waits for the third-party tail latency. Under gunicorn with 4 workers, three other users keep moving while one is waiting on Clearbit.

A second reason matters for hardening specifically: `python app.py` runs Flask's debug page on errors, which renders Python tracebacks and (in older versions) a console. Even with `debug=False`, any subprocess crash brings the whole app down because there's no worker pool to fall back on.

**Artifact.** `app.py:549` (`/applications/<id>/insight`) and the upstream block in `nginx.conf` pointing at `app:8000`. `gunicorn.conf.py` is Darrell's deliverable; my coord note at the top of `nginx.conf` documents the contract: `bind 0.0.0.0:8000`, not `127.0.0.1`.

---

## Q3 — Pick one concrete hardening you ship in this assignment. What changes?

**Concept.** A hardening is concrete if you can point at the line that changed, the threat it addresses, and the test that proves it.

**In this repo.** I'm picking `SESSION_COOKIE_SECURE = True` going from inert in week 7 to live in week 8.

In week 7, `app.py` already set `SESSION_COOKIE_SECURE` (and `REMEMBER_COOKIE_SECURE`) to `True` by default. But the dev stack served everything over `http://localhost:5000`, so browsers honored the flag the only way they could: by **not sending the session cookie at all on insecure responses**. That worked fine because nothing was insecure to begin with — there was no HTTPS endpoint to compare against. The cookie flag was correct but unverifiable.

In week 8, nginx terminates TLS on `:443` and 301-redirects every `:80` request. `SESSION_COOKIE_SECURE = True` now actually fires: the browser refuses to send the session cookie if anyone (a network attacker, a misconfigured proxy) downgrades the connection back to HTTP. Same line of code, completely different threat profile.

The four CSRF cases in `tests/test_csrf_protection.py` ride that same Secure cookie. So once HTTPS is the only entry point, both session integrity and CSRF defense are anchored to TLS.

**Artifact.** `app.py` `SESSION_COOKIE_SECURE` config (unchanged in this PR — that's the point), `nginx.conf` `:443` server block (new this PR), `tests/test_csrf_protection.py` (existing coverage that now means more).

---

## Q4 — Where does a load balancer sit relative to nginx?

**Concept.** "Load balancer" is overloaded. It can mean a Layer-4 TCP balancer (AWS NLB, HAProxy in TCP mode), a Layer-7 application balancer that terminates TLS and inspects HTTP (AWS ALB, nginx itself), or both stacked.

**In this repo.** Two reasonable placements, with different trade-offs:

- **LB in front of nginx (nginx as origin).** ALB / NLB on `:443`, terminates TLS at the edge with ACM, forwards to one or more EC2 instances each running our nginx. Wins: AWS-managed cert rotation, multi-AZ failover, easy horizontal scaling. Loses: rate-limit zones in our `nginx.conf` see the LB's IP, not the user's, unless we trust `X-Forwarded-For` (which itself needs `set_real_ip_from` directives we'd have to add). Today's `nginx.conf` keys rate limits on `$binary_remote_addr` directly, so this placement requires a follow-up edit.
- **LB replaces nginx.** ALB does TLS, security headers, attack-path 404s via WAF rules. Our app servers run gunicorn directly. Wins: one fewer moving part. Loses: ALB rate-limit features are coarser than nginx `limit_req_zone`, and WAF costs money per rule.

For a 3-person class project on a single EC2, neither is shipping today. nginx-on-EC2 with no LB is the realistic state. The right answer for the question is: "in front, when we go multi-instance — and we'll need `set_real_ip_from` to keep our rate limits correct."

**Artifact.** `nginx.conf` `limit_req_zone $binary_remote_addr` declarations (these are what would need to migrate to `$realip_remote_addr` once an LB lands).

---

## Q5 — What's the single point of failure in your current stack?

**Concept.** A SPOF is anything whose loss takes the whole product down with no automatic substitute.

**In this repo**, in order of severity:

1. **The single `db` Postgres container with one named volume `pgdata`.** No replication, no off-host backup, no PITR. If the EC2 host's disk dies, every user's application history goes with it. The named volume survives `docker compose down`, but not `docker compose down -v`, and not the host being terminated.
2. **The single EC2 instance.** No autoscaling group, no second AZ. AWS reboots the host → product is offline until it comes back.
3. **Docker Hub for `postgres:16-alpine` and `python:3.12-slim`.** If Docker Hub rate-limits or pulls a tag, our `Dockerfile` (and the `postgres:16-alpine` line in `docker-compose.yml`) fails on the next deploy. Pinning by SHA256 digest mitigates this; we don't pin today.
4. **One GitHub OAuth app per environment.** If we revoke the wrong client secret, login is broken for everyone until a redeploy with a new secret.
5. **Bus factor.** Three people, one assignment, one branch. If two of us go offline this week, deploy stops.

The realistic mitigation for (1) before submission: a periodic `pg_dump` cron into S3. For (3): pin digests in `Dockerfile` and `docker-compose.yml`. The rest are out of scope for an assignment.

**Artifact.** `docker-compose.yml` `db:` service (single replica, single volume) and `Dockerfile` `FROM python:3.12-slim` (mutable tag).

---

## Q6 — What does `docker compose down` do to your data?

**Concept.** `docker compose down` semantics depend on three things: whether your volumes are named or anonymous, whether you pass `-v`, and whether you've defined the volume in the top-level `volumes:` block or inline.

**In this repo**, our `docker-compose.yml` defines:

```
volumes:
  - pgdata:/var/lib/postgresql/data    # under db: service
volumes:
  pgdata:                               # top-level named volume declaration
```

That makes `pgdata` a **named volume**, which means:

| Command | Effect on `pgdata` |
|---|---|
| `docker compose stop` | container stopped, volume untouched, data persists |
| `docker compose down` | container removed, volume retained, data persists |
| `docker compose down -v` | container removed, **volume deleted**, data wiped |
| `docker compose down --rmi all` | image deleted, volume retained, data persists |

If `pgdata` had been declared inline as an anonymous volume (`- /var/lib/postgresql/data` with no source name), `docker compose down` would delete it on the next `up` because anonymous volumes are tied to the container they were created with.

**Verified locally** during this PR's smoke test: `docker compose up -d`, populated the `app.users` schema via the app's first request, ran `docker compose down`, ran `docker compose up -d` again — data was still there. Then `docker compose down -v` — clean slate on the next `up`.

**Artifact.** `docker-compose.yml` top-level `volumes: pgdata:` declaration (the line that makes the difference).

---

## Q7 — Surprise: something an LLM told me that turned out to need verification

**Concept.** LLMs are confidently wrong about specifics in ways that look plausible. The discipline is to feed them the actual file and verify the answer end-to-end before trusting it.

**In this repo**, the surprise was about `X-Forwarded-Proto`. I asked: "How do I make Flask treat requests as HTTPS once nginx is terminating TLS?" The LLM correctly told me to set `X-Forwarded-Proto $scheme;` in nginx — that header now lives in our `nginx.conf` proxy block. It also said Flask would "automatically" pick it up.

It does not. Flask's `request.is_secure`, `request.scheme`, and `url_for(_, _external=True, _scheme='https')` all read directly from the WSGI environment, which gets `wsgi.url_scheme = 'http'` because the actual TCP connection from nginx → gunicorn is HTTP. The `X-Forwarded-Proto` header is just a dictionary key in `request.headers` until something explicitly trusts it.

The fix is `werkzeug.middleware.proxy_fix.ProxyFix`:

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
```

Without it, `SESSION_COOKIE_SECURE = True` (Q3) is broken in subtle ways — Flask thinks the request is HTTP, so it considers the cookie domain "insecure", and any redirect to an absolute URL goes to `http://`, which nginx then 301s back to HTTPS, breaking POSTs that drop their body across the redirect.

I didn't ship the `ProxyFix` line in this PR because `app.py` is Darrell's slice. I left an explicit comment in `nginx.conf` calling out the dependency, and flagged it as a coord item.

**Artifact.** `nginx.conf` `proxy_set_header X-Forwarded-Proto $scheme;` plus the comment block immediately below it documenting the `ProxyFix` requirement on the Flask side.

---

*End of common_questions_aden.md.*
