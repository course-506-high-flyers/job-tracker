# Assignment 8 — Part C, Q3: LLM Conversation on Attack-Path Test Strategies

**Author:** Aden
**Role:** DB-and-Security on a 3-person team (High Flyers).
**Branch:** `aden-hardening` → `hardening` → `main`
**Companion file:** `role_dbsec_aden.md` (Q3 summarizes the strategy
triage; this file is the verbatim conversation + the deeper write-up
the brief asks for).
**Date of conversation:** 2026-06-01.

---

## Why this file exists separately

`role_dbsec_aden.md` Q3 ships a five-row triage table comparing test
strategies. The brief is explicit that the deeper version belongs in a
**separate `llm_strategies.md`** (in this repo, `llm_strategies_aden.md`)
that contains *the conversation itself* plus a write-up of what
strategies exist, why pytest-parametrize was chosen, what it doesn't
catch, and what I would add if the security stakes were higher.

Mixing the conversation into `role_dbsec_aden.md` would have made that
file unreadable; separating it keeps both files honest. The triage table
in `role_dbsec_aden.md` Q3 is the executive summary; this file is the
working notes.

---

## Methodology

### Setup

One model run. One prompt. No iteration to "get a better answer." I
pasted the relevant artifacts from this repo as context, asked the
strategy question once, and triaged the result. This mirrors the
discipline used for `llm_probe_dbsec_aden.md` (Q6) — one-pass probes
make for honest triage; iterated prompts make for confirmation bias.

### Context blocks pasted into the model

1. **`tests/test_attack_paths.py`** verbatim (the parametrized pytest
   approach I shipped — so the model knows what "the provided approach"
   actually does in code).
2. **`attack_paths.json`** verbatim (16 entries, 7 categories — so the
   model can see the static-list shape).
3. **A one-sentence project description:** "Flask + SQLModel + Postgres
   in docker-compose, behind nginx on EC2, three-person team, public
   internet exposure."

### The prompt

Pasted at the bottom of the same message:

> "The test above uses pytest with a parametrized fixture of known-bad
> paths. What other strategies exist for testing the same problem
> (attack-path absorption at the web edge)? For each strategy you name,
> tell me: (a) what it catches that the parametrized fixture doesn't,
> (b) what it misses that the parametrized fixture catches, (c) when it
> is the right tool versus when it is overkill or overfitted to a
> different problem class. Do not invent vulnerabilities specific to my
> code — answer at the level of test-strategy categories."

The "do not invent vulnerabilities" clause keeps the model honest. Same
constraint I used for the Q6 full-surface probe.

---

## Model response (verbatim, lightly reformatted for markdown)

