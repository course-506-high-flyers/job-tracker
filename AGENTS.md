# AGENTS.md — AI Assistance Log

This file documents how AI tools were used in the development of the Job Tracker project,
in accordance with the course policy on AI assistance.

## Tools Used
- Claude (Anthropic) — architecture guidance, debugging, code review, documentation
- GitHub Copilot — inline code suggestions during development

## How AI Was Used

### Boma (Client-side / Coordinator)
- Used Claude to debug Bootstrap template structure and navbar layout
- Used Claude to review and clean up Jinja2 template inheritance
- Used Claude to draft and refine README and project documentation
- Used Claude for deployment troubleshooting (Docker, nginx, EC2 configuration)
- Used Claude to coordinate team task management and submission checklist

### Aden (DB / Security)
- Used Claude to review SQLModel schema design and migration strategy
- Used Claude to reason through session hardening and CSRF protection patterns
- Used AI assistance for nginx TLS configuration and rate limiting rules
- Used Claude to review attack path documentation and security test coverage

### Darrell (Server-side / Flask / OAuth)
- Used GitHub Copilot for Flask route scaffolding
- Used Claude to debug GitHub OAuth callback flow and session handling
- Used Claude to design the company insights API integration and fallback strategy
- Used AI assistance for gunicorn/WSGI production configuration

## Policy
All AI-generated code and suggestions were reviewed, understood, and tested by the
team member responsible for that area before merging. No code was merged that a
team member could not explain. AI was used as a pair-programming assistant, not
as a code generator operating without oversight.

## Note on Scope
AI assistance was used throughout the project as expected and encouraged by the
course. The team takes full responsibility for all design decisions, architecture
choices, and the correctness of the delivered system.
