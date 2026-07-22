from django.urls import reverse
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from .models import JobSeekerProfile, User

class RegistrationTests(APITestCase):
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
