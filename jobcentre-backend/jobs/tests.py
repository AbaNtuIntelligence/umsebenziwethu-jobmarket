from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import EmployerProfile, User
from .models import (
    Application,
    ApplicationStatusHistory,
    Interview,
    InterviewEvent,
    Job,
    JobReport,
    JobLocationReport,
    Notification,
    Placement,
    PlacementConfirmation,
    PlacementFollowUp,
    RecruitmentSession,
    RecruitmentSessionParticipant,
)

class JobApiTests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(email="employer@example.com", username="employer", role="employer", password="StrongPass778!")
        EmployerProfile.objects.create(user=self.employer, organisation_name="Test Company")
        self.job = Job.objects.create(employer=self.employer, title="Driver", category="Transport", description="Delivery driver", employment_type="contract", province="Gauteng", city="Johannesburg", closing_date=timezone.localdate() + timedelta(days=7), status="published")
    def test_public_can_browse_jobs(self):
        response = self.client.get("/api/jobs/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
    def test_employer_can_submit_job(self):
        self.client.force_authenticate(self.employer)
        payload = {"title":"Warehouse Assistant", "category":"Warehousing", "description":"Pick and pack", "employment_type":"temporary", "province":"Gauteng", "city":"Soweto", "closing_date": str(timezone.localdate() + timedelta(days=3))}
        response = self.client.post("/api/jobs/", payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "pending")

    def test_anonymous_user_can_report_a_job(self):
        response = self.client.post("/api/job-reports/", {"job": self.job.id, "reason": "scam", "details": "Suspicious contact request"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(JobReport.objects.count(), 1)

    def test_employer_can_update_own_application_status(self):
        seeker = User.objects.create_user(email="seeker@example.com", username="seeker", role="job_seeker", password="StrongPass778!")
        application = Application.objects.create(job=self.job, applicant=seeker)
        self.client.force_authenticate(self.employer)
        response = self.client.patch(f"/api/applications/{application.id}/status/", {"status": "shortlisted"})
        self.assertEqual(response.status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.status, "shortlisted")

    def test_submit_is_idempotent_and_creates_communication_records(self):
        seeker = User.objects.create_user(email="apply@example.com", username="apply", role="job_seeker", password="StrongPass778!")
        self.client.force_authenticate(seeker)
        cv = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        first = self.client.post("/api/applications/submit/", {"job": self.job.id, "cover_note": "I am interested.", "consent_to_share": True, "cv": cv}, format="multipart")
        second = self.client.post("/api/applications/submit/", {"job": self.job.id, "cover_note": "Retry", "consent_to_share": True}, format="multipart")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data["already_submitted"])
        self.assertEqual(Application.objects.filter(job=self.job, applicant=seeker).count(), 1)
        self.assertEqual(ApplicationStatusHistory.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 2)

    def test_cv_download_is_protected(self):
        seeker = User.objects.create_user(email="document@example.com", username="document", role="job_seeker", password="StrongPass778!")
        self.client.force_authenticate(seeker)
        cv = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        submitted = self.client.post("/api/applications/submit/", {"job": self.job.id, "consent_to_share": True, "cv": cv}, format="multipart")
        url = submitted.data["application"]["documents"][0]["download_url"]
        self.client.force_authenticate(user=None)
        denied = self.client.get(url)
        self.assertEqual(denied.status_code, 401)
        self.client.force_authenticate(seeker)
        allowed = self.client.get(url)
        self.assertEqual(allowed.status_code, 200)

    def test_submission_survives_employer_without_profile(self):
        employer = User.objects.create_user(email="legacy@example.com", username="legacy", role="employer", password="StrongPass778!")
        job = Job.objects.create(employer=employer, title="Support Technician", category="IT", description="Provide support", employment_type="contract", province="Gauteng", city="Johannesburg", closing_date=timezone.localdate() + timedelta(days=7), status="published")
        seeker = User.objects.create_user(email="legacy-seeker@example.com", username="legacy-seeker", role="job_seeker", password="StrongPass778!")
        self.client.force_authenticate(seeker)
        response = self.client.post("/api/applications/submit/", {"job": job.id, "consent_to_share": True}, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Application.objects.filter(job=job, applicant=seeker).count(), 1)

    def test_exact_public_location_generates_safe_google_links(self):
        self.job.latitude = "-26.238000"
        self.job.longitude = "27.908000"
        self.job.street_address = "Vilakazi Street"
        self.job.public_location = "Orlando West, Soweto"
        self.job.address_visibility = Job.AddressVisibility.EXACT
        self.job.street_view_enabled = True
        self.job.save()

        response = self.client.get(f"/api/jobs/{self.job.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("google.com/maps/search", response.data["map_url"])
        self.assertIn("google.com/maps/dir", response.data["directions_url"])
        self.assertIn("map_action=pano", response.data["street_view_url"])
        self.assertEqual(response.data["exact_address"], "Vilakazi Street")
        self.assertNotIn("latitude", response.data)
        self.assertNotIn("longitude", response.data)

    def test_area_only_location_never_exposes_street_view_or_exact_address(self):
        self.job.latitude = "-26.238000"
        self.job.longitude = "27.908000"
        self.job.street_address = "Private workplace address"
        self.job.public_location = "Orlando West, Soweto"
        self.job.address_visibility = Job.AddressVisibility.AREA_ONLY
        self.job.street_view_enabled = True
        self.job.save()

        response = self.client.get(f"/api/jobs/{self.job.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["directions_url"])
        self.assertIsNone(response.data["street_view_url"])
        self.assertIsNone(response.data["exact_address"])
        self.assertNotIn("Private workplace address", str(response.data))

    def test_radius_search_returns_nearby_job_with_distance(self):
        self.job.latitude = "-26.204100"
        self.job.longitude = "28.047300"
        self.job.save()

        response = self.client.get("/api/jobs/?latitude=-26.2041&longitude=28.0473&radius_km=5&ordering=distance")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["distance_km"], 0.0)

    def test_anonymous_user_can_report_incorrect_location(self):
        response = self.client.post("/api/job-location-reports/", {
            "job": self.job.id,
            "reason": JobLocationReport.Reason.WRONG_AREA,
            "details": "The map pin is in another town.",
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(JobLocationReport.objects.count(), 1)

    def test_location_analytics_requires_admin(self):
        denied = self.client.get("/api/analytics/locations/")
        self.assertEqual(denied.status_code, 401)
        self.employer.is_staff = True
        self.employer.save(update_fields=["is_staff"])
        self.client.force_authenticate(self.employer)
        allowed = self.client.get("/api/analytics/locations/")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.data["jobs_total"], 1)


class EmploymentOutcomeModelTests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            email="outcomes-employer@example.com",
            username="outcomes-employer",
            role=User.Role.EMPLOYER,
            password="StrongPass778!",
        )
        self.seeker = User.objects.create_user(
            email="outcomes-seeker@example.com",
            username="outcomes-seeker",
            role=User.Role.JOB_SEEKER,
            password="StrongPass778!",
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title="Data Capturer",
            category="Administration",
            description="Capture verified records.",
            employment_type=Job.EmploymentType.CONTRACT,
            province="Gauteng",
            city="Johannesburg",
            closing_date=timezone.localdate() + timedelta(days=7),
            status=Job.Status.PUBLISHED,
        )
        self.application = Application.objects.create(job=self.job, applicant=self.seeker)
        self.placement = Placement.objects.create(
            application=self.application,
            expected_start_date=timezone.localdate() + timedelta(days=14),
            employment_type=Job.EmploymentType.CONTRACT,
        )

    def test_placement_does_not_change_existing_application(self):
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.SUBMITTED)
        self.assertEqual(self.application.placement, self.placement)

    def test_each_party_can_have_only_one_confirmation(self):
        PlacementConfirmation.objects.create(
            placement=self.placement,
            respondent=self.employer,
            respondent_role=PlacementConfirmation.RespondentRole.EMPLOYER,
            response=PlacementConfirmation.Response.STARTED,
        )
        with self.assertRaises(Exception):
            PlacementConfirmation.objects.create(
                placement=self.placement,
                respondent=self.employer,
                respondent_role=PlacementConfirmation.RespondentRole.EMPLOYER,
                response=PlacementConfirmation.Response.STARTED,
            )

    def test_confirmed_start_requires_status_and_date(self):
        self.assertFalse(self.placement.is_confirmed_start)
        self.placement.actual_start_date = timezone.localdate()
        self.placement.verification_status = Placement.VerificationStatus.CONFIRMED
        self.assertTrue(self.placement.is_confirmed_start)

    def test_follow_up_type_is_unique_per_placement(self):
        due_date = timezone.localdate() + timedelta(days=30)
        PlacementFollowUp.objects.create(
            placement=self.placement,
            follow_up_type=PlacementFollowUp.FollowUpType.DAY_30,
            due_date=due_date,
        )
        with self.assertRaises(Exception):
            PlacementFollowUp.objects.create(
                placement=self.placement,
                follow_up_type=PlacementFollowUp.FollowUpType.DAY_30,
                due_date=due_date,
            )


class InterviewWorkflowTests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(email="interview-employer@example.com", username="interview-employer", role=User.Role.EMPLOYER, password="StrongPass778!")
        EmployerProfile.objects.create(user=self.employer, organisation_name="Interview Company")
        self.seeker = User.objects.create_user(email="interview-seeker@example.com", username="interview-seeker", role=User.Role.JOB_SEEKER, password="StrongPass778!")
        self.outsider = User.objects.create_user(email="outsider@example.com", username="outsider", role=User.Role.JOB_SEEKER, password="StrongPass778!")
        self.job = Job.objects.create(employer=self.employer, title="Support Agent", category="Customer Service", description="Support customers", employment_type=Job.EmploymentType.CONTRACT, province="Gauteng", city="Soweto", closing_date=timezone.localdate() + timedelta(days=7), status=Job.Status.PUBLISHED)
        self.application = Application.objects.create(job=self.job, applicant=self.seeker, status=Application.Status.SHORTLISTED)
        self.start = timezone.now() + timedelta(days=1)

    def interview_payload(self):
        return {"application": self.application.id, "provider": "zoom", "title": "Support interview", "scheduled_start": self.start.isoformat(), "scheduled_end": (self.start + timedelta(minutes=30)).isoformat(), "join_url": "https://zoom.us/j/123456"}

    def test_employer_schedules_and_candidate_accepts(self):
        self.client.force_authenticate(self.employer)
        created = self.client.post("/api/interviews/", self.interview_payload(), format="json")
        self.assertEqual(created.status_code, 201)
        interview = Interview.objects.get()
        self.assertEqual(interview.application.status, Application.Status.INTERVIEW)
        self.assertEqual(InterviewEvent.objects.filter(interview=interview).count(), 1)
        self.client.force_authenticate(self.seeker)
        accepted = self.client.post(f"/api/interviews/{interview.id}/respond/", {"response": "accepted"}, format="json")
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.data["candidate_response"], "accepted")

    def test_outsider_cannot_see_private_interview(self):
        self.client.force_authenticate(self.employer)
        interview_id = self.client.post("/api/interviews/", self.interview_payload(), format="json").data["id"]
        self.client.force_authenticate(self.outsider)
        response = self.client.get(f"/api/interviews/{interview_id}/")
        self.assertEqual(response.status_code, 404)

    def test_host_creates_session_and_invites_job_applicant(self):
        self.client.force_authenticate(self.employer)
        payload = {"job": self.job.id, "title": "Applicant briefing", "description": "Questions and answers", "session_type": "group_briefing", "visibility": "invited", "provider": "google_meet", "scheduled_start": self.start.isoformat(), "scheduled_end": (self.start + timedelta(hours=1)).isoformat(), "join_url": "https://meet.google.com/abc-defg-hij", "capacity": 20}
        created = self.client.post("/api/recruitment-sessions/", payload, format="json")
        self.assertEqual(created.status_code, 201)
        invited = self.client.post(f"/api/recruitment-sessions/{created.data['id']}/invite/", {"application": self.application.id}, format="json")
        self.assertEqual(invited.status_code, 201)
        self.assertTrue(RecruitmentSessionParticipant.objects.filter(session_id=created.data["id"], user=self.seeker).exists())

    def test_recording_is_disabled_for_pilot(self):
        payload = self.interview_payload()
        payload["recording_allowed"] = True
        self.client.force_authenticate(self.employer)
        response = self.client.post("/api/interviews/", payload, format="json")
        self.assertEqual(response.status_code, 400)
