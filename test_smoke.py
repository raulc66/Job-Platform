import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_homepage(client):
    resp = client.get(reverse("jobs:list"))
    assert resp.status_code == 200

@pytest.mark.django_db
def test_login_page(client):
    resp = client.get(reverse("account_login"))
    assert resp.status_code == 200

@pytest.mark.django_db
def test_signup_page(client):
    resp = client.get(reverse("account_signup"))
    assert resp.status_code == 200