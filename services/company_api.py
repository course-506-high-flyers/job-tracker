import os
import requests
from datetime import datetime, timedelta, timezone

from sqlmodel import select

from models import JobInsight


CLEARBIT_URL = "https://company.clearbit.com/v2/companies/find"
API_NINJAS_URL = "https://api.api-ninjas.com/v1/company"
TIMEOUT = 5


def get_cached_insight(db, company_name):
    existing = db.exec(
        select(JobInsight).where(JobInsight.company == company_name)
    ).first()

    if not existing:
        return None

    if existing.fetched_at >= datetime.now(timezone.utc) - timedelta(hours=24):
        return existing

    return None


def fetch_company_insight(company_name):
    clearbit_key = os.environ.get("CLEARBIT_API_KEY")
    ninjas_key = os.environ.get("API_NINJAS_KEY")

    if clearbit_key:
        try:
            resp = requests.get(
                CLEARBIT_URL,
                params={"domain": company_name.lower().replace(" ", "") + ".com"},
                headers={"Authorization": f"Bearer {clearbit_key}"},
                timeout=TIMEOUT,
            )

            if resp.ok:
                data = resp.json()
                return {
                    "company": company_name,
                    "rating": None,
                    "review_count": None,
                    "industry": data.get("category", {}).get("industry"),
                    "headquarters": data.get("location"),
                    "description": data.get("description"),
                }
        except Exception:
            pass

    if ninjas_key:
        try:
            resp = requests.get(
                API_NINJAS_URL,
                params={"name": company_name},
                headers={"X-Api-Key": ninjas_key},
                timeout=TIMEOUT,
            )

            if resp.ok:
                data = resp.json()
                if data:
                    item = data[0]
                    return {
                        "company": company_name,
                        "rating": None,
                        "review_count": None,
                        "industry": item.get("industry"),
                        "headquarters": item.get("headquarters"),
                        "description": item.get("description"),
                    }
        except Exception:
            pass

    return None


def refresh_insight(db, company_name):
    data = fetch_company_insight(company_name)

    if not data:
        return None

    existing = db.exec(
        select(JobInsight).where(JobInsight.company == company_name)
    ).first()

    if existing:
        existing.rating = data["rating"]
        existing.review_count = data["review_count"]
        existing.industry = data["industry"]
        existing.headquarters = data["headquarters"]
        existing.description = data["description"]
        existing.fetched_at = datetime.now(timezone.utc)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    insight = JobInsight(**data)
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight