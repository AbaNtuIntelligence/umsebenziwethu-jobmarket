from django.urls import reverse
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

class RegistrationTests(APITestCase):
    def test_job_seeker_registration(self):
        response = self.client.post(reverse("register"), {"email": "seeker@example.com", "username": "seeker", "role": "job_seeker", "password": "StrongPass778!", "accept_terms": True})
        self.assertEqual(response.status_code, 201)

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
