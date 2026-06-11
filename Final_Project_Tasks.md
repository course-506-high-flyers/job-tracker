# Final Project Tasks — Capstone Submission Notes

> **Temporary repo file.** This file will be deleted after the project is finally complete.
> Session notes from Aden's capstone wrap-up work (2026-06-10 through 2026-06-11).
> Companion local-only files (never push): `ADENDATA.md`, `MY_EC2.md`, `Final_Presentation_Note.md`

_Last saved: 2026-06-11 (end of session)_

---

## Assignment context

**Course:** Cloud Web Application Engineering with AI  
**Capstone due:** Fri Jun 12, 2026, 11:59pm  
**Worth:** 40 marks (Week 10 presentation already done — separate 10 marks)  
**Canvas submit (two items only):**
1. Live URL of deployed application
2. GitHub repo link with instructor access and visible PR history

**Non-negotiable:** app deployed and reachable; repo accessible with PR history intact.

**Production stack:** nginx → gunicorn → Flask → Postgres, Dockerized, HTTPS.

**Team:** High Flyers — Boma (frontend/coordinator), Darrell (backend), Aden (DB/security)

**Repo:** https://github.com/course-506-high-flyers/job-tracker

---

## Grading rubric (40 base marks)

| Criterion | Marks |
|-----------|------:|
| Architecture, separation of concerns & extensibility | 10 |
| Testing & verification | 8 |
| Git workflow & team integration | 6 |
| Documentation & technical communication | 5 |
| Live deployment | 4 |
| Functional frontend delivery | 4 |
| Persistence & data integration | 3 |

Bonus up to +4: originality (+2), usability/polish (+2).

---

## Conversation summary (2026-06-10 / 2026-06-11)

### 1. Local vs GitHub sync check
- Local `main` matched `origin/main` at start of session (`36f05ee`).
- Working tree clean; no uncommitted changes at that point.

### 2. `MY_EC2.md` explained
- Does **not** replace any repo file.
- Personal local-only substitute for editing `team_evidence.md`.
- `team_evidence.md` documents team EC2; `MY_EC2.md` documents Aden's personal box.
- In `.git/info/exclude` — must not be pushed (security: exposes SSH map).

### 3. Security risk of pushing `MY_EC2.md`
- No private key contents or `.env` secrets in file.
- But exposes public IP, SSH user, key filename, open ports, deploy commands.
- Repo is public — high reconnaissance risk. Do not push.

### 4. Cursor Agents usage (informational)
- Two usage pools: Auto+Composer (generous) vs API pool (Opus, etc.).
- Opus burns credits fastest; use for hard tasks only.
- Plan before coding; one clear job per chat; match model to task.

### 5. Capstone assignment summary
- Graded as software engineering deliverable, not feature count.
- Extensibility weighted heavily (10 marks).
- Presentation separate; team focusing on capstone Canvas submit only.

### 6. Per-person task lists created
- Initial list included presentation prep — removed after user confirmed presentation is done.
- Focus narrowed to Canvas submission only.

### 7. Aden's file-level edit guide
- `role_dbsec_aden.md` needed production evidence (lines 12–16, 48–57, 83–85).
- `e2e/db_security.md` Step 1 was PENDING.
- Agent SSH'd to Aden's EC2 and collected production probe evidence without user help.

### 8. Commits and deploys completed

| Commit | Message | What |
|--------|---------|------|
| `24e4f43` | docs(dbsec): add production EC2 evidence and close stale deploy notes | `role_dbsec_aden.md`, e2e, llm docs |
| `0ed1779` | docs: document team live URL for capstone submission | README, team_evidence, about.html, 5 more files |

### 9. Team URL agreed: `35.86.191.136`
- All tracked docs updated to team live URL.
- Aden's personal box `18.118.119.37` stays in `MY_EC2.md` only.
- Both URLs return HTTP 200 publicly.

### 10. Aden EC2 sync (personal box only)
- Pulled `main` through `24e4f43` then `0ed1779` on `18.118.119.37`.
- `docker compose up -d --build` — success.
- Attack-path probes: all 404; gunicorn log delta = 0.

### 11. Remaining work identified
- Team EC2 (`35.86.191.136`) sync to `0ed1779` — Darrell/Boma (Aden has no SSH key).
- Live OAuth on team URL — unverified in browser.
- Canvas submission — Boma.
- Stale e2e logs — Darrell/Boma.

---

## Key decisions

### Team live URL (Canvas)
**`https://35.86.191.136`**

| Host | Role | Aden SSH | Public HTTP |
|------|------|----------|-------------|
| `35.86.191.136` | Capstone submission | No key | 200 |
| `18.118.119.37` | Aden personal deploy | Yes | 200 |

### Files that must never be committed
- `MY_EC2.md` — SSH/deploy attack map
- `ADENDATA.md` — personal session log
- `Final_Presentation_Note.md` — gitignored

