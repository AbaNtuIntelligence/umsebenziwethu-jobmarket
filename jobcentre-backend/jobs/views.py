from django.db.models import Count, Q
from django.db import transaction
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import User
from math import asin, cos, radians, sin, sqrt
from .models import Application, ApplicationDocument, ApplicationStatusHistory, Feedback, Interview, InterviewEvent, Job, JobLocationReport, JobMedia, JobReport, Notification, RecruitmentSession, RecruitmentSessionParticipant, SavedJob
from .permissions import IsEmployer, IsJobOwnerOrReadOnly, IsJobSeeker
from .serializers import ApplicationDocumentSerializer, ApplicationSerializer, ApplicationStatusSerializer, FeedbackSerializer, InterviewOutcomeSerializer, InterviewResponseSerializer, InterviewSerializer, JobLocationReportSerializer, JobMediaSerializer, JobReportSerializer, JobSerializer, NotificationSerializer, RecruitmentSessionSerializer, SavedJobSerializer, SessionInviteSerializer, SessionResponseSerializer, SubmitApplicationSerializer
from .services import notify

class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    filterset_fields = ("category", "province", "district", "municipality", "city", "suburb", "postal_code", "employment_type", "workplace", "urgent")
    search_fields = ("title", "description", "requirements", "category", "province", "district", "municipality", "city", "suburb", "postal_code", "public_location")
    ordering_fields = ("created_at", "closing_date", "salary_min")
    def get_queryset(self):
        public = Job.objects.filter(status=Job.Status.PUBLISHED, closing_date__gte=timezone.localdate()).select_related("employer", "employer__employer_profile")
        if self.action == "mine" and self.request.user.is_authenticated:
            return Job.objects.filter(employer=self.request.user).select_related("employer", "employer__employer_profile")
        if self.action == "retrieve" and self.request.user.is_authenticated:
            return Job.objects.filter(Q(status=Job.Status.PUBLISHED, closing_date__gte=timezone.localdate()) | Q(employer=self.request.user)).select_related("employer", "employer__employer_profile").distinct()
        if self.action not in ("list", "retrieve", "create") and self.request.user.is_authenticated:
            return Job.objects.filter(employer=self.request.user).select_related("employer", "employer__employer_profile")
        return public
    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        if self.action == "mine":
            return [IsEmployer()]
        return [IsEmployer(), IsJobOwnerOrReadOnly()]
    def perform_create(self, serializer):
        has_location = serializer.validated_data.get("latitude") is not None or serializer.validated_data.get("public_location")
        serializer.save(
            employer=self.request.user,
            status=Job.Status.PENDING,
            location_confirmed_by_employer_at=timezone.now() if has_location else None,
        )
    def perform_update(self, serializer):
        location_fields = {"latitude", "longitude", "street_address", "public_location", "address_visibility"}
        location_changed = bool(location_fields.intersection(serializer.validated_data))
        serializer.save(
            status=Job.Status.PENDING,
            rejection_reason="",
            location_confirmed_by_employer_at=timezone.now() if location_changed else serializer.instance.location_confirmed_by_employer_at,
            location_review_status=Job.LocationReviewStatus.PENDING if location_changed else serializer.instance.location_review_status,
            location_verified_by_admin_at=None if location_changed else serializer.instance.location_verified_by_admin_at,
        )
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "DELETE",
            detail="Job listings cannot be permanently deleted. Close the listing instead to preserve applications and audit history.",
        )
    @staticmethod
    def _distance_km(origin_lat, origin_lon, job):
        lat1, lon1, lat2, lon2 = map(radians, (origin_lat, origin_lon, float(job.latitude), float(job.longitude)))
        delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
        value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        return 6371.0088 * 2 * asin(sqrt(value))
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        town = request.query_params.get("town", "").strip()
        if town:
            queryset = queryset.filter(city__iexact=town)
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")
        radius = request.query_params.get("radius_km", "25")
        jobs = list(queryset)
        if latitude is not None or longitude is not None:
            from rest_framework.exceptions import ValidationError
            if latitude is None or longitude is None:
                raise ValidationError({"location": "Latitude and longitude are both required for radius search."})
            try:
                origin_lat, origin_lon, radius_km = float(latitude), float(longitude), float(radius)
            except ValueError:
                raise ValidationError({"location": "Latitude, longitude and radius must be numbers."})
            if not -90 <= origin_lat <= 90 or not -180 <= origin_lon <= 180:
                raise ValidationError({"location": "The supplied coordinates are outside the valid range."})
            if not 0.1 <= radius_km <= 200:
                raise ValidationError({"radius_km": "Choose a radius from 0.1 to 200 km."})
            nearby = []
            for job in jobs:
                if job.latitude is None or job.longitude is None:
                    continue
                job.distance_km = self._distance_km(origin_lat, origin_lon, job)
                if job.distance_km <= radius_km:
                    nearby.append(job)
            jobs = nearby
            if request.query_params.get("ordering") == "distance":
                jobs.sort(key=lambda item: item.distance_km)
        page = self.paginate_queryset(jobs)
        serializer = self.get_serializer(page if page is not None else jobs, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)
    @action(detail=False, methods=["get"])
    def mine(self, request):
        return self.list(request)
    @action(detail=True, methods=["post"], permission_classes=[IsEmployer])
    def close(self, request, pk=None):
        job = self.get_object()
        job.status = Job.Status.CLOSED
        job.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(job).data)

class ApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = ApplicationSerializer
    def get_permissions(self):
        return [IsJobSeeker()] if self.request.method == "POST" else [permissions.IsAuthenticated()]
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.EMPLOYER:
            return Application.objects.filter(job__employer=user).select_related("job", "applicant")
        return Application.objects.filter(applicant=user).select_related("job", "applicant")
    def perform_create(self, serializer):
        job = serializer.validated_data["job"]
        from rest_framework.exceptions import ValidationError
        if job.status != Job.Status.PUBLISHED or job.is_expired:
            raise ValidationError({"job": "This job is not open for applications."})
        if Application.objects.filter(job=job, applicant=self.request.user).exists():
            raise ValidationError({"job": "You have already applied for this position."})
        serializer.save(applicant=self.request.user)

class ApplicationStatusView(generics.UpdateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationStatusSerializer
    permission_classes = [IsEmployer]
    def get_queryset(self):
        return super().get_queryset().filter(job__employer=self.request.user)
    def perform_update(self, serializer):
        application = serializer.instance
        previous = application.status
        message = serializer.validated_data.pop("message", "")
        serializer.save()
        if previous != application.status:
            ApplicationStatusHistory.objects.create(application=application, from_status=previous, to_status=application.status, message=message, changed_by=self.request.user)
            body = message or f"Your application for {application.job.title} is now {application.get_status_display()}."
            notify(application.applicant, f"Application update — {application.reference}", body, application)

class SavedJobListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedJobSerializer
    permission_classes = [IsJobSeeker]
    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user).select_related("job", "job__employer", "job__employer__employer_profile")
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SavedJobDeleteView(generics.DestroyAPIView):
    permission_classes = [IsJobSeeker]
    lookup_field = "job_id"
    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user)

class JobMediaCreateView(generics.CreateAPIView):
    serializer_class = JobMediaSerializer
    permission_classes = [IsEmployer]
    def perform_create(self, serializer):
        job = generics.get_object_or_404(Job, pk=self.kwargs["job_id"], employer=self.request.user)
        content_type = serializer.validated_data["file"].content_type
        from .serializers import ALLOWED_JOB_MEDIA
        serializer.save(job=job, media_type=ALLOWED_JOB_MEDIA[content_type][0])

class JobMediaDeleteView(generics.DestroyAPIView):
    serializer_class = JobMediaSerializer
    permission_classes = [IsEmployer]
    def get_queryset(self):
        return JobMedia.objects.filter(job__employer=self.request.user)

class ApplicationDocumentCreateView(generics.CreateAPIView):
    serializer_class = ApplicationDocumentSerializer
    permission_classes = [IsJobSeeker]
    def perform_create(self, serializer):
        application = generics.get_object_or_404(Application, pk=self.kwargs["application_id"], applicant=self.request.user)
        serializer.save(application=application)

