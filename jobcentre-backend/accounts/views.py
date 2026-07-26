from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import update_last_login
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .models import AuthenticationEvent, EmployerProfile, JobSeekerProfile, SocialIdentity, User
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AccountDeleteSerializer, EmployerProfileSerializer, JobSeekerProfileSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, RegisterSerializer, SocialAuthSerializer, TalentDirectorySerializer, UserSerializer
from .social_auth import verify_social_token

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_scope = "registration"

class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"


def unique_username(email):
    base = email.split("@", 1)[0][:120] or "member"
    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        suffix += 1
        candidate = f"{base[:140 - len(str(suffix))]}-{suffix}"
    return candidate


def authentication_event(request, event, provider, email, user=None):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip_address = (forwarded.split(",", 1)[0].strip() if forwarded else request.META.get("REMOTE_ADDR")) or None
    AuthenticationEvent.objects.create(
        user=user,
        event=event,
        provider=provider,
        email=email,
        ip_address=ip_address,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )


class SocialAuthView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "social_auth"

    @transaction.atomic
    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        provider = data["provider"]
        claims = verify_social_token(provider, data["id_token"])

        identity = SocialIdentity.objects.select_related("user").filter(
            provider=provider,
            subject=claims["subject"],
        ).first()
        created = False
        linked = False

        if identity:
            user = identity.user
            identity.save(update_fields=("last_used_at",))
        else:
            user = User.objects.filter(email__iexact=claims["email"]).first()
            if user:
                if not user.has_usable_password():
                    return Response(
                        {
                            "code": "use_linked_provider",
                            "detail": "This email is already registered with another sign-in provider. Sign in with the provider already linked to the account.",
                        },
                        status=409,
                    )
                if user.has_usable_password() and not data.get("link_password"):
                    return Response(
                        {
                            "code": "link_required",
                            "detail": "This email already has an account. Enter its current password once to link it safely.",
                            "email": claims["email"],
                            "provider": provider,
                        },
                        status=409,
                    )
                if user.has_usable_password() and not user.check_password(data.get("link_password", "")):
                    authentication_event(request, AuthenticationEvent.Event.LINK_FAILED, provider, claims["email"], user)
                    return Response(
                        {"errors": {"link_password": ["The existing account password is incorrect."]}},
                        status=400,
                    )
                linked = True
            else:
                if not data.get("role") or not data.get("accept_terms"):
                    return Response(
                        {
                            "code": "registration_required",
                            "detail": "Choose an account type and accept the Terms and Privacy Notice to continue.",
                        },
                        status=409,
                    )
                user = User(
                    email=claims["email"],
                    username=unique_username(claims["email"]),
                    first_name=claims["first_name"],
                    last_name=claims["last_name"],
                    role=data["role"],
                    email_verified=claims["email_verified"],
                    terms_accepted_at=timezone.now(),
                )
                user.set_unusable_password()
                user.save()
                if user.role == User.Role.EMPLOYER:
                    EmployerProfile.objects.create(
                        user=user,
                        organisation_name=data.get("organisation_name", "").strip(),
                    )
                else:
                    JobSeekerProfile.objects.create(user=user)
                created = True

            SocialIdentity.objects.create(
                user=user,
                provider=provider,
                subject=claims["subject"],
                email_at_link=claims["email"],
            )

        if not user.is_active:
            raise PermissionDenied("This account has been deactivated.")

        updates = []
        if claims["email_verified"] and not user.email_verified:
            user.email_verified = True
            updates.append("email_verified")
        user.last_auth_provider = provider
        updates.append("last_auth_provider")
        user.save(update_fields=updates)
        update_last_login(None, user)

        event = AuthenticationEvent.Event.SIGN_UP if created else (
            AuthenticationEvent.Event.LINK if linked else AuthenticationEvent.Event.SIGN_IN
        )
        authentication_event(request, event, provider, claims["email"], user)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user, context={"request": request}).data,
                "created": created,
                "linked": linked,
            }
        )

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
