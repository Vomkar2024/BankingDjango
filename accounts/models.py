from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomerProfile(models.Model):
    KYC_STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('pending', 'Pending Verification'),
        ('in_review', 'In Review'),
        ('rejected', 'Rejected'),
    ]

    TIER_CHOICES = [
        ('standard', 'Standard'),
        ('gold', 'Gold Privilege'),
        ('platinum', 'Platinum Elite'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, default='+91 98765 43210')
    pan_number = models.CharField(max_length=15, blank=True, default='ABCDE1234F')
    aadhaar_last4 = models.CharField(max_length=4, blank=True, default='5678')
    address = models.CharField(max_length=255, blank=True, default='42, Marine Drive, Nariman Point')
    city = models.CharField(max_length=100, blank=True, default='Mumbai')
    state = models.CharField(max_length=100, blank=True, default='Maharashtra')
    pincode = models.CharField(max_length=10, blank=True, default='400021')
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='verified')
    account_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='platinum')
    avatar_color = models.CharField(max_length=100, default='from-blue-600 to-indigo-600')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.kyc_status}"

    @property
    def full_name(self):
        name = self.user.get_full_name()
        return name if name else self.user.username

    @property
    def initials(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        elif self.user.first_name:
            return self.user.first_name[:2].upper()
        return self.user.username[:2].upper()


@receiver(post_save, sender=User)
def create_or_update_customer_profile(sender, instance, created, **kwargs):
    if created:
        CustomerProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
