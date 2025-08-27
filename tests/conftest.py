import pytest
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.jobs.models import Job

User = get_user_model()

@pytest.fixture
def seeker(db):
    u = User.objects.create_user(username="seeker", email="s@example.com", password="test1234")
    if hasattr(u, "role"):
        u.role = "seeker"
        u.save()
    return u

@pytest.fixture
def employer(db):
    u = User.objects.create_user(username="employer", email="e@example.com", password="test1234")
    if hasattr(u, "role"):
        u.role = "employer"
        u.save()
    return u

@pytest.fixture
def company(db, employer):
    c = Company.objects.create(name="Exemplu SRL", slug="exemplu-srl", owner=employer)
    return c

def _create_job(company, **overrides):
    data = {
        "title": "Operator Logistică",
        "slug": slugify("operator-logistica"),
        "company": company,
    }
    # Optional/common fields
    field_names = {f.name for f in Job._meta.get_fields()}
    for fname in ("description", "location"):
        if fname in field_names:
            data[fname] = overrides.get(fname, "Descriere job")
    if "is_active" in field_names:
        data["is_active"] = overrides.get("is_active", True)
    if "category" in field_names:
        data["category"] = overrides.get("category", Job._meta.get_field("category").choices[0][0])
    # Ensure created_by if required
    if "created_by" in field_names:
        data["created_by"] = overrides.get("created_by", getattr(company, "owner", None))
    data.update(overrides)
    return Job.objects.create(**data)

@pytest.fixture
def job(db, company):
    # Ensure unique slug per test run
    base_slug = slugify("operator-logistica")
    i = Job.objects.count() + 1
    return _create_job(company, slug=f"{base_slug}-{i}")

@pytest.fixture
def make_job(company):
    def _make(**overrides):
        return _create_job(company, **overrides)
    return _make
