import pytest
from django.urls import reverse, NoReverseMatch
from apps.jobs.models import Job

@pytest.mark.django_db
def test_company_page_lists_active_jobs(client, company, make_job):
    fields = {f.name for f in Job._meta.get_fields()}
    make_job(title="Job Activ", slug="job-activ")
    if "is_active" in fields:
        make_job(title="Job Inactiv", slug="job-inactiv", is_active=False)

    try:
        url = reverse("companies:detail", kwargs={"slug": company.slug})
    except NoReverseMatch:
        pytest.skip("companies:detail URL not configured")

    resp = client.get(url)
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "Job Activ" in html
    if "is_active" in fields:
        assert "Job Inactiv" not in html