---

## What Aden completed

| Task | Status |
|------|--------|
| Production evidence in `role_dbsec_aden.md` | Done (`24e4f43`) |
| EC2 sync on personal box | Done |
| Team URL in all tracked docs | Done (`0ed1779`) |
| README live URL + architecture + work split | Done |
| `team_evidence.md` capstone live URL link | Done |
| `templates/about.html` live deployment section | Done |
| Commits pushed to GitHub | Done |

---

## Remaining tasks — per person

### Boma (P0 = blocks submission)

| Priority | Task |
|----------|------|
| **P0** | Submit Canvas: `https://35.86.191.136` + GitHub repo link |
| **P0** | Frontend smoke test on team URL (login → CRUD → stage → logout) |
| **P1** | Retest + update `e2e/client_side.md` Step 11 (L177–191) — still says insight "not yet live" |
| **P2** | Confirm instructor repo access (public repo may suffice) |

**Done:** README, about.html, team_evidence live URL, role frontend docs.

### Darrell (P0 = blocks grader login)

| Priority | Task |
|----------|------|
| **P0** | SSH team EC2 `35.86.191.136`, `git pull --ff-only origin main`, `docker compose up -d --build` |
| **P0** | Live GitHub OAuth on `https://35.86.191.136` |
| **P0** | EC2 `.env` OAuth callback = `https://35.86.191.136/auth/github/callback` |
| **P1** | CRUD + persistence test on team box |
| **P1** | Verify `/applications/<id>/insight` end-to-end |
| **P1** | Update `e2e/db_security.md` L80 (Steps 6–8 still BLOCKED) |
| **P1** | Update `e2e/client_side.md` Finding 1 (L181–191) |
| **P2** | Run `pytest` once and note result |

**Done:** OAuth routes, gunicorn, ProxyFix, backend role docs.

### Aden

| Priority | Task |
|----------|------|
| **P0** | Browser OAuth test on `https://35.86.191.136` (5 min) |
| **P2** | Optional: help Darrell update e2e ownership logs |
| **P2** | Optional: `common_questions_aden.md` verbatim headings (L7–8) |

**Done:** All doc commits, personal EC2 sync, security evidence.

### Shared (all three)

| Task | Owner | Status |
|------|-------|--------|
| Team URL agreed | Team | Done |
| Docs on GitHub at `0ed1779` | Aden | Done |
| Team EC2 = `main` | Darrell/Boma | **Unknown** |
| Full live demo works | All | **Needs browser test** |
| Canvas submitted | Boma | **Pending** |

---

## Stale docs still open

| File | Issue | Owner |
|------|-------|-------|
| `e2e/client_side.md` L177–191 | Insight route marked pending | Boma + Darrell |
| `e2e/db_security.md` L80 | Steps 6–8 BLOCKED | Darrell |

---

## Operational reference

### Team EC2 sync (Darrell/Boma)
```bash
ssh ubuntu@35.86.191.136
cd ~/job-tracker
git fetch origin
git pull --ff-only origin main
docker compose up -d --build
docker compose ps
curl -k -I https://localhost
```

### Browser OAuth checklist
1. Open `https://35.86.191.136`
2. Accept self-signed cert warning
3. Sign in with GitHub
4. Land on `/applications`
5. If fail: fix OAuth callback URL in GitHub app + EC2 `.env`

### Minimum viable submission
1. Darrell/Boma: team EC2 on latest `main`
2. OAuth works on team URL
3. Boma: Canvas submit

---

## Git history (this session)

```
0ed1779 docs: document team live URL for capstone submission
24e4f43 docs(dbsec): add production EC2 evidence and close stale deploy notes
36f05ee Add local-only presentation build script and gitignore rules.
```

---

## Current status snapshot (end of 2026-06-11)

| Item | State |
|------|-------|
| GitHub `main` | `0ed1779` |
| Team live URL | `https://35.86.191.136` |
| Team URL HTTP | 200 |
| Aden personal EC2 | Synced, stack Up |
| Team EC2 sync | Unknown — Darrell/Boma |
| Presentation | Done |
| Canvas submission | **Pending — due Fri Jun 12 11:59pm** |

---

## Copy-paste for team

**To Boma:**
> Capstone due Fri 11:59pm. Team URL is `https://35.86.191.136`. README and team_evidence are updated on GitHub (`0ed1779`). Please submit Canvas (URL + repo link) and run a quick browser smoke test.

**To Darrell:**
> Please pull latest `main` on team EC2 (`35.86.191.136`) and rebuild. Confirm GitHub OAuth works at `https://35.86.191.136` with callback `https://35.86.191.136/auth/github/callback`. Also retest insight route and update stale e2e logs in `e2e/client_side.md` and `e2e/db_security.md`.

---

*This file will be deleted after the project is finally complete.*

*End of Final_Project_Tasks.md*
