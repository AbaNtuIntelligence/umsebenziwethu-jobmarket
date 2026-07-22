from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0007_jobseekerprofile_directory_show_avatar")]
    operations = [
        migrations.AddField(model_name="user", name="phone_verified_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.CreateModel(
            name="PhoneOTPChallenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(max_length=20)),
                ("code_hash", models.CharField(max_length=128)),
                ("expires_at", models.DateTimeField()),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("max_attempts", models.PositiveSmallIntegerField(default=5)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("delivery_status", models.CharField(default="pending", max_length=20)),
                ("provider_reference", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="phone_otp_challenges", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(model_name="phoneotpchallenge", index=models.Index(fields=["user", "-created_at"], name="accounts_ph_user_id_9c49cc_idx")),
    ]
