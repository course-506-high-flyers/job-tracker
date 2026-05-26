import re

from playwright.sync_api import Page, expect


def _session_cookie(context):
    """Return the Flask session cookie from a Playwright browser context."""
    for cookie in context.cookies():
        if cookie.get("name") == "session":
            return cookie
    return None


def test_protected_page_requires_login_then_logout(page: Page, live_server):
    # Logged out users must be redirected away from protected content.
    page.goto(f"{live_server.url}/applications")
    expect(page).to_have_url(re.compile(r".*/login(\?.*)?$"))
    expect(page.get_by_role("heading", name="Log in")).to_be_visible()

    # Log in through test-only backdoor route.
    page.goto(f"{live_server.url}/test/login/aden")
    expect(page.get_by_role("heading", name="My Applications")).to_be_visible()
    expect(page.get_by_text("Hello, aden")).to_be_visible()

    # Session cookie must carry the hardening flags this role is responsible for.
    cookie = _session_cookie(page.context)
    assert cookie is not None, "Expected a Flask session cookie after login"
    assert cookie["httpOnly"] is True, "Session cookie must be HttpOnly"
    assert cookie["sameSite"] == "Lax", "Session cookie must use SameSite=Lax"
    # Note: cookie.secure is intentionally False here because the e2e fixture
    # serves over plain HTTP (SESSION_COOKIE_SECURE=false). In production-like
    # config the flag is True; this gap is documented in role_work.md.

    # Protected content is accessible after login.
    page.goto(f"{live_server.url}/applications")
    expect(page.get_by_role("heading", name="My Applications")).to_be_visible()

    # After logout, access should be denied again.
    page.get_by_role("link", name="Log out").click()
    expect(page.locator("nav").get_by_role("link", name="Log in")).to_be_visible()
    page.goto(f"{live_server.url}/applications")
    expect(page).to_have_url(re.compile(r".*/login(\?.*)?$"))
