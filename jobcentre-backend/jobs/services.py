from django.conf import settings
from django.core.mail import send_mail
from .models import Notification

def notify(user, title, message, application=None, job=None):
    notification = Notification.objects.create(user=user, title=title, message=message, application=application, job=job)
    if user.email_notifications and user.email:
        send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    return notification
