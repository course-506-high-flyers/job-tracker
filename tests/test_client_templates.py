"""
tests/test_client_templates.py

Owner: Boma Okoli (Client-side role) — High Flyers, Week 6
Role: Client-side

Purpose: Verify template structure and form shapes for the Job Application Tracker.
Uses Flask test client + BeautifulSoup. Tests assert on HTML structure and CSS
selectors — NOT on copy/text content, so the client-side developer can freely
change labels, placeholder text, and headings without breaking these tests.

All tests in this file are INITIALLY FAILING by design. They go green only
when the client-side role's templates are implemented.
"""

import pytest
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(app):
    """Flask test client. 'app' fixture provided by conftest.py."""
    return app.test_client()


@pytest.fixture
def logged_in_client(client, app):
    """Test client pre-authenticated as a test user."""
    with app.app_context():
        client.post("/register", data={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "TestPass123",
            "confirm_password": "TestPass123",
        }, follow_redirects=True)
        client.post("/login", data={
            "username": "testuser",
            "password": "TestPass123",
        }, follow_redirects=True)
    return client


@pytest.fixture
def sample_application(logged_in_client, app):
    """Create a sample application and return its ID."""
    resp = logged_in_client.post("/applications/new", data={
        "company": "Acme Corp",
        "position": "Software Engineer",
        "status": "applied",
        "applied_date": "2026-05-01",
        "notes": "Applied via LinkedIn",
        "job_url": "https://acme.com/jobs/123",
    }, follow_redirects=False)
    location = resp.headers.get("Location", "")
    app_id = location.rstrip("/").split("/")[-1]
    return app_id


# ---------------------------------------------------------------------------
# base.html — Navigation bar
# ---------------------------------------------------------------------------

class TestBaseNav:

    def test_nav_contains_applications_link_when_logged_in(self, logged_in_client):
        resp = logged_in_client.get("/")
        soup = BeautifulSoup(resp.data, "html.parser")
        nav = soup.find("nav")
        assert nav is not None, "No <nav> element found in base template"
        links = nav.find_all("a", href=True)
        hrefs = [a["href"] for a in links]
        assert "/applications" in hrefs, (
            f"Nav must contain a link to /applications. Found hrefs: {hrefs}"
        )

    def test_nav_contains_logout_link_when_logged_in(self, logged_in_client):
        resp = logged_in_client.get("/")
        soup = BeautifulSoup(resp.data, "html.parser")
        nav = soup.find("nav")
        links = nav.find_all("a", href=True)
        hrefs = [a["href"] for a in links]
        assert "/logout" in hrefs or soup.find("form", action=True) is not None

    def test_nav_does_not_contain_applications_link_when_anonymous(self, client):
        resp = client.get("/")
        soup = BeautifulSoup(resp.data, "html.parser")
        nav = soup.find("nav")
        if nav is None:
            return
        links = nav.find_all("a", href=True)
        hrefs = [a["href"] for a in links]
        assert "/applications" not in hrefs


# ---------------------------------------------------------------------------
# applications/list.html
# ---------------------------------------------------------------------------

class TestApplicationListTemplate:

    def test_list_page_returns_200(self, logged_in_client):
        resp = logged_in_client.get("/applications")
        assert resp.status_code == 200

    def test_list_page_has_link_to_new_application(self, logged_in_client):
        resp = logged_in_client.get("/applications")
        soup = BeautifulSoup(resp.data, "html.parser")
        buttons_to_new = soup.find_all(
            lambda tag: tag.name in ("a", "button") and
            tag.get("href") == "/applications/new"
        )
        assert len(buttons_to_new) > 0

    def test_list_page_has_status_filter_form(self, logged_in_client):
        resp = logged_in_client.get("/applications")
        soup = BeautifulSoup(resp.data, "html.parser")
        status_input = soup.find(attrs={"name": "status"})
        assert status_input is not None

    def test_list_page_shows_application_rows_after_creation(
        self, logged_in_client, sample_application
    ):
        resp = logged_in_client.get("/applications")
        soup = BeautifulSoup(resp.data, "html.parser")
        rows = soup.find_all(class_="application-row")
        assert len(rows) >= 1

    def test_application_row_has_detail_link(self, logged_in_client, sample_application):
        resp = logged_in_client.get("/applications")
        soup = BeautifulSoup(resp.data, "html.parser")
        detail_link = soup.find("a", href=f"/applications/{sample_application}")
        assert detail_link is not None

    def test_empty_state_renders_without_error(self, logged_in_client):
        resp = logged_in_client.get("/applications")
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.data, "html.parser")
        assert soup.find("body") is not None


# ---------------------------------------------------------------------------
# applications/form.html
# ---------------------------------------------------------------------------

