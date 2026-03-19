from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from allauth.account.signals import user_signed_up

class Profile(models.Model):
    CHOICES = [
        ('passenger', 'Passenger'),
        ('driver', 'Driver'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=CHOICES)

    def __str__(self):
        return f"{self.user.username} {self.role}"
    
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save() 

@receiver(user_signed_up)
def handle_social_signup(request, user, **kwargs):
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user, role='')