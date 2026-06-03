# LLM Probe — Coordinator Deploy Pipeline Audit
**Role:** Coordinator
**Week:** 8
**Tool used:** Claude (Anthropic)
**Date:** June 3, 2026

---

## Prompt submitted

"I'm hardening the deploy pipeline of a small team project. Here's
our GitHub Actions release workflow and how we handle secrets and
docker-compose. Audit for: (a) secrets-leakage paths, (b) what a
hostile collaborator with commit access could do, (c) what's missing
from a production-grade deploy. Tell me what you'd change and why.

Stack: Flask + Postgres + nginx + gunicorn on a single EC2 instance.
Secrets: OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, SECRET_KEY,
DATABASE_URL loaded via python-dotenv from a gitignored .env file.
No GitHub Actions workflow yet. Deployment is currently manual:
SSH into EC2, git pull, docker compose up --build -d."

---

## LLM response

**Secrets leakage paths:**

The current manual deploy process requires a developer to SSH into
the EC2 instance and run docker compose up. The .env file lives on
the server and is gitignored, which is correct. However there is no
audit trail of who deployed what and when. If the .env file is
readable by all users on the instance, any process or user with
shell access can read the secrets.

The SECRET_KEY is currently set to dev-secret-not-for-production
in docker-compose.yml as a default. If someone runs docker compose
up without a .env file override, the app starts with a known weak
key. Session cookies signed with that key could be forged by anyone
who reads the compose file, which is committed to the repo.

If GitHub Actions is added later, secrets must go into GitHub
Actions secrets, not into the workflow YAML file itself. A common
mistake is interpolating a secret into a run: step that gets logged,
which leaks it into the Actions log. Even with secrets masked, avoid
echoing or printing them in any shell command.

**What a hostile collaborator with commit access could do:**

They could modify the Dockerfile to exfiltrate the .env file during
the build step, for example by adding a RUN curl command that sends
environment variables to an external server. Since the build runs on
the EC2 instance with access to the .env file, this would leak all
secrets silently.

They could add a malicious dependency to requirements.txt that
phones home or establishes a reverse shell when imported.

They could modify nginx.conf to remove rate limiting on auth
endpoints, making credential stuffing attacks easier, or to add a
proxy_pass to a route that bypasses authentication.

They could push a commit that sets DEBUG=True in the Flask config,
re-enabling the interactive debugger in production and creating a
remote code execution vulnerability.

All of these would survive a code review if the reviewer was not
specifically looking for them. The mitigation is branch protection
rules requiring at least one reviewer approval before anything
merges to main, combined with required status checks so CI must
pass before merge.

**What's missing from a production-grade deploy:**

There is no automated deploy pipeline. Every deploy requires manual
SSH access, which is slow, error prone, and leaves no audit trail.
A minimal GitHub Actions workflow triggered on git push --tags would
SSH into the EC2, pull the latest tag, and run docker compose up
--build -d. That is the minimum viable automated deploy for a
project at this scale.

There is no health check after deploy. After docker compose up
completes, there is no verification that the app is actually
serving requests. A post-deploy curl -k https://localhost check
that asserts a 200 response would catch a broken deploy immediately.

There is no rollback plan. If a deploy breaks production, the
current process is to SSH in and manually revert. Tagging releases
means you can roll back with git checkout <previous-tag> and
redeploy, but this is not documented anywhere.

The database has a named volume which means docker compose down
preserves data. However there are no automated backups. A pg_dump
on a cron job writing to S3 is the standard small-team solution.

---

## What I took away

The finding about the dev-secret-not-for-production default in
docker-compose.yml was the most actionable. That default should be
removed entirely so the app crashes on startup if SECRET_KEY is not
explicitly set, rather than silently running with a known weak key.
The strict os.environ approach we already use for OAUTH_CLIENT_SECRET
should apply to SECRET_KEY too.

The hostile collaborator scenarios were useful to think through as
coordinator. Branch protection with required reviews is the
structural fix, not any amount of config hardening. A malicious
Dockerfile change would bypass all the nginx and cookie hardening
we did this week. I will raise adding branch protection rules with
the team before Week 9.

The post-deploy health check suggestion is something I can add in
one line and should. It is the difference between knowing the deploy
worked and hoping it worked.

I pushed back on the suggestion to add a full secrets manager like
AWS Secrets Manager. For a three person student project on a single
EC2 instance, that is significant operational overhead for marginal
security gain. The .env file approach with strict environment
variable loading is appropriate at our scale.