class SubmitApplicationView(APIView):
    permission_classes = [IsJobSeeker]
    @transaction.atomic
    def post(self, request):
        serializer = SubmitApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.validated_data["job"]
        if job.status != Job.Status.PUBLISHED or job.is_expired:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"job": "This job is not open for applications."})
        application, created = Application.objects.get_or_create(
            job=job,
            applicant=request.user,
            defaults={"cover_note": serializer.validated_data.get("cover_note", ""), "sharing_consent_at": timezone.now()},
        )
        cv = serializer.validated_data.get("cv")
        if cv and not application.documents.exists():
            ApplicationDocument.objects.create(application=application, file=cv, label="CV")
        if created:
            ApplicationStatusHistory.objects.create(application=application, to_status=Application.Status.SUBMITTED, message="Application submitted.", changed_by=request.user)
            employer_profile = getattr(job.employer, "employer_profile", None)
            organisation_name = employer_profile.organisation_name if employer_profile else (job.employer.get_full_name() or job.employer.username)
            notify(request.user, f"Application submitted — {application.reference}", f"Your application for {job.title} at {organisation_name} was submitted successfully.", application)
            notify(job.employer, f"New application — {application.reference}", f"A new application was submitted for {job.title}. Review it in your Applicants dashboard.", application)
        output = ApplicationSerializer(application, context={"request": request}).data
        return Response({"success": True, "already_submitted": not created, "application": output}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = ApplicationSerializer
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.EMPLOYER:
            return Application.objects.filter(job__employer=user).select_related("job", "applicant").prefetch_related("documents", "status_history")
        return Application.objects.filter(applicant=user).select_related("job", "applicant").prefetch_related("documents", "status_history")

class ApplicationWithdrawView(APIView):
    permission_classes = [IsJobSeeker]
    def post(self, request, pk):
        application = generics.get_object_or_404(Application, pk=pk, applicant=request.user)
        if application.status in (Application.Status.HIRED, Application.Status.WITHDRAWN):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"status": "This application cannot be withdrawn."})
        previous = application.status
        application.status = Application.Status.WITHDRAWN
        application.withdrawn_at = timezone.now()
        application.save(update_fields=["status", "withdrawn_at", "updated_at"])
        ApplicationStatusHistory.objects.create(application=application, from_status=previous, to_status=Application.Status.WITHDRAWN, message="Application withdrawn by applicant.", changed_by=request.user)
        notify(application.job.employer, f"Application withdrawn — {application.reference}", f"The applicant withdrew from {application.job.title}.", application)
        return Response(ApplicationSerializer(application, context={"request": request}).data)

class ApplicationCVReplaceView(APIView):
    permission_classes = [IsJobSeeker]
    def put(self, request, pk):
        application = generics.get_object_or_404(Application, pk=pk, applicant=request.user)
        serializer = ApplicationDocumentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        application.documents.all().delete()
        document = serializer.save(application=application, label="CV")
        return Response(ApplicationDocumentSerializer(document, context={"request": request}).data)

class ApplicationDocumentDownloadView(APIView):
    def get(self, request, pk):
        document = generics.get_object_or_404(ApplicationDocument.objects.select_related("application__job"), pk=pk)
        application = document.application
        allowed = request.user.is_staff or application.applicant_id == request.user.id or application.job.employer_id == request.user.id
        if not allowed:
            raise Http404
        return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.file.name.rsplit("/", 1)[-1], content_type="application/pdf")

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationReadView(APIView):
    def post(self, request, pk):
        notification = generics.get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

class NotificationReadAllView(APIView):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response(status=204)

class JobReportCreateView(generics.CreateAPIView):
    serializer_class = JobReportSerializer
    permission_classes = [permissions.AllowAny]
    def perform_create(self, serializer):
        reporter = self.request.user if self.request.user.is_authenticated else None
        serializer.save(reporter=reporter)


class JobLocationReportCreateView(generics.CreateAPIView):
    serializer_class = JobLocationReportSerializer
    permission_classes = [permissions.AllowAny]
    def perform_create(self, serializer):
        reporter = self.request.user if self.request.user.is_authenticated else None
        serializer.save(reporter=reporter)


class LocationAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        jobs = Job.objects.all()
        return Response({
            "jobs_total": jobs.count(),
            "jobs_with_coordinates": jobs.filter(latitude__isnull=False, longitude__isnull=False).count(),
            "locations_reviewed": jobs.filter(location_review_status=Job.LocationReviewStatus.REVIEWED).count(),
            "locations_needing_changes": jobs.filter(location_review_status=Job.LocationReviewStatus.NEEDS_CHANGES).count(),
            "exact_locations_public": jobs.filter(address_visibility=Job.AddressVisibility.EXACT).count(),
            "street_view_enabled": jobs.filter(street_view_enabled=True, address_visibility=Job.AddressVisibility.EXACT).count(),
            "open_location_reports": JobLocationReport.objects.filter(resolved=False).count(),
            "by_province": list(jobs.values("province").annotate(count=Count("id")).order_by("province")),
            "by_district": list(jobs.exclude(district="").values("province", "district").annotate(count=Count("id")).order_by("province", "district")),
            "by_municipality": list(jobs.exclude(municipality="").values("province", "municipality").annotate(count=Count("id")).order_by("province", "municipality")),
        })

class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.AllowAny]
    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)


class InterviewViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_queryset(self):
        user = self.request.user
        queryset = Interview.objects.select_related(
            "application__job__employer__employer_profile", "application__applicant"
        ).prefetch_related("events")
        if user.is_staff:
            return queryset
        return queryset.filter(Q(application__applicant=user) | Q(application__job__employer=user)).distinct()

    def perform_create(self, serializer):
        if self.request.user.role != User.Role.EMPLOYER:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only employers can schedule interviews.")
        application = serializer.validated_data["application"]
        if application.job.employer_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You may only interview applicants for your own jobs.")
        if application.status in (Application.Status.UNSUCCESSFUL, Application.Status.WITHDRAWN, Application.Status.HIRED):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"application": "This application is not available for interviewing."})
        interview = serializer.save(created_by=self.request.user)
        InterviewEvent.objects.create(interview=interview, event_type=InterviewEvent.EventType.SCHEDULED, actor=self.request.user)
        previous = application.status
        application.status = Application.Status.INTERVIEW
        application.save(update_fields=("status", "updated_at"))
        ApplicationStatusHistory.objects.create(application=application, from_status=previous, to_status=Application.Status.INTERVIEW, message="Interview scheduled.", changed_by=self.request.user, actor_role=ApplicationStatusHistory.ActorRole.EMPLOYER)
        notify(application.applicant, f"Interview invitation — {application.reference}", f"An interview has been scheduled for {application.job.title}. Please respond in Interview Hub.", application)

    def partial_update(self, request, *args, **kwargs):
        interview = self.get_object()
        if interview.application.job.employer_id != request.user.id:
            return Response({"detail": "Only the employer may reschedule this interview."}, status=status.HTTP_403_FORBIDDEN)
        response = super().partial_update(request, *args, **kwargs)
        InterviewEvent.objects.create(interview=interview, event_type=InterviewEvent.EventType.RESCHEDULED, actor=request.user)
        return response

    @action(detail=True, methods=("post",))
    def respond(self, request, pk=None):
        interview = self.get_object()
        if interview.application.applicant_id != request.user.id:
            return Response({"detail": "Only the invited applicant may respond."}, status=status.HTTP_403_FORBIDDEN)
        serializer = InterviewResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_value = serializer.validated_data["response"]
        mapping = {
            "accepted": Interview.CandidateResponse.ACCEPTED,
            "declined": Interview.CandidateResponse.DECLINED,
            "reschedule": Interview.CandidateResponse.RESCHEDULE,
        }
        interview.candidate_response = mapping[response_value]
        interview.candidate_response_note = serializer.validated_data.get("note", "")
        if response_value == "reschedule":
            interview.status = Interview.Status.RESCHEDULE_REQUESTED
        interview.save(update_fields=("candidate_response", "candidate_response_note", "status", "updated_at"))
        event_type = {"accepted": InterviewEvent.EventType.ACCEPTED, "declined": InterviewEvent.EventType.DECLINED, "reschedule": InterviewEvent.EventType.RESCHEDULE_REQUESTED}[response_value]
        InterviewEvent.objects.create(interview=interview, event_type=event_type, actor=request.user, note=interview.candidate_response_note)
        notify(interview.application.job.employer, f"Interview response — {interview.application.reference}", f"The applicant responded: {interview.get_candidate_response_display()}.", interview.application)
        return Response(self.get_serializer(interview).data)

    @action(detail=True, methods=("post",))
    def outcome(self, request, pk=None):
        interview = self.get_object()
        if interview.application.job.employer_id != request.user.id and not request.user.is_staff:
            return Response({"detail": "Only the employer or an administrator may record the outcome."}, status=status.HTTP_403_FORBIDDEN)
        serializer = InterviewOutcomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interview.status = serializer.validated_data["status"]
        interview.save(update_fields=("status", "updated_at"))
        InterviewEvent.objects.create(interview=interview, event_type=interview.status, actor=request.user, note=serializer.validated_data.get("note", ""))
        return Response(self.get_serializer(interview).data)

    @action(detail=True, methods=("post",))
    def join(self, request, pk=None):
        interview = self.get_object()
        output = self.get_serializer(interview)
        if not output.get_can_join(interview):
            return Response({"detail": "The interview room is not available yet."}, status=status.HTTP_403_FORBIDDEN)
        InterviewEvent.objects.create(interview=interview, event_type=InterviewEvent.EventType.JOIN_REQUESTED, actor=request.user)
        return Response({"meeting_url": output.get_meeting_url(interview)})


