from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .models import EmployerProfile, JobSeekerProfile, User
from .phone_otp import normalize_phone

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    avatar = serializers.ImageField(write_only=True, required=False, allow_null=True)
    organisation_name = serializers.CharField(write_only=True, required=False)
    accept_terms = serializers.BooleanField(write_only=True)
    invite_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    professional_headline = serializers.CharField(write_only=True, required=False, allow_blank=True)
    sector = serializers.CharField(write_only=True, required=False, allow_blank=True)
    industry = serializers.CharField(write_only=True, required=False, allow_blank=True)
    skills = serializers.CharField(write_only=True, required=False, allow_blank=True)
    province = serializers.CharField(write_only=True, required=False, allow_blank=True)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True)
    availability = serializers.CharField(write_only=True, required=False, allow_blank=True)
    resume = serializers.FileField(write_only=True, required=False, allow_null=True)
    directory_visible = serializers.BooleanField(write_only=True, required=False, default=False)
    directory_show_avatar = serializers.BooleanField(write_only=True, required=False, default=False)
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "phone", "role", "avatar", "password", "organisation_name", "professional_headline", "sector", "industry", "skills", "province", "city", "availability", "resume", "directory_visible", "directory_show_avatar", "accept_terms", "invite_code")
        read_only_fields = ("id",)
    def validate(self, attrs):
        if not attrs.get("accept_terms"):
            raise serializers.ValidationError({"accept_terms": "You must accept the Terms and Privacy Notice."})
        if settings.PILOT_INVITE_CODE and attrs.get("invite_code") != settings.PILOT_INVITE_CODE:
            raise serializers.ValidationError({"invite_code": "A valid pilot invitation code is required."})
        if attrs.get("role") == User.Role.EMPLOYER and not attrs.get("organisation_name"):
            raise serializers.ValidationError({"organisation_name": "Required for employers."})
        if not attrs.get("phone"):
            raise serializers.ValidationError({"phone": "A mobile number is required for account safety."})
        try:
            attrs["phone"] = normalize_phone(attrs["phone"])
        except Exception as error:
            raise serializers.ValidationError({"phone": error.messages if hasattr(error, "messages") else str(error)})
        resume = attrs.get("resume")
        if resume:
            if getattr(resume, "content_type", "") != "application/pdf":
                raise serializers.ValidationError({"resume": "Upload your résumé as a PDF file."})
            if resume.size > 5 * 1024 * 1024:
                raise serializers.ValidationError({"resume": "Résumé must be 5 MB or smaller."})
        avatar = attrs.get("avatar")
        if avatar:
            allowed = {"image/jpeg", "image/png", "image/webp"}
            if getattr(avatar, "content_type", "") not in allowed:
                raise serializers.ValidationError({"avatar": "Use a JPG, PNG or WebP image."})
            if avatar.size > 3 * 1024 * 1024:
                raise serializers.ValidationError({"avatar": "Profile image must be 3 MB or smaller."})
        return attrs
    def create(self, validated_data):
        validated_data.pop("accept_terms")
        validated_data.pop("invite_code", None)
        organisation_name = validated_data.pop("organisation_name", "")
        seeker_data = {
            key: validated_data.pop(key, "")
            for key in ("professional_headline", "sector", "industry", "skills", "province", "city", "availability", "directory_visible", "directory_show_avatar")
        }
        resume = validated_data.pop("resume", None)
        user = User.objects.create_user(**validated_data, terms_accepted_at=timezone.now())
        if user.role == User.Role.EMPLOYER:
            EmployerProfile.objects.create(user=user, organisation_name=organisation_name)
        else:
            JobSeekerProfile.objects.create(user=user, resume=resume, **seeker_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "phone", "phone_verified_at", "role", "avatar", "email_verified", "terms_accepted_at", "email_notifications", "sms_notifications", "whatsapp_notifications", "date_joined")
        read_only_fields = ("id", "email", "phone_verified_at", "role", "email_verified", "terms_accepted_at", "date_joined")
    def validate_phone(self, value):
        try:
            return normalize_phone(value)
        except Exception as error:
            raise serializers.ValidationError(error.messages if hasattr(error, "messages") else str(error))
    def update(self, instance, validated_data):
        new_phone = validated_data.get("phone")
        if new_phone and new_phone != instance.phone:
            instance.phone_verified_at = None
        return super().update(instance, validated_data)
    def validate_avatar(self, value):
        if value is None:
            return value
        allowed = {"image/jpeg", "image/png", "image/webp"}
        if getattr(value, "content_type", "") not in allowed:
            raise serializers.ValidationError("Use a JPG, PNG or WebP image.")
        if value.size > 3 * 1024 * 1024:
            raise serializers.ValidationError("Profile image must be 3 MB or smaller.")
        return value

class AccountDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm = serializers.CharField(write_only=True)
    def validate(self, attrs):
        if attrs["confirm"] != "DELETE":
            raise serializers.ValidationError({"confirm": "Type DELETE to confirm."})
        if not self.context["request"].user.check_password(attrs["password"]):
            raise serializers.ValidationError({"password": "Incorrect password."})
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PhoneOTPVerifySerializer(serializers.Serializer):
    code = serializers.RegexField(r"^\d{6}$", error_messages={"invalid": "Enter the six-digit code."})

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    def validate(self, attrs):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(attrs["uid"])))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError({"token": "Invalid or expired reset link."})
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired reset link."})
        attrs["user"] = user
        return attrs

class EmployerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    class Meta:
        model = EmployerProfile
        fields = "__all__"
        read_only_fields = ("user", "is_verified", "created_at")

class JobSeekerProfileSerializer(serializers.ModelSerializer):
    resume = serializers.FileField(required=False, allow_null=True)
    class Meta:
        model = JobSeekerProfile
        fields = "__all__"
        read_only_fields = ("user", "created_at")
    def validate_resume(self, value):
        if value is None:
            return value
        if getattr(value, "content_type", "") != "application/pdf":
            raise serializers.ValidationError("Upload your résumé as a PDF file.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Résumé must be 5 MB or smaller.")
        return value

class TalentDirectorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = JobSeekerProfile
        fields = (
            "id", "name", "avatar", "professional_headline", "sector",
            "industry", "skills", "province", "city", "availability", "bio",
        )

    def get_name(self, obj):
        full_name = obj.user.get_full_name().strip()
        return full_name or obj.user.username

    def get_avatar(self, obj):
        if not obj.directory_show_avatar or not obj.user.avatar:
            return None
        request = self.context.get("request")
        url = obj.user.avatar.url
        return request.build_absolute_uri(url) if request else url
