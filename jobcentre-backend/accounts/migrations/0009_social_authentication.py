from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0008_phone_otp_verification")]
    operations = [
        migrations.DeleteModel(name="PhoneOTPChallenge"),
        migrations.RemoveField(model_name="user", name="phone_verified_at"),
        migrations.AddField(model_name="user", name="last_auth_provider", field=models.CharField(blank=True, max_length=20)),
        migrations.CreateModel(
            name="SocialIdentity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("google", "Google"), ("microsoft", "Microsoft")], max_length=20)),
                ("subject", models.CharField(max_length=255)),
                ("email_at_link", models.EmailField(max_length=254)),
                ("linked_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="social_identities", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="AuthenticationEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.CharField(choices=[("social_signup", "Social sign-up"), ("social_signin", "Social sign-in"), ("social_link", "Social account linked"), ("social_link_failed", "Social account link failed")], max_length=40)),
                ("provider", models.CharField(max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="authentication_events", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name="socialidentity", constraint=models.UniqueConstraint(fields=("provider", "subject"), name="accounts_unique_social_identity")),
        migrations.AddIndex(model_name="socialidentity", index=models.Index(fields=["user", "provider"], name="acct_social_user_prov")),
        migrations.AddIndex(model_name="authenticationevent", index=models.Index(fields=["-created_at", "event"], name="accounts_auth_event_idx")),
    ]