class RecruitmentSessionViewSet(viewsets.ModelViewSet):
    serializer_class = RecruitmentSessionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_queryset(self):
        queryset = RecruitmentSession.objects.select_related("job__employer__employer_profile", "host").prefetch_related("participants__user")
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.role == User.Role.EMPLOYER):
            return queryset.filter(Q(visibility=RecruitmentSession.Visibility.PUBLIC) | Q(host=user) | Q(participants__user=user)).distinct()
        if user.is_authenticated:
            return queryset.filter(Q(visibility=RecruitmentSession.Visibility.PUBLIC) | Q(participants__user=user)).distinct()
        return queryset.filter(visibility=RecruitmentSession.Visibility.PUBLIC, status__in=(RecruitmentSession.Status.SCHEDULED, RecruitmentSession.Status.LIVE))

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated or self.request.user.role != User.Role.EMPLOYER:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only employers can create recruitment sessions.")
        job = serializer.validated_data["job"]
        if job.employer_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You may only create sessions for your own jobs.")
        serializer.save(host=self.request.user)

    @action(detail=True, methods=("post",))
    def invite(self, request, pk=None):
        session = self.get_object()
        if session.host_id != request.user.id:
            return Response({"detail": "Only the host may invite applicants."}, status=status.HTTP_403_FORBIDDEN)
        serializer = SessionInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]
        if application.job_id != session.job_id:
            return Response({"application": "The application must belong to this session's job."}, status=status.HTTP_400_BAD_REQUEST)
        participant, created = RecruitmentSessionParticipant.objects.get_or_create(session=session, user=application.applicant, defaults={"application": application})
        if created:
            notify(application.applicant, f"Recruitment session invitation — {application.reference}", f"You were invited to {session.title}.", application)
        return Response({"created": created, "participant": participant.pk}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=("post",))
    def respond(self, request, pk=None):
        session = self.get_object()
        participant = generics.get_object_or_404(RecruitmentSessionParticipant, session=session, user=request.user)
        serializer = SessionResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant.response = serializer.validated_data["response"]
        participant.responded_at = timezone.now()
        participant.save(update_fields=("response", "responded_at"))
        return Response(self.get_serializer(session).data)

    @action(detail=True, methods=("post",))
    def join(self, request, pk=None):
        session = self.get_object()
        output = self.get_serializer(session)
        if not output.get_can_join(session):
            return Response({"detail": "The session room is not available yet."}, status=status.HTTP_403_FORBIDDEN)
        if request.user.id != session.host_id:
            participant, _ = RecruitmentSessionParticipant.objects.get_or_create(session=session, user=request.user)
            participant.joined_at = timezone.now()
            participant.save(update_fields=("joined_at",))
        return Response({"meeting_url": output.get_meeting_url(session)})
