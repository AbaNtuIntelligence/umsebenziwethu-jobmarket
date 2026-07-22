from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_jobseekerprofile_professional_headline_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobseekerprofile",
            name="directory_visible",
            field=models.BooleanField(
                default=False,
                help_text="Allow employers to discover this professional profile.",
            ),
        ),
        migrations.AddField(
            model_name="jobseekerprofile",
            name="industry",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="jobseekerprofile",
            name="sector",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