> Your pytest parametrize approach is a known-list regression test: cheap,
> deterministic, lives in CI, and answers "did someone delete one of my
> nginx block rules?" in 2.5 seconds. It is the *floor*, not the
> ceiling. Here are the other strategy categories you could layer on top
> and what each one buys you:
>
> **1. DAST scanner integration (OWASP ZAP, Burp Suite Professional,
> Acunetix, Detectify).**
> What it does: spider your live site, then run an active-scan ruleset
> against discovered endpoints. ZAP ships ~50 active rules out of the
> box (SQLi, XSS, header checks, directory listing, etc.). Burp's
> equivalent is the Active Scan v2 engine.
> Catches what your fixture doesn't: anything off the static path list.
> If a future endpoint `/admin/users/export.csv` ships with a directory
> traversal flaw, your fixture is silent; ZAP's active scanner will
> probe `?file=../../etc/passwd` automatically.
> Misses what your fixture catches: the *project-specific* paths — your
> `/test/login/aden` backdoor, your `/.env.save` near-miss. A
> general-purpose scanner has no concept of those.
> Right tool when: pre-release sweep against a staging environment with
> known-test data, run manually once per major release.
> Overkill when: every commit. ZAP needs a JVM runtime in CI and
> produces a non-trivial false-positive rate on Flask framework
> boilerplate. Gating every commit on it produces flaky CI fast.
>
> **2. Template-driven scanners (nuclei, jaeles).**
> What it does: thousands of YAML templates describe specific known
> vulnerabilities; the scanner runs the matching ones against your
> target. Different model from ZAP — pattern-matching against a curated
> database, not spider-then-fuzz.
> Catches what your fixture doesn't: CVE-shaped vulnerabilities in
> common stack components (Apache `mod_status` exposure, nginx
> `merge_slashes off` edge cases, exposed `.well-known/security.txt`,
> WordPress version disclosure). The community template count for
> `exposed-env`-class issues alone is in the hundreds.
> Misses what your fixture catches: same gap as ZAP — your repo's
> project-specific cases (the `/test/login/` backdoor, the
> `/.env.save` paths from your repo's clone history). Nuclei has no
> way to know those exist.
> Right tool when: once-per-release sweep against staging or against
> the live host, especially before announcing a public URL.
> Overkill when: every commit. Same flakiness profile as ZAP.
>
> **3. Path / parameter fuzzers (wfuzz, ffuf, AFL-style mutation).**
> What it does: dictionary-based or mutation-based path enumeration.
> Given `/users/{id}`, try every integer in 0..10000, every UUID, every
> `../`, every null-byte injection.
> Catches what your fixture doesn't: unknown endpoints that exist but
> aren't in your route table (forgotten admin panels, dev-only routes
> that leaked into prod, parameter pollution).
> Misses what your fixture catches: the assertion that *specific
> documented paths* return safe statuses. A fuzzer's "I tried 100k
> paths and found nothing weird" doesn't match the test report
> structure your assignment is expected to produce.
> Right tool when: red-team engagements where you don't have the source
> code. Honest answer: rare for a 3-person class project.
>
> **4. Behavioral tests (rate limit verification, lockout assertions,
> session-cookie flag assertions).**
> What it does: drive specific behavior at the endpoint level and
> assert the response matches the security policy. Example: POST six
> failed `/login` attempts from one IP in one minute, assert the 6th
> returns 429.
> Catches what your fixture doesn't: misconfiguration of *active*
> defenses. Your rate-limit zones are configured at 5 r/m on
> `/login` — but if someone bumps `burst` from 3 to 30, your static
> path list still passes (it just GETs the URL once). A behavioral
> test catches the regression.
> Misses what your fixture catches: the absorption claim itself. A
> behavioral test for the rate limit doesn't care whether nginx
> *itself* serves the 404 or Flask does.
> Right tool when: complement to the static list, not replacement. The
> two answer different questions.
>
> **5. WAF / CDN logs as a passive signal.**
> What it does: rather than running a test, parse the production
> access log for what's *already* being attempted against the live
> site. Bots are scanning you all day.
> Catches what your fixture doesn't: the long tail of paths real
> attackers are probing. Today's botnet may be probing
> `/.aws/credentials` — that's not in your static list, but the access
> log will show 47 hits from 30 IPs in one hour, and you can add it.
> Misses what your fixture catches: anything that hasn't been probed
> yet. Passive signals lag the threat by definition.
> Right tool when: production has been running for at least a week and
> you want to grow the static list with empirical evidence.
> Useless before deploy.
>
> **6. Static analysis of the nginx config itself
> (`gixy`, `nginx-config-check`, custom AST walks).**
> What it does: parse `nginx.conf`, flag missing `add_header` lines,
> overly permissive locations, missing `return 444;` on attack paths,
> default-server traps.
> Catches what your fixture doesn't: misconfiguration that wouldn't
> show up in any black-box test — e.g., a `location /` block that
> *follows* the attack-path 404 block but accidentally re-exposes
> `/admin` via a `proxy_pass` rewrite.
> Misses what your fixture catches: the runtime behavior. A config can
> parse and lint cleanly and still 404 the wrong things if the
> upstream is unreachable.
> Right tool when: pre-commit, alongside `nginx -t`.
>
> **7. Production-canary attack-path replay.**
> What it does: replay last week's attacker probes (from your access
> log) against this week's deploy, assert each one still 404s.
> Catches what your fixture doesn't: drift in your real attack surface
> over time. Your static list grows from a curated initial seed; the
> canary keeps it pinned to reality.
> Misses what your fixture catches: anything that's been a 404 for
> longer than your retention window.
> Right tool when: you have access logs from production. Not before
> first deploy.
>
> **Summary read.** Your parametrized pytest is the cheapest piece of
> the whole strategy stack: deterministic, fast, runs without
> infrastructure, and answers the regression question. The other
> categories don't replace it — they complement it at different points
> in the development lifecycle (commit-time vs. release-time vs.
> post-deploy) and against different threat models (regression vs.
> discovery vs. drift).

