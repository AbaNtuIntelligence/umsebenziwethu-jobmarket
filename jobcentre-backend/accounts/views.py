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
from .serializers import AccountDeleteSerializer, EmployerProfileSerializer, JobSeekerProfileSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, RegisterSerializer, TalentDirectorySerializer, UserSerializer

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

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

class AccountDeleteView(APIView):
    def post(self, request):
        serializer = AccountDeleteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.delete()
        return Response(status=204)

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
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
