from django.urls import path
from .views import AccountDeleteView, EmployerLogoDeleteView, LoginView, LogoutView, MeView, PasswordResetConfirmView, PasswordResetRequestView, ProfileView, RefreshTokenView, RegisterView, SocialAuthView, TalentDirectoryView, TalentProfileView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("social/", SocialAuthView.as_view(), name="social-auth"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("employer-logo/", EmployerLogoDeleteView.as_view(), name="employer-logo-delete"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("job-seekers/", TalentDirectoryView.as_view(), name="job-seeker-directory"),
    path("job-seekers/<int:pk>/", TalentProfileView.as_view(), name="job-seeker-profile"),
    path("delete-account/", AccountDeleteView.as_view(), name="delete-account"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
