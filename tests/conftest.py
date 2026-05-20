"""Pytest discovery anchor — also ensures the repo root is on sys.path so
`from app import app, db` works from the tests/ directory."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlmodel import SQLModel

from app import app as flask_app, engine


@pytest.fixture
def app():
    flask_app.config.update(TESTING=True)

    with flask_app.app_context():
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)

    return flask_app