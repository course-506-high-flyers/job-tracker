import os
import sys
import tempfile
import threading
from dataclasses import dataclass

import pytest
from sqlmodel import SQLModel
from werkzeug.serving import make_server


@dataclass
class LiveServer:
    url: str


@pytest.fixture(scope="session")
def live_server():
    db_fd, db_path = tempfile.mkstemp(prefix="job_tracker_e2e_", suffix=".sqlite")
    os.close(db_fd)

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "e2e-secret-key"
    os.environ["OAUTH_CLIENT_ID"] = "e2e-oauth-client-id"
    os.environ["OAUTH_CLIENT_SECRET"] = "e2e-oauth-client-secret"
    os.environ["SESSION_COOKIE_SECURE"] = "false"
    os.environ["REMEMBER_COOKIE_SECURE"] = "false"
    os.environ["PERMANENT_SESSION_LIFETIME_SECONDS"] = "1800"
    os.environ["REMEMBER_COOKIE_DURATION_SECONDS"] = "1800"

    # Ensure app.py sees e2e env vars even if previously imported.
    if "app" in sys.modules:
        del sys.modules["app"]

    from app import app as flask_app, engine

    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=True)

    with flask_app.app_context():
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)

    server = make_server("127.0.0.1", 0, flask_app)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield LiveServer(url=f"http://{host}:{port}")
    finally:
        server.shutdown()
        thread.join(timeout=5)
        if os.path.exists(db_path):
            os.remove(db_path)
