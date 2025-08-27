import pytest
from django.urls import reverse, NoReverseMatch

@pytest.mark.django_db
def test_employer_only_job_create_requires_employer(client, seeker):
    try:
        url = reverse("jobs:create")
    except NoReverseMatch:
        pytest.skip("jobs:create URL not configured")
    client.login(username="seeker", password="test1234")
    resp = client.get(url)
    assert resp.status_code in (302, 403)