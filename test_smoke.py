import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_homepage(client):
    response = client.get(reverse('home'))  # Replace 'home' with your actual homepage URL name
    assert response.status_code == 200
    assert 'Welcome to JobBoard' in response.content.decode()  # Adjust the content check as needed

@pytest.mark.django_db
def test_login_page(client):
    response = client.get(reverse('login'))  # Replace 'login' with your actual login URL name
    assert response.status_code == 200
    assert 'Login' in response.content.decode()  # Adjust the content check as needed

@pytest.mark.django_db
def test_signup_page(client):
    response = client.get(reverse('signup'))  # Replace 'signup' with your actual signup URL name
    assert response.status_code == 200
    assert 'Sign Up' in response.content.decode()  # Adjust the content check as needed