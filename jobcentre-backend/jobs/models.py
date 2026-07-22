from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid

def application_reference():
    return f"APP-{timezone.localdate().year}-{uuid.uuid4().hex[:8].upper()}"

class Job(models.Model):
    class EmploymentType(models.TextChoices):
        PERMANENT = "permanent", "Permanent"
        CONTRACT = "contract", "Contract"
        TEMPORARY = "temporary", "Temporary"
        PART_TIME = "part_time", "Part-time"
        INTERNSHIP = "internship", "Internship"
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending review"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"
        REJECTED = "rejected", "Rejected"
    class LocationPrecision(models.TextChoices):
        PROVINCE = "province", "Province"
        DISTRICT = "district", "District"
        TOWN = "town", "Town or city"
        SUBURB = "suburb", "Suburb, township or village"
        STREET = "street", "Street"
        EXACT = "exact", "Exact address"
    class AddressVisibility(models.TextChoices):
        EXACT = "exact", "Show exact address"
        AREA_ONLY = "area_only", "Show area only"
        APPROXIMATE = "approximate", "Show approximate area"
        SHORTLISTED = "shortlisted", "Share after shortlisting"
        HIDDEN = "hidden", "Do not display"
    class LocationReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        REVIEWED = "reviewed", "Reviewed"
        NEEDS_CHANGES = "needs_changes", "Needs changes"
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    province = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=100, db_index=True)
    district = models.CharField(max_length=120, blank=True, db_index=True)
    municipality = models.CharField(max_length=120, blank=True, db_index=True)
    suburb = models.CharField(max_length=120, blank=True, db_index=True)
    postal_code = models.CharField(max_length=10, blank=True, db_index=True)
    street_address = models.CharField(max_length=250, blank=True)
    public_location = models.CharField(max_length=250, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_precision = models.CharField(max_length=20, choices=LocationPrecision.choices, default=LocationPrecision.TOWN)
    address_visibility = models.CharField(max_length=30, choices=AddressVisibility.choices, default=AddressVisibility.AREA_ONLY)
    street_view_enabled = models.BooleanField(default=False)
    google_place_id = models.CharField(max_length=200, blank=True)
    location_review_status = models.CharField(max_length=20, choices=LocationReviewStatus.choices, default=LocationReviewStatus.PENDING, db_index=True)
    location_confirmed_by_employer_at = models.DateTimeField(null=True, blank=True)
    location_verified_by_admin_at = models.DateTimeField(null=True, blank=True)
    workplace = models.CharField(max_length=20, choices=(("onsite", "On-site"), ("hybrid", "Hybrid"), ("remote", "Remote")), default="onsite")
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    positions_available = models.PositiveIntegerField(default=1)
    urgent = models.BooleanField(default=False, db_index=True)
    closing_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ("-urgent", "-created_at")
        indexes = [models.Index(fields=("status", "closing_date"))]
    @property
    def is_expired(self):
        return self.closing_date < timezone.localdate()

class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        REVIEWING = "reviewing", "Reviewing"
        SHORTLISTED = "shortlisted", "Shortlisted"
        INTERVIEW = "interview", "Interview"
        UNSUCCESSFUL = "unsuccessful", "Unsuccessful"
        HIRED = "hired", "Hired"
        WITHDRAWN = "withdrawn", "Withdrawn"
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    cover_note = models.TextField(blank=True)
    reference = models.CharField(max_length=30, db_index=True, default=application_reference, editable=False)
    sharing_consent_at = models.DateTimeField(default=timezone.now)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("job", "applicant"), name="one_application_per_job")]
        ordering = ("-created_at",)

class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "job"), name="one_saved_job_per_user")]

def job_media_path(instance, filename):
    return f"jobs/{instance.job_id}/{filename}"

class JobMedia(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        PDF = "pdf", "PDF"
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to=job_media_path)
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

def application_document_path(instance, filename):
    return f"applications/{instance.application_id}/{filename}"

class ApplicationDocument(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=application_document_path)
    label = models.CharField(max_length=100, default="CV")
    created_at = models.DateTimeField(auto_now_add=True)

