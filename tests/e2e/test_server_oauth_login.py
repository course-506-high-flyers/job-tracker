from playwright.sync_api import Page, expect


def test_server_side_login_shows_username(page: Page, live_server):
    page.goto(f"{live_server.url}/login")

    expect(page.get_by_role("link", name="Sign in with GitHub")).to_be_visible()

    page.goto(f"{live_server.url}/test/login/darrell")

    expect(page.get_by_text("Hello, darrell")).to_be_visible()
