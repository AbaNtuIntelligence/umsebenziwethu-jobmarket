from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_jobseekerprofile_directory_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobseekerprofile",
            name="directory_show_avatar",
            field=models.BooleanField(
                default=False,
                help_text="Show the account avatar in the employer talent directory.",
            ),
        ),
    ]