class ApplicationStatusHistory(models.Model):
    class ActorRole(models.TextChoices):
        EMPLOYER = "employer", "Employer"
        JOB_SEEKER = "job_seeker", "Job seeker"
        ADMIN = "admin", "Administrator"
        SYSTEM = "system", "System"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, choices=Application.Status.choices)
    message = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="application_status_changes")
    actor_role = models.CharField(max_length=20, choices=ActorRole.choices, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ("created_at",)


class Placement(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending confirmation"
        EMPLOYER_CONFIRMED = "employer_confirmed", "Employer confirmed"
        SEEKER_CONFIRMED = "seeker_confirmed", "Job seeker confirmed"
        CONFIRMED = "confirmed", "Confirmed by both parties"
        DISPUTED = "disputed", "Disputed"
        UNABLE_TO_VERIFY = "unable_to_verify", "Unable to verify"
        CANCELLED = "cancelled", "Cancelled"

    class VerificationMethod(models.TextChoices):
        IN_APP = "in_app", "In-app confirmation"
        ADMIN_REVIEW = "admin_review", "Administrator review"
        DOCUMENT = "document", "Supporting document"

    application = models.OneToOneField(
        Application,
        on_delete=models.PROTECT,
        related_name="placement",
    )
    expected_start_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True, db_index=True)
    employment_type = models.CharField(
        max_length=20,
        choices=Job.EmploymentType.choices,
        blank=True,
    )
    verification_status = models.CharField(
        max_length=24,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    verification_method = models.CharField(
        max_length=20,
        choices=VerificationMethod.choices,
        blank=True,
    )
    ended_at = models.DateField(null=True, blank=True)
    ending_reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("verification_status", "actual_start_date")),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(actual_start_date__isnull=True)
                    | models.Q(ended_at__isnull=True)
                    | models.Q(ended_at__gte=models.F("actual_start_date"))
                ),
                name="placement_end_not_before_start",
            ),
        ]

    @property
    def is_confirmed_start(self):
        return bool(
            self.actual_start_date
            and self.verification_status == self.VerificationStatus.CONFIRMED
        )


class PlacementConfirmation(models.Model):
    class RespondentRole(models.TextChoices):
        EMPLOYER = "employer", "Employer"
        JOB_SEEKER = "job_seeker", "Job seeker"

    class Response(models.TextChoices):
        STARTED = "started", "Started employment"
        ACCEPTED_NOT_STARTED = "accepted_not_started", "Accepted but not started"
        DID_NOT_ACCEPT = "did_not_accept", "Did not accept"
        INFORMATION_INCORRECT = "information_incorrect", "Information is incorrect"
        NO_LONGER_EMPLOYED = "no_longer_employed", "No longer employed"
        PREFER_NOT_TO_ANSWER = "prefer_not_to_answer", "Prefer not to answer"

    placement = models.ForeignKey(Placement, on_delete=models.CASCADE, related_name="confirmations")
    respondent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placement_confirmations",
    )
    respondent_role = models.CharField(max_length=20, choices=RespondentRole.choices)
    response = models.CharField(max_length=24, choices=Response.choices)
    confirmed_start_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    responded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("responded_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("placement", "respondent_role"),
                name="one_placement_confirmation_per_party",
            ),
        ]


