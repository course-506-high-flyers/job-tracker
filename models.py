from datetime import date, datetime, timezone

from flask_login import UserMixin
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, UserMixin, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(sa_column=Column(String(80), nullable=False, unique=True, index=True))
    password_hash: str = Field(sa_column=Column(String(256), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class JobApplication(SQLModel, table=True):
    __tablename__ = "job_applications"
    __table_args__ = (
        UniqueConstraint("user_id", "company", "position", name="uq_job_applications_user_company_position"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    company: str = Field(sa_column=Column(String(120), nullable=False))
    position: str = Field(sa_column=Column(String(120), nullable=False))
    status: str = Field(default="applied", sa_column=Column(String(30), nullable=False, server_default="applied"))
    applied_date: date = Field(nullable=False)
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    job_url: str | None = Field(default=None, sa_column=Column(String(500), nullable=True))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class JobInsight(SQLModel, table=True):
    __tablename__ = "job_insights"

    id: int | None = Field(default=None, primary_key=True)
    company: str = Field(sa_column=Column(String(120), nullable=False, unique=True))
    rating: float | None = Field(default=None)
    review_count: int | None = Field(default=None)
    industry: str | None = Field(default=None, sa_column=Column(String(120), nullable=True))
    headquarters: str | None = Field(default=None, sa_column=Column(String(200), nullable=True))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    fetched_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class OAuthIdentity(SQLModel, table=True):
    __tablename__ = "oauth_identity"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_identity_provider_user_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    provider: str = Field(sa_column=Column(String(50), nullable=False))
    provider_user_id: str = Field(sa_column=Column(String(255), nullable=False))
    provider_login: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    provider_email: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
