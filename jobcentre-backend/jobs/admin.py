from django.contrib import admin
from django.utils import timezone
from .models import (
    Application,
    ApplicationDocument,
    ApplicationStatusHistory,
    Feedback,
    Interview,
    InterviewEvent,
    Job,
    JobLocationReport,
    JobMedia,
    JobReport,
    Notification,
    Placement,
    PlacementConfirmation,
    PlacementFollowUp,
    PlacementResolution,
    RecruitmentSession,
    RecruitmentSessionParticipant,
    SavedJob,
)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "city", "municipality", "location_review_status", "urgent", "closing_date", "status")
    list_filter = ("status", "location_review_status", "address_visibility", "location_precision", "street_view_enabled", "urgent", "employment_type", "province", "district")
    search_fields = ("title", "employer__employer_profile__organisation_name", "city", "suburb", "municipality", "district", "postal_code", "public_location")
    actions = ("publish_jobs", "close_jobs", "mark_locations_reviewed", "mark_locations_needing_changes")
    fieldsets = (
        ("Opportunity", {"fields": ("employer", "title", "category", "description", "requirements", "employment_type", "workplace", "positions_available", "urgent", "closing_date", "status", "rejection_reason")}),
        ("Public area", {"fields": ("province", "district", "municipality", "city", "suburb", "postal_code", "public_location")}),
        ("Protected precise location", {"fields": ("street_address", "latitude", "longitude", "google_place_id", "location_precision", "address_visibility", "street_view_enabled")}),
        ("Location review", {"fields": ("location_review_status", "location_confirmed_by_employer_at", "location_verified_by_admin_at")}),
        ("Pay and timestamps", {"fields": ("salary_min", "salary_max", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "location_confirmed_by_employer_at", "location_verified_by_admin_at")
    @admin.action(description="Publish selected jobs")
    def publish_jobs(self, request, queryset):
        queryset.update(status=Job.Status.PUBLISHED)
    @admin.action(description="Close selected jobs")
    def close_jobs(self, request, queryset):
        queryset.update(status=Job.Status.CLOSED)
    @admin.action(description="Mark selected locations as reviewed")
    def mark_locations_reviewed(self, request, queryset):
        queryset.update(location_review_status=Job.LocationReviewStatus.REVIEWED, location_verified_by_admin_at=timezone.now())
    @admin.action(description="Mark selected locations as needing changes")
    def mark_locations_needing_changes(self, request, queryset):
        queryset.update(location_review_status=Job.LocationReviewStatus.NEEDS_CHANGES, location_verified_by_admin_at=None)

admin.site.register(Application)
admin.site.register(SavedJob)
admin.site.register(JobMedia)
admin.site.register(ApplicationDocument)
admin.site.register(JobReport)
admin.site.register(JobLocationReport)
admin.site.register(Feedback)
admin.site.register(ApplicationStatusHistory)
admin.site.register(Notification)
admin.site.register(Interview)
admin.site.register(InterviewEvent)
admin.site.register(RecruitmentSession)
admin.site.register(RecruitmentSessionParticipant)


class PlacementConfirmationInline(admin.TabularInline):
    model = PlacementConfirmation
    extra = 0
    readonly_fields = ("responded_at",)


class PlacementFollowUpInline(admin.TabularInline):
    model = PlacementFollowUp
    extra = 0
    readonly_fields = ("created_at",)


class PlacementResolutionInline(admin.TabularInline):
    model = PlacementResolution
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "verification_status",
        "expected_start_date",
        "actual_start_date",
        "ended_at",
    )
    list_filter = ("verification_status", "employment_type")
    search_fields = (
        "application__reference",
        "application__job__title",
        "application__applicant__email",
        "application__job__employer__email",
    )
    readonly_fields = ("created_at", "updated_at")
    inlines = (PlacementConfirmationInline, PlacementFollowUpInline, PlacementResolutionInline)


@admin.register(PlacementConfirmation)
class PlacementConfirmationAdmin(admin.ModelAdmin):
    list_display = ("placement", "respondent_role", "response", "responded_at")
    list_filter = ("respondent_role", "response")
    readonly_fields = ("responded_at",)


@admin.register(PlacementFollowUp)
class PlacementFollowUpAdmin(admin.ModelAdmin):
    list_display = ("placement", "follow_up_type", "due_date", "employment_status", "completed_at")
    list_filter = ("follow_up_type", "employment_status")
    readonly_fields = ("created_at",)


@admin.register(PlacementResolution)
class PlacementResolutionAdmin(admin.ModelAdmin):
    list_display = ("placement", "previous_status", "resolved_status", "resolved_by", "created_at")
    list_filter = ("resolved_status",)
    readonly_fields = ("created_at",)
