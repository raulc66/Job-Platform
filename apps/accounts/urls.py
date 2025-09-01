from django.urls import path
from .views import LoginView, LogoutView, SignupView, quick_profile, profile_edit, quick_apply_prep

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("quick-profile/", quick_profile, name="quick_profile"),
    path("profile/", profile_edit, name="profile_edit"),
    path("quick-apply-prep/", quick_apply_prep, name="quick_apply_prep"),
]