# Week 8 Role-Specific Hardening — Backend

## Role

Backend / Python process layer

## 1. Why gunicorn, concretely

`flask run` and `python app.py` are development paths, not production paths. In our project, that matters for three concrete reasons.

First, Flask's development server is intended for local development and testing. It is useful while building features, but it is not designed to be the long-running production process for our application.

Second, `app.py` still contains a direct-run block with `debug=True`. That is acceptable for local development, but it should not be the production execution path. In the hardened deployment stack, Docker starts Gunicorn using `app:app`, which imports the Flask application object directly instead of executing the `if __name__ == "__main__"` block.

Third, Gunicorn provides a production-ready WSGI process manager. It can run multiple worker processes, restart failed workers, provide centralized logging through Docker, and operate behind nginx. In our deployment, nginx terminates HTTPS and proxies requests to Gunicorn on the internal Docker network.

## 2. Worker model

Our `gunicorn.conf.py` uses the following configuration:

```python
workers = 3
worker_class = "sync"
timeout = 30
```

For the current project, sync workers are appropriate because the application primarily handles short request/response interactions such as:

* User login
* GitHub OAuth authentication
* CRUD operations on job applications
* Company insight lookups

The application does not currently use websockets, streaming responses, or other high-concurrency workloads.

If the application later evolves to handle long-running requests, heavy external API traffic, or significantly higher concurrency, I would evaluate `gthread` workers or another concurrency model.

## 3. The WSGI contract

Flask is a WSGI application, which means a WSGI server such as Gunicorn can import and execute the Flask application object using a standard interface.

Our Docker deployment starts Gunicorn with:

```bash
gunicorn -c gunicorn.conf.py app:app
```

In this command:

* The first `app` refers to the Python module `app.py`
* The second `app` refers to the Flask application object

This separation is important because:

* nginx handles incoming HTTPS traffic
* Gunicorn manages Python worker processes
* Flask handles application routes and business logic

This architecture separates web serving responsibilities from application responsibilities and provides a cleaner production deployment model.

## 4. ProxyFix and X-Forwarded-Proto

In the production environment, nginx terminates HTTPS connections and forwards traffic to Gunicorn over HTTP inside Docker.

Without ProxyFix, Flask may incorrectly believe requests arrived over HTTP rather than HTTPS. This can affect:

* Secure session cookies
* Redirect behavior
* OAuth callback handling
* Request URL generation
* `request.scheme`
* `url_for(..., _external=True)`

To address this, I added:

```python
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
```

This allows Flask to trust a single layer of proxy headers from nginx, including `X-Forwarded-Proto`.

Although nginx supplies the forwarding headers, Flask must correctly interpret them. Therefore, ProxyFix belongs in the backend application layer.

## 5. LLM backend security probe reflection

I used an LLM to review the backend deployment configuration and identify production hardening opportunities.

The most useful observation was that Flask was not yet proxy-aware. Because nginx terminates HTTPS before forwarding requests internally, Flask requires ProxyFix to correctly determine the original request scheme and host information.

The review also confirmed that:

* Gunicorn is the correct production execution path
* The Flask development server should remain a development-only tool
* Strict environment variable loading improves reliability and security
* Security-related cookie settings are correctly configured
* Dockerized logging through Gunicorn simplifies operational visibility

The largest lesson from this exercise is that backend hardening involves more than replacing the Flask development server. The application must also correctly understand the proxy environment, enforce secure configuration defaults, and ensure production behavior remains consistent with user expectations.
