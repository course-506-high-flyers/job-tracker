"""
tests/e2e/test_client_e2e.py

Owner: Boma Okoli (Client-side role) — High Flyers, Week 7
Role: Client-side

Purpose: Playwright end-to-end test verifying the client-side OAuth login
flow and post-login UI state. Uses the test-login backdoor to bypass the
real GitHub redirect, then asserts on rendered DOM elements.

Adapted from Week 6 client-side e2e walkthrough — inserted test-login
backdoor at the top, then exercises the same template surfaces.
"""

import re
import pytest
from playwright.sync_api import Page, expect


def test_login_page_has_github_button(page: Page, live_server):
    """
    A logged-out user visiting /login sees the Sign in with GitHub button.
    This catches regressions where the GitHub button is accidentally removed
    or the login template reverts to the password-only form.
    """
    page.goto(f"{live_server.url}/login")
    expect(page.get_by_role("link", name="Sign in with GitHub")).to_be_visible()


def test_login_page_has_password_form(page: Page, live_server):
    """
    The password form must coexist with the GitHub button — both login
    methods must be available on the same page.
    """
    page.goto(f"{live_server.url}/login")
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.locator("input[name='remember_me']")).to_be_visible()


def test_login_page_has_remember_me_checkbox(page: Page, live_server):
    """
    Remember me checkbox is present and unchecked by default.
    Regression: someone removes the checkbox or changes its name attribute.
    """
    page.goto(f"{live_server.url}/login")
    checkbox = page.locator("input[name='remember_me']")
    expect(checkbox).to_be_visible()
    expect(checkbox).not_to_be_checked()


def test_github_button_links_to_login_github_route(page: Page, live_server):
    """
    The Sign in with GitHub button must href to /login/github.
    Regression: href points to wrong URL or is missing entirely.
    """
    page.goto(f"{live_server.url}/login")
    github_link = page.get_by_role("link", name="Sign in with GitHub")
    expect(github_link).to_be_visible()
    href = github_link.get_attribute("href")
    assert href is not None
    assert "/login/github" in href


def test_logged_out_user_redirected_from_applications(page: Page, live_server):
    """
    Anonymous user navigating to /applications is redirected to /login.
    Regression: @login_required removed from applications_list route.
    """
    page.goto(f"{live_server.url}/applications")
    expect(page).to_have_url(re.compile(r".*/login(\?.*)?$"))


def test_backdoor_login_shows_username_in_nav(page: Page, live_server):
    """
    After logging in via the test-login backdoor, the navbar shows
    the username and My Applications link.
    This is the core client-side post-login UX assertion.
    Regression: base.html nav logic broken, or inject_user context
    processor stops injecting current_user.
    """
    # Log in via backdoor — bypasses GitHub entirely
    page.goto(f"{live_server.url}/test/login/boma")

    # Verify username appears in navbar
    expect(page.get_by_text("Hello, boma")).to_be_visible()

    # Verify My Applications nav link is present
    expect(page.get_by_role("link", name="My Applications")).to_be_visible()


def test_backdoor_login_then_applications_list(page: Page, live_server):
    """
    After login, user can navigate to /applications and see the list page.
    Regression: applications_list route broken or template missing.
    """
    page.goto(f"{live_server.url}/test/login/boma")
    page.get_by_role("link", name="My Applications").click()
    expect(page).to_have_url(f"{live_server.url}/applications")
    # Empty state or list — either way the page must render
    expect(page.locator("body")).to_be_visible()


def test_logout_clears_nav_state(page: Page, live_server):
    """
    After logging out, the navbar no longer shows the username
    and My Applications link is gone.
    Regression: logout_user() or session.clear() broken,
    or nav template doesn't check authentication state.
    """
    # Log in first
    page.goto(f"{live_server.url}/test/login/boma_logout_test")
    expect(page.get_by_text("Hello, boma_logout_test")).to_be_visible()

    # Log out
    page.get_by_role("link", name="Log out").click()

    # Verify nav reverts to anonymous state
    expect(page.get_by_role("link", name="Log in", exact=True)).to_be_visible()
    expect(page.get_by_text("Hello, boma_logout_test")).not_to_be_visible()


def test_login_page_github_button_is_prominent(page: Page, live_server):
    """
    The GitHub button renders before the password form —
    OAuth is the primary login method per the contract.
    Regression: template order changed so GitHub button appears below
    the password form instead of above it.
    """
    page.goto(f"{live_server.url}/login")

    github_btn = page.get_by_role("link", name="Sign in with GitHub")
    password_field = page.locator("input[name='password']")

    github_y = github_btn.bounding_box()["y"]
    password_y = password_field.bounding_box()["y"]

    assert github_y < password_y, (
        "GitHub button must appear above the password form on the login page"
    )
