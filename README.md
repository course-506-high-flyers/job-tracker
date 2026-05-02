# Job Application Tracker

## Team

**Team:** High Flyers  
**Members:**
- Boma (server-side, client-side)
- Aden (db-and-security)

---

## Project

We are building **Option 3: Job Application Tracker** from the Week 4 lecture. The app lets users log and manage their job applications, automatically pulls in company context from an external API, tracks application stages, and sends follow-up reminders.

---

## The User

This app is for active job seekers who are applying to multiple companies at once and need a centralized, low-friction way to track where they stand. Their goal is to stay organized, never miss a follow-up, and get a clear picture of their pipeline at a glance.

---

## The MVP

Version 1 will support the following core features:

- GitHub OAuth login
- Add a job application (company name, role, date applied, notes)
- Auto-fetch basic company info via API and cache it per company
- Track application stage (Applied → Interview → Offer → Rejected / Accepted)
- Move applications between stages with a simple UI
- Basic follow-up reminder flagging (e.g., "no update in 7 days")

---

## External APIs

**Primary:** [Clearbit Company API](https://clearbit.com/) — provides company logo, description, and industry data by domain name. Free tier available with rate limits (~50 reqs/month on the free plan).

**Backup:** [API Ninjas Company Lookup](https://api-ninjas.com/api/company) or manual entry fallback, if API limits become a constraint, users can manually fill in company details, and we cache aggressively to minimize repeat calls.

We've noted that several company info APIs shifted to paid-only tiers in 2024–2025, so our architecture will treat the external API as optional enrichment rather than a hard dependency.

---

## Why This Project

We picked the Job Application Tracker because it strikes the right balance between technical challenge and real-world usefulness this is genuinely an app either of us might use. It exercises exactly the skills we want to develop: OAuth authentication, external API integration with a smart fallback strategy, relational data modeling with meaningful state transitions, and a UI that actually has to respond to user actions. The stage-tracking workflow also gives the client-side work real substance, not just static pages. If we build this well, it's something worth showing at the pitch.

---

*README v1.0 — Week 4 setup. Subject to revision during Week 5 skeleton walkthrough.*
