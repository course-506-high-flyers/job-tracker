# gunicorn.conf.py — production WSGI server config
# Binds to a port inside the Docker network; nginx proxies to it.

bind = "0.0.0.0:8000"

# Sync workers — appropriate for our app which is I/O bound but not
# high concurrency. One worker per CPU core plus one.
workers = 3
worker_class = "sync"

# Timeout — kill and restart a worker that takes longer than 30s
timeout = 30

# Logging
accesslog = "-"   # stdout
errorlog = "-"    # stderr
loglevel = "info"

# Security — don't expose gunicorn version in headers
server_header = False