class TestApplicationFormTemplate:

    def test_new_form_returns_200(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        assert resp.status_code == 200

    def test_new_form_has_correct_action(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        form = soup.find("form")
        assert form is not None
        assert form.get("action") == "/applications/new"

    def test_new_form_method_is_post(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        form = soup.find("form")
        assert form is not None
        assert form.get("method", "").lower() == "post"

    def test_new_form_has_company_field(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        field = soup.find("input", attrs={"name": "company"})
        assert field is not None

    def test_new_form_has_position_field(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        field = soup.find("input", attrs={"name": "position"})
        assert field is not None

    def test_new_form_has_status_select(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        select = soup.find("select", attrs={"name": "status"})
        assert select is not None

    def test_status_select_has_all_enum_options(self, logged_in_client):
        expected = {"applied", "interviewing", "offered", "rejected", "withdrawn"}
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        select = soup.find("select", attrs={"name": "status"})
        assert select is not None
        option_values = {opt.get("value") for opt in select.find_all("option")}
        assert expected.issubset(option_values)

    def test_new_form_has_applied_date_field(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        field = soup.find("input", attrs={"name": "applied_date"})
        assert field is not None

    def test_new_form_has_notes_textarea(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        field = soup.find("textarea", attrs={"name": "notes"})
        assert field is not None

    def test_new_form_has_job_url_field(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        field = soup.find("input", attrs={"name": "job_url"})
        assert field is not None

    def test_new_form_has_submit_button(self, logged_in_client):
        resp = logged_in_client.get("/applications/new")
        soup = BeautifulSoup(resp.data, "html.parser")
        submit = soup.find("button", attrs={"type": "submit"})
        if submit is None:
            submit = soup.find("input", attrs={"type": "submit"})
        assert submit is not None

    def test_edit_form_returns_200(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}/edit")
        assert resp.status_code == 200

    def test_edit_form_has_correct_action(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}/edit")
        soup = BeautifulSoup(resp.data, "html.parser")
        form = soup.find("form")
        assert form is not None
        expected_action = f"/applications/{sample_application}/edit"
        assert form.get("action") == expected_action

    def test_edit_form_prefills_company(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}/edit")
        soup = BeautifulSoup(resp.data, "html.parser")
        field = soup.find("input", attrs={"name": "company"})
        assert field is not None
        assert field.get("value") == "Acme Corp"

    def test_edit_form_prefills_position(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}/edit")
        soup = BeautifulSoup(resp.data, "html.parser")
        field = soup.find("input", attrs={"name": "position"})
        assert field is not None
        assert field.get("value") == "Software Engineer"

    def test_edit_form_prefills_status(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}/edit")
        soup = BeautifulSoup(resp.data, "html.parser")
        select = soup.find("select", attrs={"name": "status"})
        assert select is not None
        selected_opt = select.find("option", selected=True)
        assert selected_opt is not None
        assert selected_opt.get("value") == "applied"

    def test_edit_form_prefills_notes(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}/edit")
        soup = BeautifulSoup(resp.data, "html.parser")
        textarea = soup.find("textarea", attrs={"name": "notes"})
        assert textarea is not None
        assert "Applied via LinkedIn" in textarea.get_text()


# ---------------------------------------------------------------------------
# applications/detail.html
# ---------------------------------------------------------------------------

class TestApplicationDetailTemplate:

    def test_detail_page_returns_200(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}")
        assert resp.status_code == 200

    def test_detail_page_has_edit_link(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}")
        soup = BeautifulSoup(resp.data, "html.parser")
        edit_link = soup.find("a", href=f"/applications/{sample_application}/edit")
        assert edit_link is not None

    def test_detail_page_has_delete_form(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}")
        soup = BeautifulSoup(resp.data, "html.parser")
        delete_form = soup.find(
            "form",
            attrs={"action": f"/applications/{sample_application}/delete"}
        )
        assert delete_form is not None
        delete_btn = delete_form.find("button", attrs={"type": "submit"})
        assert delete_btn is not None

    def test_detail_page_has_insight_section(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}")
        soup = BeautifulSoup(resp.data, "html.parser")
        insight_section = soup.find(id="insight-section")
        if insight_section is None:
            insight_section = soup.find(class_="insight-section")
        assert insight_section is not None

    def test_detail_page_has_refresh_insight_link(self, logged_in_client, sample_application):
        resp = logged_in_client.get(f"/applications/{sample_application}")
        soup = BeautifulSoup(resp.data, "html.parser")
        insight_link = soup.find("a", href=f"/applications/{sample_application}/insight")
        assert insight_link is not None

    def test_non_owner_gets_404(self, client, app, sample_application):
        client.post("/register", data={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "OtherPass123",
            "confirm_password": "OtherPass123",
        }, follow_redirects=True)
        client.post("/login", data={
            "username": "otheruser",
            "password": "OtherPass123",
        }, follow_redirects=True)
        resp = client.get(f"/applications/{sample_application}")
        assert resp.status_code == 404

    def test_anonymous_detail_redirects_to_login(self, client, sample_application):
        client.get("/logout", follow_redirects=False)
        resp = client.get(f"/applications/{sample_application}", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.location
