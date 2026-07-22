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
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", null=True, blank=True)
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


class PhoneOTPChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phone_otp_challenges")
    phone = models.CharField(max_length=20)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    consumed_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=20, default="pending")
    provider_reference = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("user", "-created_at"), name="accounts_ph_user_id_9c49cc_idx")]

    @property
    def is_active(self):
        from django.utils import timezone
        return not self.consumed_at and self.attempts < self.max_attempts and self.expires_at > timezone.now()
