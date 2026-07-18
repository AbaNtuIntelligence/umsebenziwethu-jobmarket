from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import User

@receiver(pre_save, sender=User)
def delete_replaced_avatar(sender, instance, **kwargs):
    if not instance.pk:
        return
    previous = User.objects.filter(pk=instance.pk).only("avatar").first()
    if previous and previous.avatar and previous.avatar != instance.avatar:
        previous.avatar.delete(save=False)

@receiver(post_delete, sender=User)
def delete_user_avatar(sender, instance, **kwargs):
    if instance.avatar:
        instance.avatar.delete(save=False)
