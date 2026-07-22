from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .models import EmployerProfile, JobSeekerProfile, User
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AccountDeleteSerializer, EmployerProfileSerializer, JobSeekerProfileSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PhoneOTPVerifySerializer, RegisterSerializer, TalentDirectorySerializer, UserSerializer
from .phone_otp import send_challenge, verify_challenge

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_scope = "registration"

class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"

class RefreshTokenView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "token_refresh"

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "token_refresh"

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response(status=204)

class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EmployerLogoDeleteView(APIView):
    def delete(self, request):
        if request.user.role != User.Role.EMPLOYER:
            raise PermissionDenied("Only employer accounts have a company logo.")
        if request.user.avatar:
            request.user.avatar = None
            request.user.save(update_fields=("avatar",))
        return Response(UserSerializer(request.user, context={"request": request}).data)


class PhoneOTPSendView(APIView):
    throttle_scope = "phone_otp_send"
    def post(self, request):
        if request.user.phone_verified_at:
            return Response({"detail": "Phone number is already verified.", "phone_verified": True})
        if not request.user.phone:
            raise ValidationError({"phone": "Add a mobile number to your profile first."})
        try:
            challenge = send_challenge(request.user)
        except Exception as error:
            raise ValidationError({"detail": error.messages if hasattr(error, "messages") else str(error)})
        return Response({"detail": "Verification code sent.", "expires_at": challenge.expires_at, "phone": challenge.phone})


class PhoneOTPVerifyView(APIView):
    throttle_scope = "phone_otp_verify"
    def post(self, request):
        serializer = PhoneOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = verify_challenge(request.user, serializer.validated_data["code"])
        except Exception as error:
            raise ValidationError({"code": error.messages if hasattr(error, "messages") else str(error)})
        return Response({"detail": "Phone number verified successfully.", "user": UserSerializer(user).data})

class ProfileView(APIView):
    def get_object_and_serializer(self, request):
        if request.user.role == User.Role.EMPLOYER:
            profile, _ = EmployerProfile.objects.get_or_create(user=request.user, defaults={"organisation_name": request.user.username})
            return profile, EmployerProfileSerializer
        profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
        return profile, JobSeekerProfileSerializer
    def get(self, request):
        obj, serializer_class = self.get_object_and_serializer(request)
        return Response(serializer_class(obj).data)
    def patch(self, request):
        obj, serializer_class = self.get_object_and_serializer(request)
        serializer = serializer_class(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class TalentDirectoryView(generics.ListAPIView):
    serializer_class = TalentDirectorySerializer
    throttle_scope = "talent_directory"

    def get_queryset(self):
        if self.request.user.role != User.Role.EMPLOYER:
            raise PermissionDenied("Only employer accounts can browse job seekers.")

        queryset = JobSeekerProfile.objects.filter(
            directory_visible=True,
            user__is_active=True,
        ).select_related("user").order_by("-created_at")

        search = self.request.query_params.get("search", "").strip()
        sector = self.request.query_params.get("sector", "").strip()
        industry = self.request.query_params.get("industry", "").strip()
        province = self.request.query_params.get("province", "").strip()

        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(professional_headline__icontains=search)
                | Q(skills__icontains=search)
                | Q(sector__icontains=search)
                | Q(industry__icontains=search)
                | Q(city__icontains=search)
            )
        if sector:
            queryset = queryset.filter(sector__iexact=sector)
        if industry:
            queryset = queryset.filter(industry__iexact=industry)
        if province:
            queryset = queryset.filter(province__iexact=province)
        return queryset

class TalentProfileView(generics.RetrieveAPIView):
    serializer_class = TalentDirectorySerializer
    throttle_scope = "talent_directory"

    def get_queryset(self):
        if self.request.user.role != User.Role.EMPLOYER:
            raise PermissionDenied("Only employer accounts can view job-seeker profiles.")
        return JobSeekerProfile.objects.filter(
            directory_visible=True,
            user__is_active=True,
        ).select_related("user")

class AccountDeleteView(APIView):
    def post(self, request):
        serializer = AccountDeleteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.delete()
        return Response(status=204)

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
            send_mail("Reset your Job Centre password", f"Use this link to reset your password:\n\n{link}\n\nIf you did not request this, ignore this email.", settings.DEFAULT_FROM_EMAIL, [user.email])
        return Response({"detail": "If the account exists, a reset link has been sent."})

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated successfully."})
