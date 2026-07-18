import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("jobs", "0006_job_address_visibility_job_district_and_more"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Interview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("external", "External meeting link"), ("zoom", "Zoom"), ("google_meet", "Google Meet"), ("microsoft_teams", "Microsoft Teams"), ("whatsapp", "WhatsApp"), ("jitsi", "UmsebenziWethu Live / Jitsi")], max_length=24)),
                ("title", models.CharField(default="Job interview", max_length=200)),
                ("scheduled_start", models.DateTimeField(db_index=True)),
                ("scheduled_end", models.DateTimeField()),
                ("timezone_name", models.CharField(default="Africa/Johannesburg", max_length=64)),
                ("join_url", models.URLField(blank=True, max_length=1000)),
                ("host_url", models.URLField(blank=True, max_length=1000)),
                ("provider_meeting_id", models.CharField(blank=True, max_length=200)),
                ("instructions", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("scheduled", "Scheduled"), ("reschedule_requested", "Reschedule requested"), ("cancelled", "Cancelled"), ("completed", "Completed"), ("employer_no_show", "Employer did not attend"), ("candidate_no_show", "Candidate did not attend"), ("technical_failure", "Technical failure")], db_index=True, default="scheduled", max_length=24)),
                ("candidate_response", models.CharField(choices=[("pending", "Awaiting response"), ("accepted", "Accepted"), ("declined", "Declined"), ("reschedule", "Requested another time")], default="pending", max_length=20)),
                ("candidate_response_note", models.TextField(blank=True)),
                ("recording_allowed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interviews", to="jobs.application")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_interviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("scheduled_start",)},
        ),
        migrations.CreateModel(
            name="RecruitmentSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("session_type", models.CharField(choices=[("group_briefing", "Applicant group briefing"), ("public_broadcast", "Public opportunity broadcast")], max_length=24)),
                ("visibility", models.CharField(choices=[("invited", "Invited applicants only"), ("public", "Public")], max_length=16)),
                ("provider", models.CharField(choices=[("external", "External meeting link"), ("zoom", "Zoom"), ("google_meet", "Google Meet"), ("microsoft_teams", "Microsoft Teams"), ("whatsapp", "WhatsApp"), ("jitsi", "UmsebenziWethu Live / Jitsi")], max_length=24)),
                ("scheduled_start", models.DateTimeField(db_index=True)),
                ("scheduled_end", models.DateTimeField()),
                ("timezone_name", models.CharField(default="Africa/Johannesburg", max_length=64)),
                ("join_url", models.URLField(blank=True, max_length=1000)),
                ("host_url", models.URLField(blank=True, max_length=1000)),
                ("provider_meeting_id", models.CharField(blank=True, max_length=200)),
                ("capacity", models.PositiveIntegerField(default=50)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("scheduled", "Scheduled"), ("live", "Live"), ("completed", "Completed"), ("cancelled", "Cancelled")], db_index=True, default="scheduled", max_length=16)),
                ("recording_allowed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("host", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="hosted_recruitment_sessions", to=settings.AUTH_USER_MODEL)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recruitment_sessions", to="jobs.job")),
            ],
            options={"ordering": ("scheduled_start",)},
        ),
        migrations.CreateModel(
            name="InterviewEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("scheduled", "Scheduled"), ("rescheduled", "Rescheduled"), ("accepted", "Accepted"), ("declined", "Declined"), ("reschedule_requested", "Reschedule requested"), ("join_requested", "Join requested"), ("cancelled", "Cancelled"), ("completed", "Completed"), ("employer_no_show", "Employer no-show"), ("candidate_no_show", "Candidate no-show"), ("technical_failure", "Technical failure")], max_length=30)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="interview_events", to=settings.AUTH_USER_MODEL)),
                ("interview", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="jobs.interview")),
            ],
            options={"ordering": ("created_at",)},
        ),
        migrations.CreateModel(
            name="RecruitmentSessionParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("response", models.CharField(choices=[("invited", "Invited"), ("accepted", "Accepted"), ("declined", "Declined"), ("attended", "Attended"), ("no_show", "Did not attend")], default="invited", max_length=16)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("joined_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("application", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="recruitment_session_participation", to="jobs.application")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="jobs.recruitmentsession")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recruitment_session_participation", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(model_name="interview", index=models.Index(fields=["status", "scheduled_start"], name="jobs_interv_status_44f9db_idx")),
        migrations.AddIndex(model_name="recruitmentsession", index=models.Index(fields=["visibility", "status", "scheduled_start"], name="jobs_recrui_visibil_415469_idx")),
        migrations.AddConstraint(model_name="interview", constraint=models.CheckConstraint(condition=models.Q(("scheduled_end__gt", models.F("scheduled_start"))), name="interview_end_after_start")),
        migrations.AddConstraint(model_name="recruitmentsession", constraint=models.CheckConstraint(condition=models.Q(("scheduled_end__gt", models.F("scheduled_start"))), name="session_end_after_start")),
        migrations.AddConstraint(model_name="recruitmentsessionparticipant", constraint=models.UniqueConstraint(fields=("session", "user"), name="one_participation_per_session_user")),
    ]
