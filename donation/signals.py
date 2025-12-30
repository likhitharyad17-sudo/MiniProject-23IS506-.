from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    # For a *new* user, create a profile.
    # For an existing user, ensure a profile exists (create if missing).
    Profile.objects.get_or_create(user=instance)
