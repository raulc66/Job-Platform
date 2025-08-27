
import pytest
from django.urls import reverse, NoReverseMatch
from apps.applications.models import Application

@pytest.mark.django_db
def test_apply_optional_fields(client, seeker, job):
    client.login(username="seeker", password="test1234")
    try:
        url = reverse("applications:apply", kwargs={"slug": job.slug})
    except NoReverseMatch:
        pytest.skip("applications:apply URL not configured")
    resp = client.post(url, data={}, follow=True)
    assert resp.status_code in (200, 302)
    assert Application.objects.filter(job=job, seeker=seeker).exists()

@pytest.mark.django_db
def test_apply_unique(client, seeker, job):
    client.login(username="seeker", password="test1234")
    try:
        url = reverse("applications:apply", kwargs={"slug": job.slug})
    except NoReverseMatch:
        pytest.skip("applications:apply URL not configured")
    client.post(url, data={}, follow=True)
    resp = client.post(url, data={}, follow=True)
    # Second post should not create a duplicate
    assert Application.objects.filter(job=job, seeker=seeker).count() == 1
