from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import EmployerProfile, JobSeekerProfile, PhoneOTPChallenge, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Job Centre", {"fields": ("role", "phone", "phone_verified_at", "avatar", "email_verified", "terms_accepted_at", "email_notifications", "sms_notifications", "whatsapp_notifications")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Job Centre", {"fields": ("email", "role", "phone")}),)
    list_display = ("email", "username", "role", "is_active", "date_joined")

@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ("organisation_name", "user", "is_verified", "created_at")
    list_filter = ("is_verified",)
    search_fields = ("organisation_name", "user__email")
    actions = ("verify_employers", "remove_verification")
    @admin.action(description="Verify selected employers")
    def verify_employers(self, request, queryset):
        queryset.update(is_verified=True)
    @admin.action(description="Remove verification")
    def remove_verification(self, request, queryset):
        queryset.update(is_verified=False)

admin.site.register(JobSeekerProfile)

@admin.register(PhoneOTPChallenge)
class PhoneOTPChallengeAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "delivery_status", "attempts", "expires_at", "consumed_at", "created_at")
    readonly_fields = ("user", "phone", "code_hash", "delivery_status", "provider_reference", "attempts", "max_attempts", "expires_at", "consumed_at", "created_at")
    def has_add_permission(self, request):
        return False
