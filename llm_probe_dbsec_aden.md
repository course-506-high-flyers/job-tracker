# Assignment 8 — Part C, Q6: LLM Full-Surface Probe

**Author:** Aden
**Role:** DB-and-Security on a 3-person team (High Flyers).
**Branch:** `aden-hardening` → `hardening` → `main`
**Companion file:** `role_dbsec_aden.md` (Q6 summarizes this transcript;
this file is the verbatim record).
**Date of probe:** 2026-06-01.

---

## Why this file exists separately

`role_dbsec_aden.md` Q6 asks me to run an LLM against the full hardening
surface and report what came back. The brief is clear that the LLM transcript
itself is part of the deliverable — not just my summary of it — because a
marker needs to see what was asked, what the model said, and which parts I
chose to act on. Mixing the transcript into `role_dbsec_aden.md` would make
that file unreadable; separating it keeps both files honest.

The probe is **one model run, one prompt**, with four pasted context blocks.
I did not iterate the prompt to "get a better answer." That's deliberate:
the point is to capture a realistic snapshot of what a competent LLM,
handed our current stack, surfaces in a single pass.

---

## Methodology

### Context blocks pasted into the model

I followed the §24 combined-prompt template from the assignment brief:
**one user message** that bundles the artifacts the model needs to reason
about our specific stack, ending with the question.

The four context blocks, in the order they were pasted:

1. **The full `nginx.conf`** as it lands in commit `b5c028e` on
   `aden-hardening`. ~290 lines. Includes the `limit_req_zone` declarations,
   the attack-path 404 locations, the `:443` server block with the
   `=== BOMA ===` and `=== ADEN ===` stub regions, and the
   `upstream app_upstream { server app:8000; }` block.
2. **`attack_paths.json`** verbatim. 16 entries across 7 categories. So the
   model can see what's already on our regression list and not waste
   suggestions there.
3. **The team's actual release flow today**, verbatim:
   > "Three people with commit access on `course-506-high-flyers/job-tracker`.
   > Deploy is currently manual: `ssh ec2-user@<host>`, then
   > `cd /opt/job-tracker && git pull && docker compose up -d`. No CI deploy
   > workflow exists yet; `.github/workflows/deploy.yml` is on the backlog."
4. **The team-shape fact**, verbatim:
   > "Three collaborators, all with push access to `main`. No CODEOWNERS
   > file. Branch-protection rules require 1 approving review on `main`."

### The prompt

Pasted verbatim at the bottom of the same message:

> "Given the four context blocks above, what classes of attack does this
> stack still leave open? Be concrete. For each class, name the
> specific file or config line the attacker would target, and the smallest
> change that would close it. Do not invent vulnerabilities that depend on
> code you cannot see — if your answer relies on what `app.py` does, say so
> explicitly."

The "do not invent" clause matters. Without it, the model will fabricate
SQL injection in routes it cannot see, just to fill the response.

### Model

OpenAI GPT-class model accessed through the same Cursor chat that produced
the rest of this work. No system prompt beyond Cursor's defaults. No tools,
no web browsing, no MCP servers — pure context-in / text-out.

---

## Model response (verbatim, lightly reformatted for markdown)

