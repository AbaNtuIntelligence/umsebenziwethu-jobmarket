import re

from django.core.exceptions import ValidationError


def normalize_phone(value):
    """Normalise optional South African contact numbers; this is not verification."""
    raw = str(value or "").strip()
    if not re.fullmatch(r"[+\d\s().-]+", raw):
        raise ValidationError("Enter a valid South African mobile number, for example +27 73 086 2149.")
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("0") and len(digits) == 10:
        digits = "27" + digits[1:]
    elif not (digits.startswith("27") and len(digits) == 11):
        raise ValidationError("Enter a valid South African mobile number, for example +27 73 086 2149.")
    if not re.fullmatch(r"27[6-8]\d{8}", digits):
        raise ValidationError("Enter a valid South African mobile number beginning with +27 6, +27 7 or +27 8.")
    return f"+{digits}"
