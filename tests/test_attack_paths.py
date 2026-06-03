"""Attack-path tests for Assignment 8 (Aden / DB-sec slice).

These tests probe the running app for known scanner targets and confirm:

    1. Each path returns one of {301, 302, 404}.
       (Never 200, never 500.)
    2. The response body does not leak internals like Python tracebacks,
       framework names, or the literal string `secret_key`.

The test data lives in ``attack_paths.json`` at the repo root so the list is
data-not-code and can be reviewed without reading Python.

Where this test runs
====================
The base URL is read from the ``JOB_TRACKER_BASE_URL`` environment variable.
Defaults to ``https://localhost:8443`` which matches the local nginx sidecar
brought up during evidence collection. Override for the EC2 deploy:

    JOB_TRACKER_BASE_URL=https://<ec2-host> pytest tests/test_attack_paths.py

Self-signed dev certs make ``requests`` complain. We pass ``verify=False`` and
silence the InsecureRequestWarning. In production, the cert is Let's Encrypt
and verify will be True automatically (if you flip the env-driven flag below).

Skipped vs. failed
==================
If the base URL is unreachable, the suite is skipped (not failed) so this
file is safe to keep in CI before the prod stack exists. Once the EC2 deploy
lands, point ``JOB_TRACKER_BASE_URL`` at it and the suite will run.
"""
from __future__ import annotations

import json
import os
import pathlib

import pytest
import requests
from urllib3.exceptions import InsecureRequestWarning


BASE_URL = os.environ.get("JOB_TRACKER_BASE_URL", "https://localhost:8443").rstrip("/")
VERIFY_TLS = os.environ.get("JOB_TRACKER_VERIFY_TLS", "false").lower() in {"1", "true", "yes"}
ALLOWED_STATUSES = {301, 302, 404}
LEAK_MARKERS = (
    "traceback",
    "werkzeug",
    "sqlalchemy",
    "psycopg2",
    "secret_key",
    "postgres://",
    "postgresql://",
)

DATA_FILE = pathlib.Path(__file__).resolve().parent.parent / "attack_paths.json"
ATTACK_PATHS: list[dict] = json.loads(DATA_FILE.read_text(encoding="utf-8"))

if not VERIFY_TLS:
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


@pytest.fixture(scope="session")
def attack_target() -> str:
    """Verify the target URL is reachable; skip the whole module if not.

    Renamed away from the conventional ``base_url`` to avoid a scope clash
    with the ``base_url`` fixture provided by ``pytest-base-url`` (a transitive
    dependency of ``pytest-playwright`` in our requirements.txt).
    """
    try:
        requests.get(BASE_URL + "/", verify=VERIFY_TLS, timeout=5, allow_redirects=False)
    except requests.exceptions.RequestException as exc:
        pytest.skip(
            f"JOB_TRACKER_BASE_URL={BASE_URL!r} is not reachable ({exc.__class__.__name__}); "
            "bring up nginx + app first or set JOB_TRACKER_BASE_URL to a deployed host."
        )
    return BASE_URL


@pytest.mark.parametrize("entry", ATTACK_PATHS, ids=lambda e: e["path"])
def test_attack_path_returns_safe_status(attack_target: str, entry: dict) -> None:
    url = f"{attack_target}{entry['path']}"
    resp = requests.get(url, verify=VERIFY_TLS, timeout=5, allow_redirects=False)
    assert resp.status_code in ALLOWED_STATUSES, (
        f"{entry['path']} returned {resp.status_code}; "
        f"expected one of {sorted(ALLOWED_STATUSES)} (category={entry['category']})"
    )


@pytest.mark.parametrize("entry", ATTACK_PATHS, ids=lambda e: e["path"])
def test_attack_path_body_does_not_leak_internals(attack_target: str, entry: dict) -> None:
    url = f"{attack_target}{entry['path']}"
    resp = requests.get(url, verify=VERIFY_TLS, timeout=5, allow_redirects=False)
    body_lower = resp.text.lower()
    for marker in LEAK_MARKERS:
        assert marker not in body_lower, (
            f"{entry['path']} body contains leak marker {marker!r}; "
            f"first 200 chars: {resp.text[:200]!r} (category={entry['category']})"
        )


def test_https_only_root_redirects(attack_target: str) -> None:
    """If we hit the http variant of the target URL, we should be 301'd to https.

    Skipped automatically if attack_target is already http (e.g., a dev-only
    host that doesn't terminate TLS).
    """
    if not attack_target.startswith("https://"):
        pytest.skip("attack_target is not https; nothing to redirect")
    http_base = attack_target.replace("https://", "http://", 1)
    if ":8443" in http_base:
        http_base = http_base.replace(":8443", ":8080")
    try:
        resp = requests.get(http_base + "/", verify=VERIFY_TLS, timeout=5, allow_redirects=False)
    except requests.exceptions.RequestException as exc:
        pytest.skip(f"http variant {http_base!r} not reachable ({exc.__class__.__name__})")
    assert resp.status_code in {301, 302}, (
        f"http {http_base}/ returned {resp.status_code}; expected 301/302 to https"
    )
    location = resp.headers.get("location", "")
    assert location.startswith("https://"), f"Location header was {location!r}"
