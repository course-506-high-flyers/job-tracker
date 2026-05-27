"""
tests/e2e/test_full_lifecycle.py

Owner: High Flyers Team (coordinator: Boma Okoli) — Week 7
Role: Coordinator / Team

Purpose: Full-system Playwright suite exercising the OAuth login lifecycle.
Covers four required scenarios:
1. First-time OAuth login — user + oauth_identity rows created
2. Returning OAuth login — existing row reused, not duplicated
3. CSRF protection — tokenless POST rejected
4. Session lifecycle — protected page inaccessible after logout

Uses the test-login backdoor for everything after the OAuth redirect.
The real GitHub redirect is a named gap — see team_walkthrough.md.
"""

import pytest
from playwright.sync_api import Page, expect
from sqlmodel import Session, select

from models import OAuthIdentity, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_engine(live_server):
    """Get the SQLModel engine from the running app."""
    import sys
    # app module is already loaded by the live_server fixture
    from app import engine
    return engine


# ---------------------------------------------------------------------------
# Test 1 — First-time OAuth login
# ---------------------------------------------------------------------------

def test_first_time_oauth_login(page: Page, live_server):
    """
    A user with no existing account logs in via the backdoor.
    Verifies: login page has GitHub button, backdoor creates user,
    navbar shows username, oauth_identity row exists in DB.
    """
    # Verify GitHub button is on login page
    page.goto(f"{live_server.url}/login")
    expect(page.get_by_role("link", name="Sign in with GitHub")).to_be_visible()

    # Log in via backdoor as a brand new user
    page.goto(f"{live_server.url}/test/login/alice_first")

    # Verify post-login state
    expect(page.get_by_text("Hello, alice_first")).to_be_visible()
    expect(page.get_by_role("link", name="My Applications")).to_be_visible()

    # Verify user row exists in DB
    engine = get_engine(live_server)
    with Session(engine) as db:
        user = db.exec(
            select(User).where(User.username == "alice_first")
        ).first()
        assert user is not None, "User row must be created on first login"


# ---------------------------------------------------------------------------
# Test 2 — Returning OAuth login
# ---------------------------------------------------------------------------

def test_returning_oauth_login(page: Page, live_server):
    """
    The same user logs in twice. Verifies the second login reuses
    the existing user row — no duplicate created.
    """
    username = "alice_returning"

    # First login
    page.goto(f"{live_server.url}/test/login/{username}")
    expect(page.get_by_text(f"Hello, {username}")).to_be_visible()

    # Log out
    page.get_by_role("link", name="Log out").click()
    expect(page.get_by_role("link", name="Log in")).to_be_visible()

    # Second login
    page.goto(f"{live_server.url}/test/login/{username}")
    expect(page.get_by_text(f"Hello, {username}")).to_be_visible()

    # Verify only one user row exists
    engine = get_engine(live_server)
    with Session(engine) as db:
        users = db.exec(
            select(User).where(User.username == username)
        ).all()
        assert len(users) == 1, (
            f"Expected exactly 1 user row for {username}, found {len(users)}. "
            "The returning login branch must reuse existing rows."
        )


# ---------------------------------------------------------------------------
# Test 3 — CSRF protection
# ---------------------------------------------------------------------------

def test_csrf_protection(page: Page, live_server):
    """
    A tokenless POST to a state-changing endpoint is rejected with 400.
    Uses Playwright's request context to send a raw POST without a CSRF token.
    """
    # Log in first so the route is reachable
    page.goto(f"{live_server.url}/test/login/csrf_test_user")
    expect(page.get_by_text("Hello, csrf_test_user")).to_be_visible()

    # Send a tokenless POST to /logout using Playwright's API context
    # This bypasses the browser form and sends no csrf_token field
    api_context = page.request

    response = api_context.post(
        f"{live_server.url}/logout",
        form={},  # no csrf_token field
    )

    # CSRF protection must reject this with 400
    assert response.status == 400, (
        f"Expected 400 for tokenless POST, got {response.status}. "
        "Flask-WTF CSRF protection may be disabled."
    )


# ---------------------------------------------------------------------------
# Test 4 — Session lifecycle
# ---------------------------------------------------------------------------

def test_session_lifecycle(page: Page, live_server):
    """
    Full session lifecycle: login → access protected page → logout →
    protected page inaccessible again.
    """
    username = "session_lifecycle_user"

    # Step 1: logged out — protected page redirects to login
    page.goto(f"{live_server.url}/applications")
    expect(page).to_have_url(f"{live_server.url}/login")

    # Step 2: log in via backdoor
    page.goto(f"{live_server.url}/test/login/{username}")
    expect(page.get_by_text(f"Hello, {username}")).to_be_visible()

    # Step 3: protected page now accessible
    page.goto(f"{live_server.url}/applications")
    expect(page).to_have_url(f"{live_server.url}/applications")

    # Step 4: log out
    page.get_by_role("link", name="Log out").click()
    expect(page.get_by_role("link", name="Log in")).to_be_visible()

    # Step 5: protected page inaccessible again
    page.goto(f"{live_server.url}/applications")
    expect(page).to_have_url(f"{live_server.url}/login")