class PlacementFollowUp(models.Model):
    class FollowUpType(models.TextChoices):
        DAY_30 = "30_day", "30-day follow-up"
        DAY_90 = "90_day", "90-day follow-up"

    class EmploymentStatus(models.TextChoices):
        STILL_EMPLOYED = "still_employed", "Still employed"
        ENDED = "ended", "Employment ended"
        UNKNOWN = "unknown", "Unknown"
        PREFER_NOT_TO_ANSWER = "prefer_not_to_answer", "Prefer not to answer"

    placement = models.ForeignKey(Placement, on_delete=models.CASCADE, related_name="follow_ups")
    follow_up_type = models.CharField(max_length=10, choices=FollowUpType.choices)
    due_date = models.DateField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    employment_status = models.CharField(
        max_length=24,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.UNKNOWN,
    )
    respondent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placement_follow_ups",
    )
    respondent_role = models.CharField(
        max_length=20,
        choices=PlacementConfirmation.RespondentRole.choices,
        blank=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("due_date",)
        constraints = [
            models.UniqueConstraint(
                fields=("placement", "follow_up_type"),
                name="one_follow_up_type_per_placement",
            ),
        ]


class PlacementResolution(models.Model):
    placement = models.ForeignKey(Placement, on_delete=models.CASCADE, related_name="resolutions")
    previous_status = models.CharField(max_length=24, choices=Placement.VerificationStatus.choices)
    resolved_status = models.CharField(max_length=24, choices=Placement.VerificationStatus.choices)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placement_resolutions",
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class MeetingProvider(models.TextChoices):
    EXTERNAL = "external", "External meeting link"
    ZOOM = "zoom", "Zoom"
    GOOGLE_MEET = "google_meet", "Google Meet"
    MICROSOFT_TEAMS = "microsoft_teams", "Microsoft Teams"
    WHATSAPP = "whatsapp", "WhatsApp"
    JITSI = "jitsi", "UmsebenziWethu Live / Jitsi"


class Interview(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        RESCHEDULE_REQUESTED = "reschedule_requested", "Reschedule requested"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
        EMPLOYER_NO_SHOW = "employer_no_show", "Employer did not attend"
        CANDIDATE_NO_SHOW = "candidate_no_show", "Candidate did not attend"
        TECHNICAL_FAILURE = "technical_failure", "Technical failure"

    class CandidateResponse(models.TextChoices):
        PENDING = "pending", "Awaiting response"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        RESCHEDULE = "reschedule", "Requested another time"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="interviews")
    provider = models.CharField(max_length=24, choices=MeetingProvider.choices)
    title = models.CharField(max_length=200, default="Job interview")
    scheduled_start = models.DateTimeField(db_index=True)
    scheduled_end = models.DateTimeField()
    timezone_name = models.CharField(max_length=64, default="Africa/Johannesburg")
    join_url = models.URLField(max_length=1000, blank=True)
    host_url = models.URLField(max_length=1000, blank=True)
    provider_meeting_id = models.CharField(max_length=200, blank=True)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    candidate_response = models.CharField(max_length=20, choices=CandidateResponse.choices, default=CandidateResponse.PENDING)
    candidate_response_note = models.TextField(blank=True)
    recording_allowed = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_interviews")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("scheduled_start",)
        indexes = [models.Index(fields=("status", "scheduled_start"))]
        constraints = [models.CheckConstraint(condition=models.Q(scheduled_end__gt=models.F("scheduled_start")), name="interview_end_after_start")]


class InterviewEvent(models.Model):
    class EventType(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        RESCHEDULED = "rescheduled", "Rescheduled"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        RESCHEDULE_REQUESTED = "reschedule_requested", "Reschedule requested"
        JOIN_REQUESTED = "join_requested", "Join requested"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
        EMPLOYER_NO_SHOW = "employer_no_show", "Employer no-show"
        CANDIDATE_NO_SHOW = "candidate_no_show", "Candidate no-show"
        TECHNICAL_FAILURE = "technical_failure", "Technical failure"

    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="interview_events")
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class RecruitmentSession(models.Model):
    class SessionType(models.TextChoices):
        GROUP_BRIEFING = "group_briefing", "Applicant group briefing"
        PUBLIC_BROADCAST = "public_broadcast", "Public opportunity broadcast"

    class Visibility(models.TextChoices):
        INVITED = "invited", "Invited applicants only"
        PUBLIC = "public", "Public"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="recruitment_sessions")
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="hosted_recruitment_sessions")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    session_type = models.CharField(max_length=24, choices=SessionType.choices)
    visibility = models.CharField(max_length=16, choices=Visibility.choices)
    provider = models.CharField(max_length=24, choices=MeetingProvider.choices)
    scheduled_start = models.DateTimeField(db_index=True)
    scheduled_end = models.DateTimeField()
    timezone_name = models.CharField(max_length=64, default="Africa/Johannesburg")
    join_url = models.URLField(max_length=1000, blank=True)
    host_url = models.URLField(max_length=1000, blank=True)
    provider_meeting_id = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(default=50)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    recording_allowed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("scheduled_start",)
        indexes = [models.Index(fields=("visibility", "status", "scheduled_start"))]
        constraints = [models.CheckConstraint(condition=models.Q(scheduled_end__gt=models.F("scheduled_start")), name="session_end_after_start")]


class RecruitmentSessionParticipant(models.Model):
    class Response(models.TextChoices):
        INVITED = "invited", "Invited"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        ATTENDED = "attended", "Attended"
        NO_SHOW = "no_show", "Did not attend"

    session = models.ForeignKey(RecruitmentSession, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recruitment_session_participation")
    application = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True, blank=True, related_name="recruitment_session_participation")
    response = models.CharField(max_length=16, choices=Response.choices, default=Response.INVITED)
    responded_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("session", "user"), name="one_participation_per_session_user")]

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ("-created_at",)

class JobInvitation(models.Model):
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_job_invitations")
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_invitations")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="candidate_invitations")
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("job", "candidate"), name="one_invitation_per_job_candidate"),
        ]

class JobReport(models.Model):
    class Reason(models.TextChoices):
        SCAM = "scam", "Suspected scam"
        PAYMENT = "payment", "Asked for payment"
        MISLEADING = "misleading", "Misleading information"
        DISCRIMINATION = "discrimination", "Discriminatory content"
        EXPIRED = "expired", "Expired or unavailable"
        OTHER = "other", "Other"
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="job_reports")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class JobLocationReport(models.Model):
    class Reason(models.TextChoices):
        WRONG_AREA = "wrong_area", "Pin is in the wrong area"
        ADDRESS_MISMATCH = "address_mismatch", "Address does not match the description"
        UNSAFE_OR_SUSPICIOUS = "unsafe_or_suspicious", "Location appears unsafe or suspicious"
        WORKPLACE_NOT_FOUND = "workplace_not_found", "Workplace does not exist"
        PRIVATE_ADDRESS_EXPOSED = "private_address_exposed", "A private address is exposed"
        OTHER = "other", "Other"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="location_reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="job_location_reports")
    reason = models.CharField(max_length=30, choices=Reason.choices)
    details = models.TextField(blank=True)
    resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

class Feedback(models.Model):
    class Area(models.TextChoices):
        REGISTRATION = "registration", "Registration"
        JOB_SEARCH = "job_search", "Job search"
        JOB_POSTING = "job_posting", "Job posting"
        APPLICATION = "application", "Application"
        OTHER = "other", "Other"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="feedback")
    area = models.CharField(max_length=20, choices=Area.choices)
    rating = models.PositiveSmallIntegerField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
