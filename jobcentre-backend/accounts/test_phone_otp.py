from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import User
from .phone_otp import normalize_phone


class CapturingOTPProvider:
    code = None
    def send(self, *, phone, code, expires_minutes):
        self.__class__.code = code
        return {"reference": "test-message"}


class PhoneNormalizationTests(APITestCase):
    def test_accepts_local_and_international_sa_mobile_formats(self):
        expected = "+27730862149"
        self.assertEqual(normalize_phone("0730862149"), expected)
        self.assertEqual(normalize_phone("+27 73 086 2149"), expected)
        self.assertEqual(normalize_phone("27730862149"), expected)


@override_settings(
    PHONE_OTP_PROVIDER="accounts.test_phone_otp.CapturingOTPProvider",
    PHONE_OTP_RESEND_SECONDS=0,
)
class PhoneOTPTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="otp@example.com", username="otp-user", role=User.Role.EMPLOYER,
            phone="+27821234567", password="StrongPass778!",
        )
        self.client.force_authenticate(self.user)

    def test_send_and_verify_phone_code(self):
        sent = self.client.post(reverse("phone-otp-send"))
        self.assertEqual(sent.status_code, 200)
        self.assertNotIn("code", sent.data)
        verified = self.client.post(reverse("phone-otp-verify"), {"code": CapturingOTPProvider.code})
        self.assertEqual(verified.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.phone_verified_at)

    def test_code_is_single_use(self):
        self.client.post(reverse("phone-otp-send"))
        code = CapturingOTPProvider.code
        self.client.post(reverse("phone-otp-verify"), {"code": code})
        second = self.client.post(reverse("phone-otp-verify"), {"code": code})
        self.assertEqual(second.status_code, 400)

    def test_plaintext_code_is_not_stored(self):
        self.client.post(reverse("phone-otp-send"))
        challenge = self.user.phone_otp_challenges.latest("created_at")
        self.assertNotEqual(challenge.code_hash, CapturingOTPProvider.code)
