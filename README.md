# Job Application Tracker

## Team

**Team:** High Flyers  
**Members:**
- Boma (client-side)
- Aden (db-and-security)
- Darrell (server-side)
- Olga (Coordinator)
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

## Team Bylaws — Project Team-3 / High-Flyer

### Purpose

These bylaws define the roles, responsibilities, and working agreements between the four members of Project Team-3 / High-Flyer to ensure clear cooperation, shared responsibility, and consistent progress throughout the project.

### Roles

#### 1. Client-Side Member

The Client-Side member will:

- Lead all client-side (frontend / user interface) work and maintain steady progress.
- Ensure the client-side implementation integrates cleanly with the server- and database-side work.
- Send technical reminders related to client-side tasks, highlighting areas that need attention.
- Complete an equal share of the project work and ensure related tasks and files are properly compiled.
- Support the other team members whenever needed.

#### 2. Server-Side Member

The Server-Side member will:

- Lead all server-side (backend / API) work and maintain steady progress.
- Ensure the server-side implementation integrates cleanly with the client- and database-side work.
- Send technical reminders related to server-side tasks, highlighting areas that need attention.
- Complete an equal share of the project work and ensure related tasks and files are properly compiled.
- Support the other team members whenever needed.

#### 3. Database-Side Member

The Database-Side member will:

- Lead all database-side work, including schema design, queries, and data integrity.
- Ensure the database-side implementation integrates cleanly with the client- and server-side work.
- Send technical reminders related to database-side tasks, highlighting areas that need attention.
- Complete an equal share of the project work and ensure related tasks and files are properly compiled.
- Support the other team members whenever needed.

#### 4. Coordinator

The Coordinator will:

- Send meeting and scheduling reminders, and organize Zoom meetings.
- Take the lead in keeping the project on track.
- Safeguard the project's progress, files, and overall integrity.
- Ensure that all work is organized and documented through the GitHub repository.
- Complete an equal share of the project work and ensure related tasks and files are properly compiled.
- Support the other team members whenever needed.

### Shared Responsibilities

Each team member will:

- Contribute a fair share of the project and demonstrate a clear understanding of the problem being solved.
- Respect the views, ideas, working styles, culture, and preferences of the other members.
- Coordinate with members in adjacent roles to ensure the client-, server-, and database-side components work together as a unified system.

### Communication and Conduct

Each team member will:

- Be dependable and attend all scheduled meetings unless prior notice is given.
- Notify the team in advance if unable to attend a meeting.
- Respond to project communications within 24–48 hours.

### Weekly Submissions and Change Control

In line with the course requirements, the team will submit work on a weekly basis:

- Members will rotate weekly submissions in an agreed order, so that each member takes a turn submitting on behalf of the team.
- "Submitted work" refers to any work pushed to the `main` branch of the GitHub repository or turned in for grading.
- No member may change or alter submitted work without first notifying — and receiving agreement from — the member responsible for that work.
- If no response is received within 24 hours of a pending deadline, the change may proceed with a written note in the commit message and a follow-up notification to the responsible member.
- The final project will be submitted according to the instructions provided for the assignment.

### Conflict Resolution and Missed Deadlines

- If members disagree on a design or grading-relevant decision, they will first attempt to resolve the matter through direct discussion. If no agreement is reached, the team will decide by majority vote among the four members, with the Coordinator facilitating the discussion.
- If a tie occurs or the team cannot reach a resolution, the matter will be brought to the course instructor or teaching assistant for guidance.
- If a member is unable to meet a weekly submission deadline, they will notify the team as early as possible so that coverage can be coordinated and the project kept on schedule.

### Amendments

These bylaws may be amended at any time, provided all four members agree in writing (including written confirmation by email or GitHub commit message) to the proposed change.

---

*README v1.0 — Week 4 setup. Subject to revision during Week 5 skeleton walkthrough.*

## Running the production stack

The production stack runs nginx in front of gunicorn in front of Flask.

### Prerequisites
- Docker and Docker Compose installed
- A self-signed cert in `certs/` (gitignored — generate once with the command below)

### Generate the self-signed certificate (first time only)
```bash
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/key.pem \
  -out certs/cert.pem \
  -subj "/CN=localhost"
```

### Start the stack
```bash
docker compose up --build -d
```

### Verify it is running
```bash
curl -k https://localhost
```

The app is served at https://localhost via nginx on port 443.
nginx proxies to gunicorn on port 8000 inside the Docker network.
The database runs on the same Docker network and is not exposed publicly.

### Stop the stack
```bash
docker compose down
```

Note: `docker compose down -v` will also delete the database volume and all data.