---

## My triage

> **Read this section as analysis, not as commitments.** The columns
> below describe what each strategy buys and what it costs; whether the
> team adopts any of them is a future team decision, not a promise from
> this document.

| # | Strategy | Adopted in this PR? | Why or why not |
|---|---|---|---|
| 1 | pytest parametrize (the brief's provided approach) | **Yes.** | The floor of the strategy stack. Cheap, deterministic, lives in our existing pytest harness, runs in 2.5s in CI, no extra infrastructure required. `tests/test_attack_paths.py` ships 33 assertions today. |
| 2 | DAST scanner (ZAP / Burp) | No (considered, not shipped) | Requires JVM runtime in CI plus a tuning pass to manage false positives on Flask framework boilerplate. Worth running manually once before submission as a cross-check; would not gate every commit on it. |
| 3 | Template-driven scanner (nuclei) | No (considered, not shipped) | Same flakiness profile as ZAP at commit-gate scale. The template categories (`exposed-env`, `wordpress-detect`) would extend coverage past my static list; mentioned in `role_dbsec_aden.md` Q3 as "will run once manually" if we ever stand up a staging environment. |
| 4 | Path / parameter fuzzer (wfuzz, ffuf) | No (rejected) | The assignment expects a *regression suite a marker can read*. A fuzzer's "no findings against 100k paths" doesn't match that shape. Right tool for red-team engagements without source access; wrong tool for a class project where reviewers want to see exactly which 16 paths I tested. |
| 5 | Behavioral tests (e.g., 429 verification) | Considered, not shipped | Verifies *active* defenses (rate limits, lockouts), not absorption. `role_dbsec_aden.md` Q3 documents this as an example shape if the team ever picks it up — kept separate from `test_attack_paths.py` because the rate-limit test needs POSTs and clean rate windows, a different flakiness profile from read-only GETs. |
| 6 | WAF / access-log mining as a passive signal | Not applicable yet | We have no production traffic. The strategy is named here so a future-me reading this file knows the option exists once Darrell deploys and we accumulate one or two weeks of real access logs. |
| 7 | Static analysis of nginx config (`gixy`) | No (considered, not shipped) | A reasonable pre-commit hook layer. Out of scope for this assignment; flagged as the example shape if config drift ever becomes a recurring problem. |
| 8 | Production-canary replay | Not applicable yet | Requires production access logs from at least one prior deploy. Listed for completeness. |

---

## My own write-up (the four beats the brief asks for)

### What strategies exist

The list above gives the eight I'd put on the table for a project at our
scale. They sort into three categories by *when* in the development
lifecycle they run, which is the most useful axis for thinking about
them:

- **Commit-gate (must be cheap, deterministic, no infra):** pytest
  parametrize (#1), nginx static analysis (#6).
- **Release-gate (run once per release, can be slower):** DAST scanners
  (#2), template-driven scanners (#3), behavioral tests (#4).
- **Post-deploy (require production signal):** WAF / access-log mining
  (#5), production-canary replay (#7), fuzzers (#3 in a red-team
  context).

A second useful axis is *what threat model they answer*:

- **Regression** ("did someone delete a config line that was protecting
  me?"): pytest parametrize, nginx static analysis, behavioral tests.
- **Discovery** ("is there a category of attack I haven't thought of
  yet?"): DAST scanners, template-driven scanners, fuzzers.
- **Drift** ("is my static list still aligned with what real attackers
  are doing?"): WAF / access-log mining, production-canary replay.

The pytest parametrize approach is firmly in the
**commit-gate × regression** quadrant. That's its job, and that's why
it ships in this PR.

### Why the provided approach (pytest parametrize) is what it is

Three properties make it the right tool for the regression quadrant:

1. **Determinism.** The same input list produces the same test count
   and the same pass/fail outcome on every run. CI doesn't tolerate
   flaky tests; the moment one is flaky, people start to ignore the
   *real* failures it eventually reports. A scanner-based test against
   a live target is inherently flaky — the target might be slow, the
   scanner might find different "findings" on different runs.
2. **Readable failures.** If `test_attack_path_returns_safe_status[/.env.save]`
   fails, the marker (or a future contributor) knows exactly which
   path regressed. A scanner that reports "47 issues found, see HTML
   report" is not a debugging surface.
3. **Documentation of intent.** The static list *is* the regression
   spec. Anyone reading `attack_paths.json` knows what the project
   considers in scope for absorption. A fuzzer's coverage is implicit
   in its dictionary; it does not communicate intent.

### What it doesn't catch

The honest gaps, mapped onto the model's response:

- **Unknown paths.** The static list grows from a curated initial seed.
  If a botnet starts probing `/.aws/credentials` tomorrow and I haven't
  added it, my test passes and the path silently traverses Flask. The
  remedy is the access-log-mining strategy (#5), which requires
  production traffic.
- **Misconfigured rate limits.** If someone bumps `burst` from 3 to 30
  in `nginx.conf` `auth_zone`, my `test_attack_paths.py` still passes
  — it doesn't drive behavior, it only checks GET responses. The
  remedy is the behavioral test strategy (#4); the cost is flakiness.
- **Application-layer leakage at allowed paths.** My test asserts that
  the response body for an attack path contains none of `{traceback,
  werkzeug, sqlalchemy, psycopg2, secret_key, postgres://, postgresql://}`.
  That's a small safety net. If a real route — say
  `/applications/<id>/insight` — ever leaks one of those strings on a
  legitimate request, my test never runs against that route. The
  remedy is a separate response-body-hygiene test scoped to live
  routes.
- **Anything off the path axis.** Header injection, parameter
  pollution, response-splitting, HTTP smuggling — none of these are in
  scope for an absorption test. They're in scope for the DAST scanner
  strategy (#2).

### What I'd add if security were higher stakes

Three additions, in priority order:

1. **A behavioral rate-limit test** (strategy #4 above), even with its
   flakiness cost. The 5 r/m + burst 3 configuration on `auth_zone` is
   the closest thing in our stack to a "credential-stuffing wall" —
   without a behavioral test, that wall can be silently turned off by
   anyone editing `nginx.conf`. The strategy belongs in a separate
   test file (`tests/test_rate_limit.py`) with a longer pytest timeout
   and an explicit rate-window-reset fixture. Not in scope for this
   PR; example shape only.
2. **A weekly nuclei scan against the live host** (strategy #3 above),
   run as a scheduled GitHub Actions job rather than on every PR. The
   `exposed-env`, `dotgit-detect`, and `wordpress-detect` template
   categories alone would catch what my static list doesn't think to
   ask. Output: a Slack ping (or Linear ticket) when a new finding
   appears, not a CI red-light. The point is to *grow* the static
   list, not to fail builds.
3. **Access-log mining once production traffic exists** (strategy #5
   above). A small script that parses last week's nginx access log
   for 404-with-suspicious-substring patterns, deduplicates by path,
   and surfaces "candidate new attack paths" for review. Manual review
   before adding to `attack_paths.json` — never auto-add, since attacker
   creativity outpaces curation.

What I would explicitly *not* add even at higher security stakes:

- **Fuzzing in CI.** The signal-to-noise ratio is wrong for a
  regression suite. Fuzzers belong in red-team engagements, not
  commit-gate.
- **A WAF replacing the static list.** A WAF is a complement to the
  list, not a substitute. Outsourcing the absorption decision to a
  vendor's ruleset hides what's actually being blocked.

---

## Honest caveats about this conversation

- **One model run.** The response above is what came back on the first
  ask. No iteration to "get a better answer."
- **The model could not see `app.py` or `nginx.conf`.** I deliberately
  did not paste the full nginx config — the question was about test
  *strategies* at the category level, not about how my specific config
  performs. If I had pasted `nginx.conf`, I would have gotten more
  config-specific suggestions and fewer strategy-category suggestions,
  which would have defeated the prompt.
- **The model named eight strategies; I triaged eight.** I did not
  silently drop ones I disliked. The triage table in
  `role_dbsec_aden.md` Q3 is the executive summary of five rows
  because the other three (#5 WAF mining, #6 static analysis, #7
  canary replay) require operational context (production traffic,
  pre-commit hook infrastructure) that doesn't exist for our project
  yet. They're documented here, not summarized in Q3, by design.
- **No secrets in this transcript.** Same `.gitignore`-grade discipline
  as `llm_probe_dbsec_aden.md`: no `.env` values, no `OAUTH_CLIENT_SECRET`,
  no `SECRET_KEY` hex, no DB password. The transcript can be read
  end-to-end and find nothing rotatable.

---

*End of llm_strategies_aden.md.*
