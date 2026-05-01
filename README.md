# Job Application Tracker

## Team

**Team:** High Flyers  
**Members:**
- Boma Okoli (server-side, client-side)
- Aden Abdulahi (db and Coordination)

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
Other bylaws for the High-Flyer Team:
Goal: This bylaw facilitates practical cooperation and responsibility sharing between the two members of Project team-3/Highflyer. 
Coordinator and DB-security Role: The coordinator and DB-security will send reminder emails, organize Zoom meetings, and take the lead to ensure project work is on the right track and progressive. Ensure the safety and security of the project and its progress.

Does one half of the project and ensures the project tasks and files are properly compiled. Support another member/s if it is necessary to help. 
Service-side and Client-side Role: The Service-side and Client-side will oversee and do service and client-side related work and ensure progressiveness of the project, and send remainder/s, if necessary, specifics on areas that need attention, and effective focus. Does one half of the project and ensures the project tasks and files are properly compiled. 
The Service-side and Client-side will ensure that all work is organized and documented, through collecting the work of others, and will ensure that the work submitted is not changed or altered unless notified who does that work and has agreed. Does one-third of the project and ensures the project tasks and files are properly compiled. Finally, submit the project assignment as per the instructions provided. Support other members if it is necessary to help. 
General Role: Each Team member will do a sufficient part of the project or group assignment and must make sure that she/he/they understand that the problem is solved clearly. Each member will ensure that they respect the views, ideas, methods of work, culture, and preferences of other team members. Each member will ensure that he/she/they is/are dependable and are available at the group meetings as best as possible or notify the team in advance and respond to communications accordingly.


*README v1.0 — Week 4 setup. Subject to revision during Week 5 skeleton walkthrough.*