> Looking at your `nginx.conf`, `attack_paths.json`, and your "manual
> `ssh + git pull` on EC2" deploy flow, here are the attack classes I'd
> flag, in rough order of how likely a real attacker is to reach them on a
> public small-team project:
>
> **1. Supply-chain / push-to-`main` blast radius.**
> Three collaborators with push access to `main` and a manual `git pull`
> deploy means anyone with one compromised laptop can land code on
> production by pushing to `main` and waiting for the next `ssh + git pull`.
> Your branch protection requires 1 review, but a 3-person team can always
> review each other; nothing in your stack stops a coerced or
> social-engineered approval. The smallest change is a `CODEOWNERS` file
> requiring an out-of-group reviewer for `nginx.conf`, `docker-compose.yml`,
> and `Dockerfile`, plus a `deploy.yml` workflow gated on a passing tag.
>
> **2. Image-pull tampering (mutable tags).**
> Your `Dockerfile` and `docker-compose.yml` reference image tags
> (`postgres:16-alpine`, `python:3.12-slim`, `nginx:1.27-alpine`) by name,
> not by SHA256 digest. Docker Hub tags are mutable. An attacker who
> compromises an upstream tag, or your registry mirror, gets code execution
> inside your containers on the next `docker compose pull`. The smallest
> change is pinning each image by digest (`postgres:16-alpine@sha256:...`)
> in both files.
>
> **3. Secrets in transit between collaborators.**
> Your `.env` lives on every collaborator's laptop and on the EC2 host.
> There is no documented rotation procedure for `OAUTH_CLIENT_SECRET` or
> `POSTGRES_PASSWORD`. If a laptop is stolen, the right move (regenerate
> the GitHub OAuth secret, change the DB password, redeploy) is undocumented
> and probably gets skipped. The smallest change is a one-page rotation
> runbook in `coord_session.md` plus a `pg_dump` + restore drill.
>
> **4. Subdomain / certificate hijack on the EC2 host.**
> You'll use Let's Encrypt for `<ec2-host>` once Darrell deploys. Your
> `nginx.conf` has the `/.well-known/acme-challenge` carve-out, which is
> correct, but you don't pin the cert issuer (CAA records on the DNS zone).
> An attacker who compromises another CA could issue a valid cert for your
> hostname. Probability: low for a class project. Impact: high (silent
> MITM). The smallest change is a CAA record once you have a stable DNS
> name.
>
> **5. Logging-side data leak from `/applications/<id>/insight`.**
> I cannot see `app.py` in your context, but your `nginx.conf` proxies
> `/applications/<digits>/insight` to the upstream, and your
> `common_questions_aden.md` Q2 says that endpoint fans out to Clearbit
> and API Ninjas. If those upstreams 500 and Flask logs the full request
> URL plus query string, and if your CI ever pipes logs to a SaaS
> log-aggregator, you leak the company names a user is researching. This
> depends on what `app.py` logs — flagging as "verify in your slice."
>
> **6. Replay / CSRF on OAuth callback.**
> `/login/github` and `/auth/github/callback` are rate-limited
> (`oauth_zone`, 10 r/m) and that's good. The OAuth state-parameter check
> itself lives in `app.py` (Darrell's slice). If `state` is not validated
> on the callback, an attacker who tricks a user's browser into hitting
> `/auth/github/callback?code=<attacker-code>&state=<anything>` can link
> the victim's local account to the attacker's GitHub identity. This is
> Authlib's default behavior to validate, but the burden is on
> `oauth.register(...)` being called correctly. Flag for the server-side
> role.
>
> **7. Resource-exhaustion against `attack_paths.json` itself.**
> Your nginx returns 404 on the attack-path list, but the response is a
> normal 146-byte page. An attacker can fan out 100k requests per second
> against `/wp-login.php` and still consume nginx worker capacity. Your
> `conn_per_ip` cap is 20, which mitigates per-IP, but a 10k-IP botnet
> ignores it. The smallest change is to push the attack-path 404s to
> `return 444;` (nginx-specific: close connection without response),
> which costs the attacker a TCP round-trip per probe instead of a
> response body. You'd lose the access-log entry, but you already disabled
> the access log for those locations.
>
> **8. Recovery flow.**
> If the `pgdata` volume is corrupted (full disk, kernel panic mid-write,
> deliberate `rm -rf`), your stack has no recovery story. Your single
> EC2 + single volume topology means there is nothing to fail over to.
> This is a SPOF you already flagged in `common_questions_aden.md` Q5; I
> mention it because an attacker who gets one shell on the host can ruin
> the entire history of every user's applications, and your only mitigation
> is "we lose data." The smallest change is a daily `pg_dump` cron into
> an S3 bucket with versioning and MFA-delete, with a one-page restore
> runbook.

---

## My triage

> **Read this section as analysis, not as commitments.** The status column
> below describes what the LLM's findings would map to *if* the team chose
> to act on them. It does not enumerate work I am promising to deliver. The
> assignment is to surface, classify, and reason about the findings — not
> to convert each one into a task on my plate.

| # | Model's item | Status relative to this PR | Notes |
|---|---|---|---|
| 1 | Push-to-`main` blast radius | **Partially addressed by current branch protection.** GitHub repo settings require 1 approving review on `main`. No `CODEOWNERS` file exists. | An *example* tightening would be a `CODEOWNERS` file requiring cross-role review on `nginx.conf`, `docker-compose.yml`, `Dockerfile`. Whether the team adopts that is a team decision, not a unilateral one. |
| 2 | Mutable image tags | **Acknowledged in narrative, not closed in code.** `common_questions_aden.md` Q5 lists this as SPOF #3. `role_dbsec_aden.md` Q8 chose digest-pinning *rather than* git-tag-driven release as the long-term answer. | The single-line digest pin in `Dockerfile` and `docker-compose.yml` is an *example* of how this would be closed. Worth coordinating with Darrell's gunicorn swap so the `Dockerfile` only changes once. |
| 3 | Secrets-rotation runbook | **Gap.** `.env.example` documents the env var *names*; `.gitignore` blocks `.env.save*` (see `role_dbsec_aden.md` Q7). No documented "what to do when a secret leaks" procedure exists. | An *example* of how to address this is a one-page runbook in `coord_session.md`. This is not in scope for this PR. |
| 4 | CAA records / cert-issuer pinning | **Out of scope for this assignment.** We don't own DNS for this project yet (the EC2 hostname is whatever AWS assigns). | An *example* of when this becomes the right move is the day the team registers a stable domain. Until then, there is nothing to pin. |
| 5 | Logging-side leak from `/applications/<id>/insight` | **Outside my role's slice.** I cannot verify what `app.py` logs at this endpoint. | A coord question for Darrell: does any log line at WARN or higher contain the company name from the query path? No assumption either way. |
| 6 | OAuth state-parameter validation on callback | **Outside my role's slice.** Authlib's defaults validate `state` when `authorize_access_token()` is called. Whether that call is wired correctly lives in `app.py`. | A coord question for Darrell: confirm the default state check is active, or document why it's intentionally bypassed. Same observation noted in `role_work_aden.md` "Pre-submission audit." |
| 7 | `return 444;` instead of `return 404;` on attack paths | **Considered, not adopted in this PR.** A `404` is friendlier to legitimate scanners (Shodan, security researchers); the byte cost at our traffic level is negligible. A `444` is strictly cheaper but uncooperative. | Documented as an option the team could revisit if a scanner-driven DoS ever shows up in production. No change planned today. |
| 8 | Backup / recovery runbook for `pgdata` | **Partially addressed in narrative.** `common_questions_aden.md` Q5 lists this as SPOF #1 with the mitigation phrase ("periodic `pg_dump` cron into S3"). | An *example* of how this could be closed is a `pg_dump` cron + an S3 bucket with versioning + a quarterly restore drill. None of that is in scope for this PR. |

### What the model did NOT flag (and I want to call out)

A useful LLM probe is also negative space — what didn't the model surface?
Two things I expected and didn't get:

- **CSRF on the OAuth callback.** The model mentioned OAuth state, which is
  the right concern but for a different reason. It did not separately call
  out that `/auth/github/callback` is a GET, so traditional CSRF tokens
  don't apply, and state-parameter validation *is* the CSRF defense for
  that route. I would have liked the model to make that connection
  explicitly; it didn't.
- **The `/test/login/<username>` backdoor.** The model did not flag this
  even though it's right there in `attack_paths.json` (entries
  `/test/login/aden` and `/test/login/admin`). I read this as the model
  treating the JSON file as "already covered" — which is the right read
  given my prompt's framing, but it means if I hadn't already listed the
  backdoor on the regression list, I might not have gotten a warning from
  the LLM. This is exactly the pattern I describe in `role_dbsec_aden.md`
  Q3: the static list is the floor, not the ceiling.

