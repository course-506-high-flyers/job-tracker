"""
tests/test_db_security_contract.py

Owner: Aden (DB-and-security role) -- High Flyers, Week 6
Role: DB-and-security

Purpose: Verify the database schema and authorization behavior promised in
CONTRACTS.md. These tests are INITIALLY FAILING by design. They should pass
only after the job application schema, ownership rules, and login protection
are implemented.
"""

import os

# Configure the app for tests before importing app.py.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

import pytest
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel

from app import app, engine


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # CSRF disabled for this fixture so plain POSTs work; dedicated CSRF
    # rejection assertions live in tests/test_csrf_protection.py.
    app.config["WTF_CSRF_ENABLED"] = False
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with app.test_client() as test_client:
        yield test_client


def test_job_application_schema_matches_contract():
    """Aden owns the application tables, columns, FK, and duplicate guard."""
    tables = SQLModel.metadata.tables

    assert "job_applications" in tables
    assert "job_insights" in tables

    applications = tables["job_applications"]
    expected_application_columns = {
        "id",
        "user_id",
        "company",
        "position",
        "status",
        "applied_date",
        "notes",
        "job_url",
        "created_at",
        "updated_at",
    }
    assert expected_application_columns.issubset(applications.columns.keys())

    foreign_keys = {
        (fk.parent.name, fk.column.table.name, fk.column.name)
        for fk in applications.foreign_keys
    }
    assert ("user_id", "users", "id") in foreign_keys

    unique_column_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in applications.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("user_id", "company", "position") in unique_column_sets

    insights = tables["job_insights"]
    expected_insight_columns = {
        "id",
        "company",
        "rating",
        "review_count",
        "industry",
        "headquarters",
        "description",
        "fetched_at",
    }
    assert expected_insight_columns.issubset(insights.columns.keys())


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/applications"),
        ("get", "/applications/new"),
        ("post", "/applications/new"),
        ("get", "/applications/1"),
        ("get", "/applications/1/edit"),
        ("post", "/applications/1/edit"),
        ("post", "/applications/1/delete"),
        ("get", "/applications/1/insight"),
    ],
)
def test_application_routes_require_login(client, method, path):
    """All application routes must redirect anonymous users to login."""
    response = getattr(client, method)(path, follow_redirects=False)

    assert response.status_code in (301, 302)
    assert "/login" in response.headers["Location"]
    assert "next=" in response.headers["Location"]


def test_non_owner_gets_404_for_application_detail(client):
    """Ownership-restricted resources return 404 to prevent ID enumeration."""
    client.post(
        "/register",
        data={"username": "owner", "password": "OwnerPass123"},
        follow_redirects=True,
    )
    create_response = client.post(
        "/applications/new",
        data={
            "company": "Secret Corp",
            "position": "Security Engineer",
            "status": "applied",
            "applied_date": "2026-05-20",
            "notes": "Owned by another user",
            "job_url": "https://example.com/jobs/1",
        },
        follow_redirects=False,
    )
    assert create_response.status_code in (301, 302)

    application_id = create_response.headers["Location"].rstrip("/").split("/")[-1]

    client.post("/logout", follow_redirects=True)
    client.post(
        "/register",
        data={"username": "other", "password": "OtherPass123"},
        follow_redirects=True,
    )

    response = client.get(f"/applications/{application_id}")

    assert response.status_code == 404
