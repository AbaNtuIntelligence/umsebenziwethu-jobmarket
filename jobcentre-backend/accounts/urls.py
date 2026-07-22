from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import AccountDeleteView, MeView, PasswordResetConfirmView, PasswordResetRequestView, ProfileView, RegisterView, TalentDirectoryView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("job-seekers/", TalentDirectoryView.as_view(), name="job-seeker-directory"),
    path("delete-account/", AccountDeleteView.as_view(), name="delete-account"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
