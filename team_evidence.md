# Assignment 8 — Part A: Team Evidence
**Team:** High Flyers
**Project:** Job Application Tracker
**Week:** 8
**Members:**
- Boma (Client-side / Frontend + Coordinator)
- Aden (DB-and-Security)
- Darrell (Server-side / Backend)

---

## Repo
GitHub organization: course-506-high-flyers
Repo: job-tracker
URL: https://github.com/course-506-high-flyers/job-tracker

---

## Links the rubric asks for

### 1. main with the stack committed
Link: https://github.com/course-506-high-flyers/job-tracker/tree/main

### 2. Merged hardening branch
Link: https://github.com/course-506-high-flyers/job-tracker/tree/hardening

### 3. Per-student personal hardening branches

| Owner | Branch | Status | Link |
|---|---|---|---|
| Boma | boma-hardening | Merged into hardening via PR #12 | https://github.com/course-506-high-flyers/job-tracker/tree/boma-hardening |
| Aden | aden-hardening | Merged into main via PR #14 | https://github.com/course-506-high-flyers/job-tracker/tree/aden-hardening |
| Darrell | darrell-hardening | Merged into hardening | https://github.com/course-506-high-flyers/job-tracker/tree/darrell-hardening |

---

## Per-slice ownership

| Layer | File(s) | Owner |
|---|---|---|
| Network edge — TLS termination, rate-limit zones, attack-path 404s | nginx.conf (server block + :443 block) | Aden |
| Network edge — security headers, /static/ block | nginx.conf (BOMA slot) | Boma |
| Python process — WSGI server config | gunicorn.conf.py | Darrell |
| Container topology | docker-compose.yml | All |
| Cert generation | scripts/make-dev-certs.sh | Aden |
| Dockerfile swap to gunicorn | Dockerfile | Boma/Darrell |
| Secrets hygiene | .gitignore | Aden |
| Production-stack docs | README.md | Boma |
| About page update | templates/about.html | Boma |
| Attack path tests | tests/test_attack_paths.py, attack_paths.json | Aden |

---

## PRs into hardening and main

| # | PR | Slice | Link |
|---|---|---|---|
| 12 | boma-hardening -> hardening | Boma frontend hardening | https://github.com/course-506-high-flyers/job-tracker/pull/12 |
| 13 | hardening -> main | Team stack merge | https://github.com/course-506-high-flyers/job-tracker/pull/13 |
| 14 | aden-hardening -> main | Aden DB/sec hardening recovery | https://github.com/course-506-high-flyers/job-tracker/pull/14 |

---

## How to verify the stack runs from main

1. Clone the repo and cd job-tracker
2. Copy the env template: cp .env.example .env
3. Populate .env with SECRET_KEY, DATABASE_URL, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET
4. Generate dev certs: mkdir -p certs && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -subj "/CN=localhost" && cp certs/cert.pem certs/fullchain.pem && cp certs/key.pem certs/privkey.pem
5. Bring up the stack: docker compose up -d
6. Verify: curl -k https://localhost returns HTTP 200
7. Verify HTTP redirects: curl -I http://localhost returns 301 to https

---

## Stack verification (performed on EC2 ip-172-31-54-242)

- docker compose up brings up nginx, app, and db cleanly
- nginx listens on 443 with a self-signed cert
- https://35.86.191.136 reaches the Flask app via nginx and gunicorn
- curl -k -I https://localhost returns HTTP/2 200 with all six security headers active
- HTTP to HTTPS redirect confirmed
- Attack paths (/.env, /wp-login.php, /admin) return 404

## Conflict-resolution log

One non-trivial conflict arose in nginx.conf during the merge sequence.
Boma's boma-hardening branch had a working nginx.conf with security
headers. Aden's aden-hardening branch had a comprehensive rewrite with
rate-limit zones, TLS hardening, and attack-path 404s, with a BOMA slot
reserved for Boma's headers. Resolution: Aden's version was kept as the
base, and Boma ported her security headers and static asset block into
the BOMA slot after PR #14 merged. Both contributions are preserved in
the final nginx.conf on main.
