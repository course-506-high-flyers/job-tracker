"""
Course 506 Week 5 Skeleton — Flask + Postgres + SQLModel + Bootstrap

Single-file Flask app demonstrating the architecture of a web application:
- Server (Flask) handles HTTP requests
- Database (Postgres via SQLModel) stores user state across requests
- Flask-Login keeps users logged in across requests
- Templates render HTML to send back to the browser

The home page serves the static site you sync from your S3 bucket into
S3_content/. Login, register, logout, and about are Flask-rendered routes.

This file is meant to be readable top-to-bottom. No Blueprints, no app factory,
no advanced Flask patterns. Just enough to teach the architecture.
"""

# MUST come before any os.environ lookups so .env values are visible.
from dotenv import load_dotenv
load_dotenv()

import os
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import (
    Flask, render_template, request, redirect, url_for, flash, g, session,
    send_from_directory, abort,
)
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from sqlmodel import SQLModel, Session, create_engine, select
from werkzeug.security import generate_password_hash, check_password_hash

from models import User, JobApplication, JobInsight, OAuthIdentity  # noqa: F401  (OAuthIdentity registered for metadata.create_all)
from services.company_api import get_cached_insight, refresh_insight

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = Flask(__name__)


def _env_bool(key: str, default: bool) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Secrets and DB are strict env lookups: a missing value crashes on startup
# instead of surfacing as a confusing runtime error later.
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

app.config["SESSION_COOKIE_SECURE"] = _env_bool("SESSION_COOKIE_SECURE", True)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    seconds=int(os.environ.get("PERMANENT_SESSION_LIFETIME_SECONDS", "1209600"))
)
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(
    seconds=int(os.environ.get("REMEMBER_COOKIE_DURATION_SECONDS", "1209600"))
)
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_SECURE"] = _env_bool("REMEMBER_COOKIE_SECURE", True)
app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"

csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# SQLModel uses SQLAlchemy underneath. The engine is the connection pool.
engine = create_engine(DATABASE_URL, echo=False)

# Path to the synced S3 content. Students populate this with `aws s3 sync`.
S3_CONTENT_DIR = Path(__file__).parent / "S3_content"

S3_SITE_URLS = (
    "http://506-class-2026-demo.s3-website.us-east-2.amazonaws.com",
    "http://506-class-2026-demo.s3-website-us-west-2.amazonaws.com",
)


# ---------------------------------------------------------------------------
# Session helper
#
# SQLModel doesn't have a Flask extension. We open a fresh DB session for each
# request and close it when the request finishes. Flask's `g` object holds
# request-scoped state.
# ---------------------------------------------------------------------------

def get_db_session():
    if "db_session" not in g:
        g.db_session = Session(engine)
    return g.db_session


@app.teardown_appcontext
def close_db_session(exception=None):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


@login_manager.user_loader
def load_user(user_id: str):
    try:
        user_pk = int(user_id)
    except ValueError:
        return None

    db = get_db_session()
    return db.get(User, user_pk)


# Make `user` available in every Flask-rendered template (login page, register
# page, about page, placeholder). Static files served from S3_content/ don't
# go through templates, so this only affects Jinja2-rendered pages.
@app.context_processor
def inject_user():
    user = current_user if current_user.is_authenticated else None
    return {"user": user}

STATUS_CHOICES = ["applied", "interviewing", "offered", "rejected", "withdrawn"]


def get_owned_application(app_id):
    db = get_db_session()
    app_record = db.get(JobApplication, app_id)

    if not app_record:
        abort(404)

    if app_record.user_id != current_user.id:
        abort(404)

    return app_record


def validate_application_form(form):
    errors = {}

    company = form.get("company", "").strip()
    position = form.get("position", "").strip()
    status = form.get("status", "").strip()
    applied_date_raw = form.get("applied_date", "").strip()
    notes = form.get("notes", "").strip()
    job_url = form.get("job_url", "").strip()

    if not company:
        errors["company"] = "Company is required."

    if not position:
        errors["position"] = "Position is required."

    if status not in STATUS_CHOICES:
        errors["status"] = "Invalid status."

    try:
        applied_date = date.fromisoformat(applied_date_raw)
    except ValueError:
        errors["applied_date"] = "Valid applied date is required."
        applied_date = None

    return {
        "company": company,
        "position": position,
        "status": status,
        "applied_date": applied_date,
        "notes": notes or None,
        "job_url": job_url or None,
        "errors": errors,
    }


@lru_cache(maxsize=1)
def get_team_s3_site_url():
    for url in S3_SITE_URLS:
        request = Request(url, headers={"User-Agent": "job-tracker-health-check"})
        try:
            with urlopen(request, timeout=2) as response:
                if 200 <= response.status < 400:
                    return url
        except (HTTPError, URLError, TimeoutError):
            continue

    return S3_SITE_URLS[0]

# ---------------------------------------------------------------------------
# Routes — your S3 static site
#
# Your S3 site lives at /site/. Populate the S3_content/ folder by running:
#   aws s3 sync s3://<your-bucket>/ S3_content/
# from the repo root. Then click "My Site" in the navbar.
#
# The home page is Flask-rendered and acts as the entry point: it has the
# navbar (Login/Register/About/My Site) and a brief landing message.
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/site/")
def site_home():
    index_path = S3_CONTENT_DIR / "index.html"
    if not index_path.exists():
        # Friendly placeholder when the student hasn't synced yet.
        return render_template("placeholder.html"), 200
    return send_from_directory(S3_CONTENT_DIR, "index.html")


@app.route("/site/<path:filename>")
def serve_s3_content(filename):
    file_path = S3_CONTENT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    return send_from_directory(S3_CONTENT_DIR, filename)


