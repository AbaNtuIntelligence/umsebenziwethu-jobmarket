from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .models import EmployerProfile, JobSeekerProfile, User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    organisation_name = serializers.CharField(write_only=True, required=False)
    accept_terms = serializers.BooleanField(write_only=True)
    invite_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "phone", "role", "password", "organisation_name", "accept_terms", "invite_code")
        read_only_fields = ("id",)
    def validate(self, attrs):
        if not attrs.get("accept_terms"):
            raise serializers.ValidationError({"accept_terms": "You must accept the Terms and Privacy Notice."})
        if settings.PILOT_INVITE_CODE and attrs.get("invite_code") != settings.PILOT_INVITE_CODE:
            raise serializers.ValidationError({"invite_code": "A valid pilot invitation code is required."})
        if attrs.get("role") == User.Role.EMPLOYER and not attrs.get("organisation_name"):
            raise serializers.ValidationError({"organisation_name": "Required for employers."})
        return attrs
    def create(self, validated_data):
        validated_data.pop("accept_terms")
        validated_data.pop("invite_code", None)
        organisation_name = validated_data.pop("organisation_name", "")
        user = User.objects.create_user(**validated_data, terms_accepted_at=timezone.now())
        if user.role == User.Role.EMPLOYER:
            EmployerProfile.objects.create(user=user, organisation_name=organisation_name)
        else:
            JobSeekerProfile.objects.create(user=user)
        return user

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "phone", "role", "avatar", "email_verified", "terms_accepted_at", "email_notifications", "sms_notifications", "whatsapp_notifications", "date_joined")
        read_only_fields = ("id", "email", "role", "email_verified", "terms_accepted_at", "date_joined")
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
    class Meta:
        model = JobSeekerProfile
        fields = "__all__"
        read_only_fields = ("user", "created_at")
