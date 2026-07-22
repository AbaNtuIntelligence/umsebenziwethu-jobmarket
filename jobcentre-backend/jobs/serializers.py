from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from urllib.parse import urlencode
from .models import Application, ApplicationDocument, ApplicationStatusHistory, Feedback, Interview, InterviewEvent, Job, JobInvitation, JobLocationReport, JobMedia, JobReport, Notification, RecruitmentSession, RecruitmentSessionParticipant, SavedJob
from django.urls import reverse

ALLOWED_JOB_MEDIA = {
    "image/jpeg": (JobMedia.MediaType.IMAGE, 8 * 1024 * 1024),
    "image/png": (JobMedia.MediaType.IMAGE, 8 * 1024 * 1024),
    "image/webp": (JobMedia.MediaType.IMAGE, 8 * 1024 * 1024),
    "video/mp4": (JobMedia.MediaType.VIDEO, 50 * 1024 * 1024),
    "video/webm": (JobMedia.MediaType.VIDEO, 50 * 1024 * 1024),
    "application/pdf": (JobMedia.MediaType.PDF, 10 * 1024 * 1024),
}

class JobMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMedia
        fields = ("id", "file", "media_type", "caption", "created_at")
        read_only_fields = ("id", "media_type", "created_at")
    def validate_file(self, value):
        rule = ALLOWED_JOB_MEDIA.get(value.content_type)
        if not rule:
            raise serializers.ValidationError("Use JPG, PNG, WebP, MP4, WebM or PDF files only.")
        if value.size > rule[1]:
            raise serializers.ValidationError("File exceeds the allowed size for this type.")
        return value

class ApplicationDocumentSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    class Meta:
        model = ApplicationDocument
        fields = ("id", "file", "label", "created_at", "download_url")
        read_only_fields = ("id", "created_at", "download_url")
        extra_kwargs = {"file": {"write_only": True}}
    def get_download_url(self, obj):
        request = self.context.get("request")
        path = reverse("application-document-download", kwargs={"pk": obj.pk})
        return request.build_absolute_uri(path) if request else path
    def validate_file(self, value):
        if value.content_type != "application/pdf":
            raise serializers.ValidationError("Application documents must be PDF files.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("PDF must be 10 MB or smaller.")
        return value

class JobSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(source="employer.employer_profile.organisation_name", read_only=True)
    employer_verified = serializers.BooleanField(source="employer.employer_profile.is_verified", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    media = JobMediaSerializer(many=True, read_only=True)
    employer_avatar = serializers.SerializerMethodField()
    display_location = serializers.SerializerMethodField()
    exact_address = serializers.SerializerMethodField()
    map_url = serializers.SerializerMethodField()
    directions_url = serializers.SerializerMethodField()
    street_view_url = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = "__all__"
        read_only_fields = ("employer", "status", "created_at", "updated_at")
        extra_kwargs = {
            "street_address": {"write_only": True},
            "latitude": {"write_only": True},
            "longitude": {"write_only": True},
            "google_place_id": {"write_only": True},
            "location_review_status": {"read_only": True},
            "location_confirmed_by_employer_at": {"read_only": True},
            "location_verified_by_admin_at": {"read_only": True},
        }
    def get_employer_avatar(self, obj):
        if not obj.employer.avatar:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.employer.avatar.url) if request else obj.employer.avatar.url
    def get_display_location(self, obj):
        if obj.address_visibility == Job.AddressVisibility.HIDDEN:
            return "Location shared by the employer"
        if obj.public_location:
            return obj.public_location
        parts = [obj.suburb, obj.city, obj.municipality, obj.province]
        return ", ".join(dict.fromkeys(part for part in parts if part))
    def get_exact_address(self, obj):
        if obj.address_visibility == Job.AddressVisibility.EXACT:
            return obj.street_address or None
        return None
    def _maps_query(self, obj):
        if obj.address_visibility == Job.AddressVisibility.EXACT and obj.latitude is not None and obj.longitude is not None:
            return f"{obj.latitude},{obj.longitude}"
        return self.get_display_location(obj)
    def get_map_url(self, obj):
        if obj.address_visibility == Job.AddressVisibility.HIDDEN:
            return None
        query = self._maps_query(obj)
        if not query:
            return None
        params = {"api": 1, "query": query}
        if obj.address_visibility == Job.AddressVisibility.EXACT and obj.google_place_id:
            params["query_place_id"] = obj.google_place_id
        return f"https://www.google.com/maps/search/?{urlencode(params)}"
    def get_directions_url(self, obj):
        if obj.address_visibility != Job.AddressVisibility.EXACT:
            return None
        destination = self._maps_query(obj)
        if not destination:
            return None
        params = {"api": 1, "destination": destination}
        if obj.google_place_id:
            params["destination_place_id"] = obj.google_place_id
        return f"https://www.google.com/maps/dir/?{urlencode(params)}"
    def get_street_view_url(self, obj):
        if not obj.street_view_enabled or obj.address_visibility != Job.AddressVisibility.EXACT:
            return None
        if obj.latitude is None or obj.longitude is None:
            return None
        return "https://www.google.com/maps/@?" + urlencode({
            "api": 1,
            "map_action": "pano",
            "viewpoint": f"{obj.latitude},{obj.longitude}",
        })
    def get_distance_km(self, obj):
        distance = getattr(obj, "distance_km", None)
        return round(distance, 1) if distance is not None else None
    def validate_closing_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Closing date cannot be in the past.")
        return value
    def validate(self, attrs):
        low, high = attrs.get("salary_min"), attrs.get("salary_max")
        if low is not None and high is not None and low > high:
            raise serializers.ValidationError({"salary_max": "Must be greater than or equal to salary_min."})
        latitude = attrs.get("latitude", getattr(self.instance, "latitude", None))
        longitude = attrs.get("longitude", getattr(self.instance, "longitude", None))
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError({"location": "Latitude and longitude must be supplied together."})
        if latitude is not None and not -90 <= latitude <= 90:
            raise serializers.ValidationError({"latitude": "Latitude must be between -90 and 90."})
        if longitude is not None and not -180 <= longitude <= 180:
            raise serializers.ValidationError({"longitude": "Longitude must be between -180 and 180."})
        visibility = attrs.get("address_visibility", getattr(self.instance, "address_visibility", Job.AddressVisibility.AREA_ONLY))
        if visibility != Job.AddressVisibility.EXACT:
            attrs["street_view_enabled"] = False
        return attrs

class ApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source="job.title", read_only=True)
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    applicant_phone = serializers.CharField(source="applicant.phone", read_only=True)
    applicant_profile = serializers.SerializerMethodField()
    status_history = serializers.SerializerMethodField()
    applicant_avatar = serializers.SerializerMethodField()
    class Meta:
        model = Application
        fields = "__all__"
        read_only_fields = ("applicant", "status", "created_at", "updated_at")
    def get_applicant_name(self, obj):
        return obj.applicant.get_full_name() or obj.applicant.username
    def get_applicant_avatar(self, obj):
        if not obj.applicant.avatar:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.applicant.avatar.url) if request else obj.applicant.avatar.url
    def get_applicant_profile(self, obj):
        profile = getattr(obj.applicant, "job_seeker_profile", None)
        if not profile:
            return None
        return {"province": profile.province, "city": profile.city, "skills": profile.skills, "bio": profile.bio, "availability": profile.availability}
    def get_status_history(self, obj):
        return ApplicationStatusHistorySerializer(obj.status_history.all(), many=True).data

class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()
    class Meta:
        model = ApplicationStatusHistory
        fields = ("id", "from_status", "to_status", "message", "changed_by_name", "created_at")
    def get_changed_by_name(self, obj):
        if not obj.changed_by:
            return "Job Centre"
        return obj.changed_by.get_full_name() or obj.changed_by.username

class ApplicationStatusSerializer(serializers.ModelSerializer):
    message = serializers.CharField(write_only=True, required=False, allow_blank=True)
    class Meta:
        model = Application
        fields = ("status", "message")

class SubmitApplicationSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    cover_note = serializers.CharField(required=False, allow_blank=True)
    cv = serializers.FileField(required=False, allow_null=True)
    consent_to_share = serializers.BooleanField()
    def validate_consent_to_share(self, value):
        if not value:
            raise serializers.ValidationError("You must agree to share this application with the employer.")
        return value
    def validate_cv(self, value):
        if value is None:
            return value
        if value.content_type != "application/pdf":
            raise serializers.ValidationError("CV must be a PDF file.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("CV must be 10 MB or smaller.")
        return value

class NotificationSerializer(serializers.ModelSerializer):
    application_reference = serializers.CharField(source="application.reference", read_only=True)
    class Meta:
        model = Notification
        fields = ("id", "application", "job", "application_reference", "title", "message", "is_read", "created_at")
        read_only_fields = fields

class JobInvitationSerializer(serializers.ModelSerializer):
    candidate_profile = serializers.IntegerField(write_only=True)
    message = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    class Meta:
        model = JobInvitation
        fields = ("id", "job", "candidate_profile", "message", "created_at")
        read_only_fields = ("id", "created_at")

class SavedJobSerializer(serializers.ModelSerializer):
    job_detail = JobSerializer(source="job", read_only=True)
    class Meta:
        model = SavedJob
        fields = ("id", "job", "job_detail", "created_at")
        read_only_fields = ("id", "created_at")

class JobReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobReport
        fields = ("id", "job", "reason", "details", "created_at")
        read_only_fields = ("id", "created_at")


class JobLocationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobLocationReport
        fields = ("id", "job", "reason", "details", "created_at")
        read_only_fields = ("id", "created_at")

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ("id", "area", "rating", "message", "created_at")
        read_only_fields = ("id", "created_at")
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be from 1 to 5.")
        return value


class InterviewEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = InterviewEvent
        fields = ("id", "event_type", "actor_name", "note", "created_at")
        read_only_fields = fields

    def get_actor_name(self, obj):
        if not obj.actor:
            return "UmsebenziWethu"
        return obj.actor.get_full_name() or obj.actor.username


class InterviewSerializer(serializers.ModelSerializer):
    application_reference = serializers.CharField(source="application.reference", read_only=True)
    job_title = serializers.CharField(source="application.job.title", read_only=True)
    organisation_name = serializers.SerializerMethodField()
    candidate_name = serializers.SerializerMethodField()
    events = InterviewEventSerializer(many=True, read_only=True)
    can_join = serializers.SerializerMethodField()
    meeting_url = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = (
            "id", "application", "application_reference", "job_title", "organisation_name",
            "candidate_name", "provider", "title", "scheduled_start", "scheduled_end",
            "timezone_name", "join_url", "host_url", "provider_meeting_id", "instructions",
            "status", "candidate_response", "candidate_response_note", "recording_allowed",
            "events", "can_join", "meeting_url", "created_at", "updated_at",
        )
        read_only_fields = (
            "candidate_response", "candidate_response_note", "status", "events", "can_join",
            "meeting_url", "created_at", "updated_at",
        )
        extra_kwargs = {
            "join_url": {"write_only": True, "required": False},
            "host_url": {"write_only": True, "required": False},
            "provider_meeting_id": {"write_only": True, "required": False},
        }

    def get_organisation_name(self, obj):
        profile = getattr(obj.application.job.employer, "employer_profile", None)
        return profile.organisation_name if profile else (obj.application.job.employer.get_full_name() or obj.application.job.employer.username)

    def get_candidate_name(self, obj):
        candidate = obj.application.applicant
        return candidate.get_full_name() or candidate.username

    def _within_join_window(self, obj):
        now = timezone.now()
        return obj.scheduled_start - timedelta(minutes=15) <= now <= obj.scheduled_end + timedelta(minutes=30)

    def get_can_join(self, obj):
        request = self.context.get("request")
        if not request or obj.status != Interview.Status.SCHEDULED:
            return False
        if request.user.id == obj.application.job.employer_id:
            return True
        return request.user.id == obj.application.applicant_id and obj.candidate_response == Interview.CandidateResponse.ACCEPTED and self._within_join_window(obj)

    def get_meeting_url(self, obj):
        request = self.context.get("request")
        if not request or not self.get_can_join(obj):
            return None
        if request.user.id == obj.application.job.employer_id:
            return obj.host_url or obj.join_url or None
        return obj.join_url or None

    def validate(self, attrs):
        start = attrs.get("scheduled_start", getattr(self.instance, "scheduled_start", None))
        end = attrs.get("scheduled_end", getattr(self.instance, "scheduled_end", None))
        if start and end and end <= start:
            raise serializers.ValidationError({"scheduled_end": "The interview must end after it starts."})
        if start and not self.instance and start <= timezone.now():
            raise serializers.ValidationError({"scheduled_start": "Schedule the interview in the future."})
        if attrs.get("recording_allowed"):
            raise serializers.ValidationError({"recording_allowed": "Recording requires a separate consent workflow and is disabled for this pilot."})
        return attrs


class InterviewResponseSerializer(serializers.Serializer):
    response = serializers.ChoiceField(choices=("accepted", "declined", "reschedule"))
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class InterviewOutcomeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("completed", "employer_no_show", "candidate_no_show", "technical_failure", "cancelled"))
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class RecruitmentSessionParticipantSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentSessionParticipant
        fields = ("id", "user", "application", "name", "response", "responded_at", "joined_at")
        read_only_fields = fields

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class RecruitmentSessionSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    organisation_name = serializers.SerializerMethodField()
    participant_count = serializers.IntegerField(source="participants.count", read_only=True)
    my_response = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    meeting_url = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentSession
        fields = (
            "id", "job", "job_title", "organisation_name", "title", "description",
            "session_type", "visibility", "provider", "scheduled_start", "scheduled_end",
            "timezone_name", "join_url", "host_url", "provider_meeting_id", "capacity",
            "status", "recording_allowed", "participant_count", "my_response", "can_join",
            "meeting_url", "participants", "created_at", "updated_at",
        )
        read_only_fields = ("status", "participant_count", "my_response", "can_join", "meeting_url", "participants", "created_at", "updated_at")
        extra_kwargs = {
            "join_url": {"write_only": True, "required": False},
            "host_url": {"write_only": True, "required": False},
            "provider_meeting_id": {"write_only": True, "required": False},
        }

    def get_organisation_name(self, obj):
        profile = getattr(obj.host, "employer_profile", None)
        return profile.organisation_name if profile else (obj.host.get_full_name() or obj.host.username)

    def get_participants(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or (request.user.id != obj.host_id and not request.user.is_staff):
            return []
        return RecruitmentSessionParticipantSerializer(obj.participants.all(), many=True).data

    def _participant(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return next((item for item in obj.participants.all() if item.user_id == request.user.id), None)

    def get_my_response(self, obj):
        participant = self._participant(obj)
        return participant.response if participant else None

    def get_can_join(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or obj.status not in (RecruitmentSession.Status.SCHEDULED, RecruitmentSession.Status.LIVE):
            return False
        if request.user.id == obj.host_id:
            return True
        participant = self._participant(obj)
        authorised = obj.visibility == RecruitmentSession.Visibility.PUBLIC or (participant and participant.response in ("accepted", "attended"))
        now = timezone.now()
        return bool(authorised and obj.scheduled_start - timedelta(minutes=15) <= now <= obj.scheduled_end + timedelta(minutes=30))

    def get_meeting_url(self, obj):
        request = self.context.get("request")
        if not request or not self.get_can_join(obj):
            return None
        return (obj.host_url or obj.join_url) if request.user.id == obj.host_id else obj.join_url

    def validate(self, attrs):
        start, end = attrs.get("scheduled_start"), attrs.get("scheduled_end")
        if start and end and end <= start:
            raise serializers.ValidationError({"scheduled_end": "The session must end after it starts."})
        if start and not self.instance and start <= timezone.now():
            raise serializers.ValidationError({"scheduled_start": "Schedule the session in the future."})
        if attrs.get("visibility") == RecruitmentSession.Visibility.PUBLIC and attrs.get("session_type") != RecruitmentSession.SessionType.PUBLIC_BROADCAST:
            raise serializers.ValidationError({"visibility": "Only opportunity broadcasts may be public during the pilot."})
        if attrs.get("recording_allowed"):
            raise serializers.ValidationError({"recording_allowed": "Recording is disabled for this pilot."})
        return attrs


class SessionInviteSerializer(serializers.Serializer):
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.all())


class SessionResponseSerializer(serializers.Serializer):
    response = serializers.ChoiceField(choices=("accepted", "declined"))
