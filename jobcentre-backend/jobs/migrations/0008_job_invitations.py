from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("jobs", "0007_interviews_and_recruitment_sessions"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="job",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to="jobs.job",
            ),
        ),
        migrations.CreateModel(
            name="JobInvitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="job_invitations", to=settings.AUTH_USER_MODEL)),
                ("employer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_job_invitations", to=settings.AUTH_USER_MODEL)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidate_invitations", to="jobs.job")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(
            model_name="jobinvitation",
            constraint=models.UniqueConstraint(fields=("job", "candidate"), name="one_invitation_per_job_candidate"),
        ),
    ]
