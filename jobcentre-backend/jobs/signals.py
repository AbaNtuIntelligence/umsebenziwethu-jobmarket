from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ApplicationDocument, JobMedia

@receiver(post_delete, sender=JobMedia)
@receiver(post_delete, sender=ApplicationDocument)
def delete_uploaded_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
