from functools import lru_cache

import jwt
from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework.exceptions import ValidationError


def verify_google(token):
    try:
        claims = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except Exception as error:
        raise ValidationError({"id_token": "Google could not verify this sign-in."}) from error
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ValidationError({"id_token": "Google returned an invalid token issuer."})
    return claims


@lru_cache(maxsize=1)
def microsoft_jwk_client():
    return jwt.PyJWKClient(
        f"https://login.microsoftonline.com/{settings.MICROSOFT_OAUTH_TENANT}/discovery/v2.0/keys",
        cache_keys=True,
        lifespan=3600,
    )


def verify_microsoft(token):
    try:
        signing_key = microsoft_jwk_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.MICROSOFT_OAUTH_CLIENT_ID,
            options={"require": ["exp", "iat", "iss", "sub"]},
        )
    except Exception as error:
        raise ValidationError({"id_token": "Microsoft could not verify this sign-in."}) from error
    issuer = claims.get("iss", "")
    if not issuer.startswith("https://login.microsoftonline.com/") or not issuer.endswith("/v2.0"):
        raise ValidationError({"id_token": "Microsoft returned an invalid token issuer."})
    return claims


def verify_social_token(provider, token):
    if provider == "google":
        claims = verify_google(token)
    elif provider == "microsoft":
        claims = verify_microsoft(token)
    else:
        raise ValidationError({"provider": "Unsupported sign-in provider."})

    email = (claims.get("email") or claims.get("preferred_username") or "").strip().lower()
    email_verified = claims.get("email_verified")
    if not email:
        raise ValidationError({"id_token": "The provider did not return an email address."})
    if provider == "google" and email_verified is not True:
        raise ValidationError({"id_token": "Google has not verified this email address."})
    return {
        "subject": str(claims["sub"]),
        "email": email,
        "email_verified": True if provider == "microsoft" else bool(email_verified),
        "first_name": (claims.get("given_name") or "").strip(),
        "last_name": (claims.get("family_name") or "").strip(),
        "display_name": (claims.get("name") or "").strip(),
    }
