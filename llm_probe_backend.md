# Week 8 LLM Probe — Backend Layer

## Prompt Used

I asked an LLM to review the backend production deployment for our Flask job tracker application.

Prompt summary:

"Review the Flask production deployment stack, including Gunicorn, nginx, Docker, session security settings, and environment variable handling. Identify production hardening improvements, security concerns, deployment risks, and anything that behaves differently under nginx and Gunicorn than under Flask's development server."

## Project Context

The project is a Flask-based job application tracker that includes:

* Username/password authentication
* GitHub OAuth authentication
* SQLModel database access
* CSRF protection
* Secure cookie configuration
* Docker deployment
* nginx reverse proxy
* Gunicorn WSGI server

The application was originally developed using Flask's built-in development server and later hardened for production deployment.

## Findings

The most significant finding was that the application was operating behind nginx but Flask was not yet proxy-aware.

nginx terminates HTTPS connections and forwards requests internally to Gunicorn over HTTP. Without additional configuration, Flask may incorrectly believe requests are arriving via HTTP rather than HTTPS.

Potential impacts include:

* Incorrect URL generation
* Incorrect redirect behavior
* OAuth callback issues
* Secure cookie handling inconsistencies
* Incorrect request scheme detection

The review also confirmed that Gunicorn is the correct production execution path and that Flask's development server should not be used for deployment.

## Change Implemented

Based on the review, I added ProxyFix to the Flask application:

```python
from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1
)
```

This allows Flask to properly interpret forwarded headers supplied by nginx.

## Validation

After implementing the change:

* Python compilation completed successfully
* Local test suite passed (80/80 tests)
* Docker stack built successfully
* nginx started successfully
* Gunicorn started successfully
* HTTPS requests returned HTTP 200 responses
* Secure cookies were issued correctly
* Security headers were present in responses
* Protected routes redirected correctly to login

## What I Learned

The most important lesson was that HTTPS termination at the proxy layer does not automatically mean Flask understands the original request was HTTPS.

Even when nginx is correctly configured, Flask must be explicitly told to trust proxy headers. ProxyFix bridges that gap and ensures that URL generation, redirects, OAuth flows, and secure cookie behavior all work correctly in a reverse-proxy deployment.

This exercise reinforced that production hardening is not only about replacing the development server. It also requires ensuring that application behavior remains correct when deployed behind production infrastructure components such as nginx and Gunicorn.
