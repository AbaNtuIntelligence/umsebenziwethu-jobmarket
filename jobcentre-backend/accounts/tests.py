from django.urls import reverse
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from .models import JobSeekerProfile, User
from django.utils import timezone
from datetime import timedelta
from jobs.models import Job, JobInvitation, Notification
from django.core.cache import cache
from django.test import override_settings
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

class RegistrationTests(APITestCase):
    @staticmethod
    def avatar_upload(name="avatar.png"):
        image = BytesIO()
        Image.new("RGB", (20, 20), "navy").save(image, format="PNG")
        return SimpleUploadedFile(name, image.getvalue(), content_type="image/png")

    def test_job_seeker_registration(self):
        response = self.client.post(reverse("register"), {"email": "seeker@example.com", "username": "seeker", "role": "job_seeker", "password": "StrongPass778!", "accept_terms": True})
        self.assertEqual(response.status_code, 201)

    def test_job_seeker_can_register_with_skills_and_resume(self):
        resume = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 profile resume", content_type="application/pdf")
        response = self.client.post(reverse("register"), {
            "email": "skilled@example.com",
            "username": "skilled",
            "role": "job_seeker",
            "password": "StrongPass778!",
            "accept_terms": True,
            "professional_headline": "Junior IT Support Technician",
            "skills": "Technical support, networking, customer service",
            "province": "Gauteng",
            "city": "Johannesburg",
            "availability": "Immediately available",
            "resume": resume,
        }, format="multipart")
        self.assertEqual(response.status_code, 201)
        profile = JobSeekerProfile.objects.get(user__email="skilled@example.com")
        self.assertEqual(profile.professional_headline, "Junior IT Support Technician")
        self.assertIn("networking", profile.skills)
        self.assertTrue(bool(profile.resume))

    def test_resume_must_be_pdf(self):
        resume = SimpleUploadedFile("resume.txt", b"not a pdf", content_type="text/plain")
        response = self.client.post(reverse("register"), {
            "email": "bad-resume@example.com",
            "username": "bad-resume",
            "role": "job_seeker",
            "password": "StrongPass778!",
            "accept_terms": True,
            "resume": resume,
        }, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("resume", response.data["errors"])

    def test_employer_requires_organisation(self):
        response = self.client.post(reverse("register"), {"email": "boss@example.com", "username": "boss", "role": "employer", "password": "StrongPass778!", "accept_terms": True})
        self.assertEqual(response.status_code, 400)

    def test_both_roles_can_upload_an_avatar_during_registration(self):
        seeker = self.client.post(reverse("register"), {
            "email": "photo-seeker@example.com",
            "username": "photo-seeker",
            "role": "job_seeker",
            "password": "StrongPass778!",
            "accept_terms": True,
            "avatar": self.avatar_upload("seeker.png"),
            "directory_visible": True,
            "directory_show_avatar": True,
        }, format="multipart")
        employer = self.client.post(reverse("register"), {
            "email": "photo-employer@example.com",
            "username": "photo-employer",
            "role": "employer",
            "password": "StrongPass778!",
            "organisation_name": "Photo Employer",
            "accept_terms": True,
            "avatar": self.avatar_upload("employer.png"),
        }, format="multipart")
        self.assertEqual(seeker.status_code, 201)
        self.assertEqual(employer.status_code, 201)
        self.assertTrue(bool(User.objects.get(email="photo-seeker@example.com").avatar))
        self.assertTrue(bool(User.objects.get(email="photo-employer@example.com").avatar))
        profile = JobSeekerProfile.objects.get(user__email="photo-seeker@example.com")
        self.assertTrue(profile.directory_show_avatar)

    def test_registration_rejects_non_image_avatar(self):
        response = self.client.post(reverse("register"), {
            "email": "bad-avatar@example.com",
            "username": "bad-avatar",
            "role": "job_seeker",
            "password": "StrongPass778!",
            "accept_terms": True,
            "avatar": SimpleUploadedFile("avatar.txt", b"not an image", content_type="text/plain"),
        }, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("avatar", response.data["errors"])

    def test_registration_requires_terms(self):
        response = self.client.post(reverse("register"), {"email": "private@example.com", "username": "private", "role": "job_seeker", "password": "StrongPass778!", "accept_terms": False})
        self.assertEqual(response.status_code, 400)

    def test_account_delete_requires_password_and_confirmation(self):
        from .models import User
        user = User.objects.create_user(email="delete@example.com", username="delete", role="job_seeker", password="StrongPass778!")
        self.client.force_authenticate(user)
        denied = self.client.post(reverse("delete-account"), {"password": "wrong", "confirm": "DELETE"})
        self.assertEqual(denied.status_code, 400)
        accepted = self.client.post(reverse("delete-account"), {"password": "StrongPass778!", "confirm": "DELETE"})
        self.assertEqual(accepted.status_code, 204)

    def test_user_can_upload_optional_avatar(self):
        from .models import User
        user = User.objects.create_user(email="avatar@example.com", username="avatar", role="job_seeker", password="StrongPass778!")
        image = BytesIO()
        Image.new("RGB", (20, 20), "navy").save(image, format="PNG")
        upload = SimpleUploadedFile("avatar.png", image.getvalue(), content_type="image/png")
        self.client.force_authenticate(user)
        response = self.client.patch(reverse("me"), {"avatar": upload}, format="multipart")
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(bool(user.avatar))


class TalentDirectoryTests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            email="employer@example.com",
            username="employer",
            role=User.Role.EMPLOYER,
            password="StrongPass778!",
        )
        self.visible_user = User.objects.create_user(
            email="visible@example.com",
            username="visible",
            first_name="Naledi",
            last_name="Mokoena",
            phone="0820000000",
            role=User.Role.JOB_SEEKER,
            password="StrongPass778!",
        )
        self.visible = JobSeekerProfile.objects.create(
            user=self.visible_user,
            professional_headline="Junior Data Analyst",
            sector="Technology",
            industry="Data services",
            skills="Excel, SQL, data collection",
            province="Gauteng",
            city="Johannesburg",
            availability="Immediately available",
            directory_visible=True,
            resume=SimpleUploadedFile(
                "private-resume.pdf",
                b"%PDF-1.4 private",
                content_type="application/pdf",
            ),
        )
        hidden_user = User.objects.create_user(
            email="hidden@example.com",
            username="hidden",
            role=User.Role.JOB_SEEKER,
            password="StrongPass778!",
        )
        JobSeekerProfile.objects.create(
            user=hidden_user,
            professional_headline="Private candidate",
            directory_visible=False,
        )
        self.hidden_profile = hidden_user.job_seeker_profile

    def test_employer_can_browse_only_opted_in_profiles(self):
        self.client.force_authenticate(self.employer)
        response = self.client.get(reverse("job-seeker-directory"))
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Naledi Mokoena")
        self.assertNotIn("email", results[0])
        self.assertNotIn("phone", results[0])
        self.assertNotIn("resume", results[0])

    def test_job_seeker_cannot_browse_directory(self):
        self.client.force_authenticate(self.visible_user)
        response = self.client.get(reverse("job-seeker-directory"))
        self.assertEqual(response.status_code, 403)

    def test_directory_can_filter_by_sector_and_search_skills(self):
        self.client.force_authenticate(self.employer)
        matching = self.client.get(reverse("job-seeker-directory"), {"sector": "Technology", "search": "SQL"})
        missing = self.client.get(reverse("job-seeker-directory"), {"sector": "Hospitality"})
        self.assertEqual(len(matching.data.get("results", matching.data)), 1)
        self.assertEqual(len(missing.data.get("results", missing.data)), 0)

    def test_job_seeker_can_hide_avatar_without_hiding_directory_profile(self):
        self.visible_user.avatar = RegistrationTests.avatar_upload("visible.png")
        self.visible_user.save(update_fields=["avatar"])
        self.visible.directory_show_avatar = False
        self.visible.save(update_fields=["directory_show_avatar"])
        self.client.force_authenticate(self.employer)
        response = self.client.get(reverse("job-seeker-directory"))
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]["avatar"])

    def test_employer_can_open_visible_profile_but_not_hidden_profile(self):
        self.client.force_authenticate(self.employer)
        visible = self.client.get(reverse("job-seeker-profile", kwargs={"pk": self.visible.pk}))
        hidden = self.client.get(reverse("job-seeker-profile", kwargs={"pk": self.hidden_profile.pk}))
        self.assertEqual(visible.status_code, 200)
        self.assertEqual(visible.data["name"], "Naledi Mokoena")
        self.assertEqual(hidden.status_code, 404)

    def test_employer_can_invite_visible_candidate_to_own_published_job(self):
        job = Job.objects.create(
            employer=self.employer,
            title="Junior Data Assistant",
            category="Technology",
            description="Support the data team.",
            employment_type=Job.EmploymentType.CONTRACT,
            province="Gauteng",
            city="Johannesburg",
            closing_date=timezone.localdate() + timedelta(days=14),
            status=Job.Status.PUBLISHED,
        )
        self.client.force_authenticate(self.employer)
        response = self.client.post(reverse("job-invitation-create"), {
            "candidate_profile": self.visible.pk,
            "job": job.pk,
            "message": "Your SQL skills look relevant to this opportunity.",
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(JobInvitation.objects.filter(job=job, candidate=self.visible_user).exists())
        notification = Notification.objects.get(user=self.visible_user, job=job)
        self.assertIn("invited you to apply", notification.message)

        duplicate = self.client.post(reverse("job-invitation-create"), {
            "candidate_profile": self.visible.pk,
            "job": job.pk,
        })
        self.assertEqual(duplicate.status_code, 400)


class HardeningTests(APITestCase):
    def test_readiness_checks_database_connection(self):
        response = self.client.get("/api/ready/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["database"], "ok")

    def test_invalid_token_returns_readable_error_shape(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer definitely-not-a-jwt")
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data["success"])
        self.assertIsInstance(response.data["detail"], str)
        self.assertNotEqual(response.data["detail"], "[object Object]")

    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(
            email="logout@example.com",
            username="logout",
            role=User.Role.JOB_SEEKER,
            password="StrongPass778!",
        )
        refresh = str(RefreshToken.for_user(user))
        logout = self.client.post(reverse("logout"), {"refresh": refresh})
        rejected = self.client.post(reverse("token-refresh"), {"refresh": refresh})
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(rejected.status_code, 401)

    @override_settings(REST_FRAMEWORK={
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {
            **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
            "anon": "100/min",
            "login": "2/min",
        },
    })
    def test_login_is_rate_limited(self):
        cache.clear()
        payload = {"email": "nobody@example.com", "password": "WrongPass778!"}
        self.client.post(reverse("login"), payload)
        self.client.post(reverse("login"), payload)
        limited = self.client.post(reverse("login"), payload)
        self.assertEqual(limited.status_code, 429)
