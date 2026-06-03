# Team Evidence — Week 8 Hardening
**Team:** High Flyers
**Project:** Job Application Tracker
**Week:** 8

## Team repo main branch
https://github.com/course-506-high-flyers/job-tracker/tree/main

## Hardening branch
https://github.com/course-506-high-flyers/job-tracker/tree/hardening

## Personal hardening branches

| Member | Branch | Link |
|--------|--------|------|
| Boma | boma-hardening | https://github.com/course-506-high-flyers/job-tracker/tree/boma-hardening |
| Aden | aden-hardening | https://github.com/course-506-high-flyers/job-tracker/tree/aden-hardening |
| Darrell | darrell-hardening | https://github.com/course-506-high-flyers/job-tracker/tree/darrell-hardening |

## Stack verification
- docker compose up from boma-hardening brings up nginx, app, and db
- nginx listens on 443 with a self-signed cert
- https://35.86.191.136 reaches the Flask app via nginx and gunicorn
- curl -k https://localhost returns 200 from inside the EC2 instance
