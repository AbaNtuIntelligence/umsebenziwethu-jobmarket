from django.contrib.auth.models import AbstractUser
from django.db import models

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
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    bio = models.TextField(blank=True)
    availability = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