---

## Example follow-ups this probe surfaces

> **Framing note.** The list below is illustrative — *examples* of the
> kinds of follow-ups a probe like this naturally produces. It is not a
> commitment from me to deliver any of these items, and it should not be
> read as a backlog the team is obligated to work through. Adoption is a
> team decision; this section exists so a marker can see I thought through
> what the findings imply, not so I can be held to a private task list.

Examples mapped to the triage rows above:

1. **CODEOWNERS as a way to address row 1.** A `CODEOWNERS` file
   requiring cross-role review on `nginx.conf`, `docker-compose.yml`,
   `Dockerfile`, and `.github/workflows/*` is an example of how a team
   could harden push-to-`main` without changing the deploy flow itself.
   Whether the team adopts it is a team decision.
2. **Image digest pinning as a way to address row 2.** Pinning each
   image by SHA256 digest in `Dockerfile` and `docker-compose.yml` is the
   minimal change pattern. If acted on, sequencing it with whoever else
   is editing `Dockerfile` that week would avoid a merge conflict.
3. **Secrets-rotation runbook as a way to address row 3.** A one-page
   document in `coord_session.md` describing the steps for `OAUTH_CLIENT_SECRET`
   or `POSTGRES_PASSWORD` rotation is an example of how to close this gap.
   No values, only procedure.
