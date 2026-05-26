"""Pytest discovery anchor — also ensures the repo root is on sys.path so
`from app import app, db` works from the tests/ directory, and seeds the
strict environment variables that `app.py` requires at import time."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# app.py uses strict os.environ[...] reads for these, so they must be present
# before the module is imported. setdefault keeps any value the test file or
# the developer has already exported.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")
os.environ.setdefault("REMEMBER_COOKIE_SECURE", "false")

import pytest
from sqlmodel import SQLModel

from app import app as flask_app, engine


@pytest.fixture
def app():
    # CSRF is wired globally in production config but disabled here so the
    # BeautifulSoup/Flask-test-client tests can POST without rendering a token.
    # The dedicated CSRF assertions live in tests/test_csrf_protection.py.
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with flask_app.app_context():
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)

    return flask_app
