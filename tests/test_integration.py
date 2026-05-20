"""
tests/test_integration.py

Owner: Boma Okoli (Coordinator) — High Flyers, Week 6
Role: Coordinator

Purpose: End-to-end integration test that exercises all three roles' work.
This test only passes when server-side routes, db models (Flask-Login),
and client-side templates are all implemented and working together.

All tests in this file are INITIALLY FAILING by design.
"""

import pytest
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def registered_client(client, app):
    """Register and log in a user, return the client."""
    with app.app_context():
        client.post("/register", data={
            "username": "integration_user",
            "email": "integration@example.com",
            "password": "IntegPass123",
            "confirm_password": "IntegPass123",
        }, follow_redirects=True)
        client.post("/login", data={
            "username": "integration_user",
            "password": "IntegPass123",
        }, follow_redirects=True)
    return client


# ---------------------------------------------------------------------------
# Full CRUD integration flow
# ---------------------------------------------------------------------------

class TestFullApplicationFlow:
    """
    Tests the complete user journey:
    register → login → create → list → view → edit → delete
    This only passes when all three roles have shipped.
    """

    def test_register_and_login_flow(self, client):
        """User can register and immediately use the app."""
        resp = client.post("/register", data={
            "username": "flowuser",
            "email": "flowuser@example.com",
            "password": "FlowPass123",
            "confirm_password": "FlowPass123",
        }, follow_redirects=True)
        assert resp.status_code == 200
        # After registration, applications link should be visible
        soup = BeautifulSoup(resp.data, "html.parser")
        nav = soup.find("nav")
        assert nav is not None
        links = [a["href"] for a in nav.find_all("a", href=True)]
        assert "/applications" in links

    def test_create_application_full_flow(self, registered_client):
        """Create an application and verify it appears on the list page."""
        # Create
        resp = registered_client.post("/applications/new", data={
            "company": "Integration Corp",
            "position": "Full Stack Engineer",
            "status": "applied",
            "applied_date": "2026-05-15",
            "notes": "Integration test note",
            "job_url": "https://integrationcorp.com/jobs/1",
        }, follow_redirects=False)
        assert resp.status_code in (301, 302)

        # Verify on list page
        list_resp = registered_client.get("/applications")
        assert resp.status_code in (200, 301, 302)
        assert b"Integration Corp" in list_resp.data

    def test_detail_page_shows_correct_data(self, registered_client):
        """Detail page shows the application data that was submitted."""
        resp = registered_client.post("/applications/new", data={
            "company": "Detail Corp",
            "position": "QA Engineer",
            "status": "interviewing",
            "applied_date": "2026-05-10",
            "notes": "Detail test note",
        }, follow_redirects=False)
        location = resp.headers.get("Location", "")
        app_id = location.rstrip("/").split("/")[-1]

        detail = registered_client.get(f"/applications/{app_id}")
        assert detail.status_code == 200
        assert b"Detail Corp" in detail.data
        assert b"QA Engineer" in detail.data

    def test_edit_application_updates_data(self, registered_client):
        """Editing an application updates the stored data."""
        # Create
        resp = registered_client.post("/applications/new", data={
            "company": "Edit Corp",
            "position": "Junior Dev",
            "status": "applied",
            "applied_date": "2026-05-01",
        }, follow_redirects=False)
        location = resp.headers.get("Location", "")
        app_id = location.rstrip("/").split("/")[-1]

        # Edit
        edit_resp = registered_client.post(
            f"/applications/{app_id}/edit", data={
                "company": "Edit Corp",
                "position": "Senior Dev",
                "status": "interviewing",
                "applied_date": "2026-05-01",
            }, follow_redirects=True)
        assert edit_resp.status_code == 200
        assert b"Senior Dev" in edit_resp.data

    def test_delete_application_removes_from_list(self, registered_client):
        """Deleting an application removes it from the list."""
        # Create
        resp = registered_client.post("/applications/new", data={
            "company": "Delete Corp",
            "position": "Temp Role",
            "status": "withdrawn",
            "applied_date": "2026-05-01",
        }, follow_redirects=False)
        location = resp.headers.get("Location", "")
        app_id = location.rstrip("/").split("/")[-1]

        # Delete
        registered_client.post(
            f"/applications/{app_id}/delete",
            follow_redirects=True
        )

        # Verify gone from list
        list_resp = registered_client.get("/applications")
        assert b"Delete Corp" not in list_resp.data

    def test_ownership_isolation(self, registered_client, app):
        """User A cannot access User B's applications."""
        # Create as integration_user
        resp = registered_client.post("/applications/new", data={
            "company": "Secret Corp",
            "position": "Secret Role",
            "status": "applied",
            "applied_date": "2026-05-01",
        }, follow_redirects=False)
        location = resp.headers.get("Location", "")
        app_id = location.rstrip("/").split("/")[-1]

        # Try to access as a different user
        other = app.test_client()
        other.post("/register", data={
            "username": "integ_other",
            "email": "integ_other@example.com",
            "password": "OtherPass123",
            "confirm_password": "OtherPass123",
        }, follow_redirects=True)
        other.post("/login", data={
            "username": "integ_other",
            "password": "OtherPass123",
        }, follow_redirects=True)

        resp = other.get(f"/applications/{app_id}")
        assert resp.status_code == 404

    def test_anonymous_user_cannot_access_applications(self, client):
        """Anonymous users are redirected to login for all app routes."""
        for path in ["/applications", "/applications/new", "/applications/1"]:
            resp = client.get(path, follow_redirects=False)
            assert resp.status_code in (301, 302), (
                f"Expected redirect for anonymous access to {path}"
            )

    def test_status_filter_integration(self, registered_client):
        """Status filter returns only matching applications."""
        # Create two applications with different statuses
        registered_client.post("/applications/new", data={
            "company": "Filter A",
            "position": "Role A",
            "status": "offered",
            "applied_date": "2026-05-01",
        }, follow_redirects=True)
        registered_client.post("/applications/new", data={
            "company": "Filter B",
            "position": "Role B",
            "status": "rejected",
            "applied_date": "2026-05-01",
        }, follow_redirects=True)

        # Filter for offered only
        resp = registered_client.get("/applications?status=offered")
        assert resp.status_code == 200
        assert b"Filter A" in resp.data
        assert b"Filter B" not in resp.data
