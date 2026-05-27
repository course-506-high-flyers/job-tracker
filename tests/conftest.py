"""Pytest fixtures for unit and Playwright E2E tests."""

import os
import socket
import sys
import threading
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlmodel import SQLModel
from werkzeug.serving import make_server

from app import app as flask_app, engine


@pytest.fixture
def app():
    flask_app.config.update(TESTING=True)

    with flask_app.app_context():
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)

    return flask_app


def _free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture
def live_server(app):
    port = _free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    try:
        yield SimpleNamespace(url=f"http://127.0.0.1:{port}")
    finally:
        server.shutdown()
        thread.join(timeout=5)
