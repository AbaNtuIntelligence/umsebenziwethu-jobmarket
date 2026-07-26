from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from .models import AuthenticationEvent, SocialIdentity, User


def claims(email="new@example.com", subject="provider-user-1"):
    return {
        "subject": subject,
        "email": email,
        "email_verified": True,
        "first_name": "New",
        "last_name": "Member",
        "display_name": "New Member",
    }


class SocialAuthenticationTests(APITestCase):
    @patch("accounts.views.verify_social_token")
    def test_new_job_seeker_can_sign_up_with_google(self, verify):
        verify.return_value = claims()
        response = self.client.post(reverse("social-auth"), {
            "provider": "google", "id_token": "valid", "role": "job_seeker", "accept_terms": True,
        })
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.email_verified)
        self.assertTrue(SocialIdentity.objects.filter(user=user, provider="google").exists())
        self.assertIn("access", response.data)

    @patch("accounts.views.verify_social_token")
    def test_unknown_account_requires_registration_details(self, verify):
        verify.return_value = claims()
        response = self.client.post(reverse("social-auth"), {"provider": "google", "id_token": "valid"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "registration_required")

    @patch("accounts.views.verify_social_token")
    def test_existing_password_account_requires_safe_link(self, verify):
        verify.return_value = claims(email="existing@example.com")
        User.objects.create_user(email="existing@example.com", username="existing", role="job_seeker", password="StrongPass778!")
        response = self.client.post(reverse("social-auth"), {"provider": "google", "id_token": "valid"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "link_required")
        self.assertFalse(SocialIdentity.objects.exists())

    @patch("accounts.views.verify_social_token")
    def test_existing_account_links_after_password_confirmation(self, verify):
        verify.return_value = claims(email="existing@example.com")
        user = User.objects.create_user(email="existing@example.com", username="existing", role="job_seeker", password="StrongPass778!")
        response = self.client.post(reverse("social-auth"), {
            "provider": "google", "id_token": "valid", "link_password": "StrongPass778!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["linked"])
        self.assertTrue(SocialIdentity.objects.filter(user=user).exists())
        self.assertTrue(AuthenticationEvent.objects.filter(user=user, event="social_link").exists())

    @patch("accounts.views.verify_social_token")
    def test_link_rejects_wrong_password(self, verify):
        verify.return_value = claims(email="existing@example.com")
        user = User.objects.create_user(email="existing@example.com", username="existing", role="job_seeker", password="StrongPass778!")
        response = self.client.post(reverse("social-auth"), {
            "provider": "google", "id_token": "valid", "link_password": "wrong-password",
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(SocialIdentity.objects.filter(user=user).exists())
