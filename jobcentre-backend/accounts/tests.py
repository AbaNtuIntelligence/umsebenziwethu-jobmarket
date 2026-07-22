from django.urls import reverse
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from .models import JobSeekerProfile, User

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
