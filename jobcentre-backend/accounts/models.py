from django.contrib.auth.models import AbstractUser
from django.db import models


def job_seeker_resume_path(instance, filename):
    return f"resumes/{instance.user_id}/{filename}"

class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYER = "employer", "Employer"
        JOB_SEEKER = "job_seeker", "Job seeker"
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    phone = models.CharField(max_length=20, blank=True)
    email_verified = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", null=True, blank=True)
    last_auth_provider = models.CharField(max_length=20, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "role"]

class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employer_profile")
    organisation_name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="job_seeker_profile")
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    professional_headline = models.CharField(max_length=160, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    bio = models.TextField(blank=True)
    availability = models.CharField(max_length=100, blank=True)
    resume = models.FileField(upload_to=job_seeker_resume_path, null=True, blank=True)
    directory_visible = models.BooleanField(
        default=False,
        help_text="Allow employers to discover this professional profile.",
    )
    directory_show_avatar = models.BooleanField(
        default=False,
        help_text="Show the account avatar in the employer talent directory.",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class SocialIdentity(models.Model):
    class Provider(models.TextChoices):
        GOOGLE = "google", "Google"
        MICROSOFT = "microsoft", "Microsoft"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_identities")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    subject = models.CharField(max_length=255)
    email_at_link = models.EmailField()
    linked_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "subject"),
                name="accounts_unique_social_identity",
            ),
        ]
        indexes = [models.Index(fields=("user", "provider"), name="acct_social_user_prov")]


class AuthenticationEvent(models.Model):
    class Event(models.TextChoices):
        SIGN_UP = "social_signup", "Social sign-up"
        SIGN_IN = "social_signin", "Social sign-in"
        LINK = "social_link", "Social account linked"
        LINK_FAILED = "social_link_failed", "Social account link failed"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="authentication_events")
    event = models.CharField(max_length=40, choices=Event.choices)
    provider = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("-created_at", "event"), name="accounts_auth_event_idx")]