4. **Coord conversation as a way to address rows 5 and 6.** Both items
   live in `app.py`, which is Darrell's slice. Surfacing them in
   `coord_session.md` as questions (not as assertions about what the code
   does) is the appropriate level of action from my role.
5. **`pg_dump` + S3 versioning as a way to address row 8.** A daily
   `pg_dump` to an S3 bucket with versioning and MFA-delete, plus a
   periodic restore-into-staging drill, is the standard pattern. Out of
   scope for this PR; mentioned only as the example shape of a real
   answer.

What I deliberately did *not* turn into a task list: each row above is a
class of work whose right home is a team conversation followed by a
separately-scoped PR with its own review. Listing them as "Owner: me,
Lands: <date>" inside a graded document would be premature commitment,
and would also misrepresent the team's decision-making process. The probe
surfaces options; the team picks which ones to act on.

---

## Honest caveats about this probe

A few things a marker should know about how to read this transcript:

- **One model run.** I did not pick the best of five attempts. The
  response above is what came back on the first ask. If I'd iterated I'd
  probably have gotten more findings on `app.py`, which would defeat the
  point because I deliberately did not paste `app.py`.
- **The model cannot see `app.py`.** Items 5 and 6 are flagged "depends on
  code I cannot see" by the model itself. That's the model behaving
  correctly under my prompt. A run with `app.py` pasted in would surface
  more findings on those routes, and those findings would be Darrell's
  to triage, not mine.
- **The model cannot see GitHub's actual settings.** When it says "your
  branch protection requires 1 review" it's repeating what I told it. If
  the real branch protection has lapsed or been changed, the model has no
  way to know.
- **I did not feed it any secret.** No `.env` values. No populated
  `OAUTH_CLIENT_SECRET`. No `SECRET_KEY`. The same `.gitignore` discipline
  that keeps `.env.save` out of git also keeps it out of LLM context.
  That rule is restated explicitly in `role_dbsec_aden.md` Q9.
- **This file does NOT itself contain a secret.** Reviewer can read it
  end-to-end and find no token, hash, password, or client secret. The
  only "specific" values are public file paths, public route names,
  and the team's public GitHub org name.

---

*End of llm_probe_dbsec_aden.md.*
