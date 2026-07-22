import logging
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.module_loading import import_string

from .models import PhoneOTPChallenge, User

logger = logging.getLogger(__name__)


def normalize_phone(value):
    raw = str(value or "").strip()
    if not re.fullmatch(r"[+\d\s().-]+", raw):
        raise ValidationError("Enter a valid South African mobile number, for example +27 73 086 2149.")
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("0") and len(digits) == 10:
        digits = "27" + digits[1:]
    elif digits.startswith("27") and len(digits) == 11:
        pass
    else:
        raise ValidationError("Enter a valid South African mobile number, for example +27 73 086 2149.")
    if not re.fullmatch(r"27[6-8]\d{8}", digits):
        raise ValidationError("Enter a valid South African mobile number beginning with +27 6, +27 7 or +27 8.")
    return f"+{digits}"


class ConsoleOTPProvider:
    """Development provider. Replace with a configured provider in production."""
    def send(self, *, phone, code, expires_minutes):
        if not settings.DEBUG:
            raise RuntimeError("The console OTP provider is disabled in production. Configure PHONE_OTP_PROVIDER.")
        logger.warning("DEVELOPMENT PHONE OTP for %s: %s (expires in %s minutes)", phone, code, expires_minutes)
        return {"reference": "console"}


def get_provider():
    provider_class = import_string(settings.PHONE_OTP_PROVIDER)
    return provider_class()


def send_challenge(user):
    phone = normalize_phone(user.phone)
    cooldown = timedelta(seconds=settings.PHONE_OTP_RESEND_SECONDS)
    latest = user.phone_otp_challenges.order_by("-created_at").first()
    if latest and latest.created_at > timezone.now() - cooldown:
        wait = max(1, int((latest.created_at + cooldown - timezone.now()).total_seconds()))
        raise ValidationError(f"Please wait {wait} seconds before requesting another code.")

    user.phone_otp_challenges.filter(consumed_at__isnull=True).update(consumed_at=timezone.now())
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = PhoneOTPChallenge.objects.create(
        user=user,
        phone=phone,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(minutes=settings.PHONE_OTP_EXPIRY_MINUTES),
        max_attempts=settings.PHONE_OTP_MAX_ATTEMPTS,
    )
    try:
        result = get_provider().send(phone=phone, code=code, expires_minutes=settings.PHONE_OTP_EXPIRY_MINUTES) or {}
    except Exception:
        challenge.delivery_status = "failed"
        challenge.save(update_fields=("delivery_status",))
        logger.exception("Phone OTP delivery failed for challenge %s", challenge.pk)
        raise ValidationError("We could not send the verification code. Please try again later.")
    challenge.delivery_status = "sent"
    challenge.provider_reference = str(result.get("reference", ""))[:200]
    challenge.save(update_fields=("delivery_status", "provider_reference"))
    return challenge


def verify_challenge(user, code):
    challenge = user.phone_otp_challenges.filter(consumed_at__isnull=True, delivery_status="sent").order_by("-created_at").first()
    if not challenge or challenge.expires_at <= timezone.now():
        raise ValidationError("The code has expired. Request a new code.")
    if challenge.attempts >= challenge.max_attempts:
        raise ValidationError("Too many incorrect attempts. Request a new code.")
    challenge.attempts += 1
    challenge.save(update_fields=("attempts",))
    if not check_password(str(code), challenge.code_hash):
        remaining = challenge.max_attempts - challenge.attempts
        raise ValidationError(f"Incorrect code. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
    if User.objects.exclude(pk=user.pk).filter(phone=challenge.phone, phone_verified_at__isnull=False).exists():
        raise ValidationError("This mobile number is already verified on another account. Contact support if you own both accounts.")
    now = timezone.now()
    challenge.consumed_at = now
    challenge.save(update_fields=("consumed_at",))
    user.phone = challenge.phone
    user.phone_verified_at = now
    user.save(update_fields=("phone", "phone_verified_at"))
    return user
