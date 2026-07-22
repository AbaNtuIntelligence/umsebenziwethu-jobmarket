from django.urls import path
from .views import AccountDeleteView, LoginView, LogoutView, MeView, PasswordResetConfirmView, PasswordResetRequestView, PhoneOTPSendView, PhoneOTPVerifyView, ProfileView, RefreshTokenView, RegisterView, TalentDirectoryView, TalentProfileView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("phone-otp/send/", PhoneOTPSendView.as_view(), name="phone-otp-send"),
    path("phone-otp/verify/", PhoneOTPVerifyView.as_view(), name="phone-otp-verify"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("job-seekers/", TalentDirectoryView.as_view(), name="job-seeker-directory"),
    path("job-seekers/<int:pk>/", TalentProfileView.as_view(), name="job-seeker-profile"),
    path("delete-account/", AccountDeleteView.as_view(), name="delete-account"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
