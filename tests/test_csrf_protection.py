"""
tests/test_csrf_protection.py

Owner: Aden (DB-and-security) -- Week 7

Asserts that Flask-WTF CSRF protection is wired correctly and that
state-changing form POSTs without a valid token are rejected with HTTP 400.

This test deliberately re-enables WTF_CSRF_ENABLED so the assertion exercises
production-like behavior, in contrast to the other unit-test fixtures which
disable CSRF for convenience.
"""

import pytest
from sqlmodel import SQLModel

from app import app, engine


@pytest.fixture
def csrf_client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = True

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with app.test_client() as test_client:
        yield test_client


def test_register_post_without_csrf_token_is_rejected(csrf_client):
    response = csrf_client.post(
        "/register",
        data={"username": "csrfuser", "password": "Whatever123"},
    )
    assert response.status_code == 400


def test_login_post_without_csrf_token_is_rejected(csrf_client):
    response = csrf_client.post(
        "/login",
        data={"username": "csrfuser", "password": "Whatever123"},
    )
    assert response.status_code == 400


def test_applications_new_post_without_csrf_token_is_rejected(csrf_client):
    # CSRFProtect runs as a before_request hook, so the token check fires
    # before @login_required redirects. A tokenless POST must be rejected
    # with 400 regardless of auth state.
    response = csrf_client.post(
        "/applications/new",
        data={
            "company": "Acme",
            "position": "SWE",
            "status": "applied",
            "applied_date": "2026-05-27",
        },
    )
    assert response.status_code == 400


def test_applications_edit_post_without_csrf_token_is_rejected(csrf_client):
    response = csrf_client.post(
        "/applications/1/edit",
        data={
            "company": "Acme",
            "position": "SWE",
            "status": "applied",
            "applied_date": "2026-05-27",
        },
    )
    assert response.status_code == 400


def test_applications_delete_post_without_csrf_token_is_rejected(csrf_client):
    response = csrf_client.post("/applications/1/delete", data={})
    assert response.status_code == 400


def test_test_login_backdoor_returns_404_when_testing_disabled(csrf_client):
    # Regression guard: removing the TESTING check in app.test_login would be
    # a critical security regression. Toggle TESTING off and confirm 404.
    app.config["TESTING"] = False
    try:
        response = csrf_client.get("/test/login/anybody")
        assert response.status_code == 404
    finally:
        app.config["TESTING"] = True
