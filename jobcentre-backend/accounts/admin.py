from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AuthenticationEvent, EmployerProfile, JobSeekerProfile, SocialIdentity, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Job Centre", {"fields": ("role", "phone", "avatar", "email_verified", "terms_accepted_at", "last_auth_provider", "email_notifications", "sms_notifications", "whatsapp_notifications")}),)
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

@admin.register(SocialIdentity)
class SocialIdentityAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "email_at_link", "linked_at", "last_used_at")
    search_fields = ("user__email", "email_at_link", "subject")
    readonly_fields = ("user", "provider", "subject", "email_at_link", "linked_at", "last_used_at")
    def has_add_permission(self, request):
        return False


@admin.register(AuthenticationEvent)
class AuthenticationEventAdmin(admin.ModelAdmin):
    list_display = ("event", "provider", "email", "user", "ip_address", "created_at")
    list_filter = ("event", "provider")
    search_fields = ("email", "user__email")
    readonly_fields = ("user", "event", "provider", "email", "ip_address", "user_agent", "created_at")
    def has_add_permission(self, request):
        return False