# ---------------------------------------------------------------------------
# Routes — authentication (Flask-rendered, not static)
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # POST: create a new user.
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Username and password are required.")
        return redirect(url_for("register"))

    db = get_db_session()
    existing = db.exec(select(User).where(User.username == username)).first()
    if existing is not None:
        flash("That username is already taken.")
        return redirect(url_for("register"))

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    login_user(user, remember=False)
    session.permanent = False
    session["user_id"] = user.id
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # POST: validate credentials.
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    remember_me = request.form.get("remember_me") == "on"

    db = get_db_session()
    user = db.exec(select(User).where(User.username == username)).first()

    if user is None or not check_password_hash(user.password_hash, password):
        flash("Invalid username or password.")
        return redirect(url_for("login"))

    login_user(user, remember=remember_me)
    session.permanent = remember_me
    session["user_id"] = user.id
    return redirect(request.args.get("next") or url_for("home"))


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("home"))


@app.route("/test/login/<username>")
def test_login(username):
    if not app.config.get("TESTING"):
        abort(404)

    safe_username = username.strip().lower()
    if not safe_username:
        abort(404)

    db = get_db_session()
    user = db.exec(select(User).where(User.username == safe_username)).first()
    if user is None:
        user = User(
            username=safe_username,
            password_hash=generate_password_hash("test-login-placeholder"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    login_user(user)
    session.permanent = False
    session["user_id"] = user.id
    return redirect(url_for("applications_list"))


@app.route("/about")
def about():
    # Each team replaces this content with their own About page (see
    # the assignment instructions in README.md).
    return render_template("about.html", team_s3_site_url=get_team_s3_site_url())


@app.route("/applications")
@login_required
def applications_list():
    db = get_db_session()
    status_filter = request.args.get("status")

    query = select(JobApplication).where(JobApplication.user_id == current_user.id)

    if status_filter in STATUS_CHOICES:
        query = query.where(JobApplication.status == status_filter)
    else:
        status_filter = None

    applications = db.exec(query).all()

    return render_template(
        "applications/list.html",
        applications=applications,
        status_filter=status_filter,
        status_choices=STATUS_CHOICES,
    )


@app.route("/applications/new", methods=["GET", "POST"])
@login_required
def applications_new():
    if request.method == "GET":
        return render_template(
            "applications/form.html",
            form_action="/applications/new",
            application=None,
            errors={},
        )

    data = validate_application_form(request.form)
    errors = data.pop("errors")

    db = get_db_session()

    if errors:
        return render_template(
            "applications/form.html",
            form_action="/applications/new",
            application=type("ApplicationForm", (), data),
            errors=errors,
        ), 400

    duplicate = db.exec(
        select(JobApplication).where(
            JobApplication.user_id == current_user.id,
            JobApplication.company == data["company"],
            JobApplication.position == data["position"],
        )
    ).first()

    if duplicate:
        errors["duplicate"] = "You already saved this application."
        flash("You already saved this application.", "error")
        return render_template(
            "applications/form.html",
            form_action="/applications/new",
            application=type("ApplicationForm", (), data),
            errors=errors,
        ), 409

    application = JobApplication(
        user_id=current_user.id,
        **data,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    flash("Application saved.", "success")
    return redirect(f"/applications/{application.id}")

@app.route("/applications/<int:app_id>")
@login_required
def applications_detail(app_id):
    application = get_owned_application(app_id)
    db = get_db_session()

    insight = get_cached_insight(db, application.company)

    return render_template(
        "applications/detail.html",
        application=application,
        insight=insight,
    )

@app.route("/applications/<int:app_id>/edit", methods=["GET", "POST"])
@login_required
def applications_edit(app_id):
    application = get_owned_application(app_id)

    if request.method == "GET":
        return render_template(
            "applications/form.html",
            form_action=f"/applications/{application.id}/edit",
            application=application,
            errors={},
        )

    data = validate_application_form(request.form)
    errors = data.pop("errors")

    if errors:
        for key, value in data.items():
            setattr(application, key, value)

        return render_template(
            "applications/form.html",
            form_action=f"/applications/{application.id}/edit",
            application=application,
            errors=errors,
        ), 400

    db = get_db_session()

    duplicate = db.exec(
        select(JobApplication).where(
            JobApplication.user_id == current_user.id,
            JobApplication.company == data["company"],
            JobApplication.position == data["position"],
            JobApplication.id != application.id,
        )
    ).first()

    if duplicate:
        errors["duplicate"] = "You already saved this application."
        flash("You already saved this application.", "error")
        return render_template(
            "applications/form.html",
            form_action=f"/applications/{application.id}/edit",
            application=application,
            errors=errors,
        ), 409

    for key, value in data.items():
        setattr(application, key, value)

    db.add(application)
    db.commit()
    db.refresh(application)

    flash("Application updated.", "success")
    return redirect(f"/applications/{application.id}")


@app.route("/applications/<int:app_id>/delete", methods=["POST"])
@login_required
def applications_delete(app_id):
    application = get_owned_application(app_id)
    db = get_db_session()

    db.delete(application)
    db.commit()

    flash("Application deleted.", "success")
    return redirect("/applications")


@app.route("/applications/<int:app_id>/insight")
@login_required
def applications_insight(app_id):
    application = get_owned_application(app_id)
    db = get_db_session()

    insight = refresh_insight(db, application.company)

    if insight is None:
        flash("Company data temporarily unavailable.", "warning")

    return redirect(f"/applications/{application.id}")

# ---------------------------------------------------------------------------
# First-run schema creation
# ---------------------------------------------------------------------------

# DEVELOPMENT ONLY: this creates missing tables automatically for the current
# classroom skeleton. Once the schema is finalized, replace this with Alembic
# migrations and make `alembic upgrade head` the official database update path.
SQLModel.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
