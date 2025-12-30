from django.db import models
from django.contrib.auth.models import User

BLOOD_TYPES = [
    ("O+", "O+"), ("O-", "O-"),
    ("A+", "A+"), ("A-", "A-"),
    ("B+", "B+"), ("B-", "B-"),
    ("AB+", "AB+"), ("AB-", "AB-"),
]

REQUEST_STATUS = [
    ("PENDING", "Pending"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, blank=True)
    is_donor = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_donation_date = models.DateField(null=True, blank=True)
    radius_km = models.IntegerField(default=30)  # how far user is willing to travel

    def __str__(self):
        return self.user.username


class Donation(models.Model):
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    units_available = models.PositiveIntegerField(default=1)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.donor.username} - {self.blood_type} ({self.units_available} units)"


class BloodRequest(models.Model):
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    patient_name = models.CharField(max_length=100)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    units_needed = models.PositiveIntegerField()
    hospital_name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    urgency = models.CharField(max_length=20, choices=[
        ("CRITICAL", "Critical"),
        ("HIGH", "High"),
        ("MEDIUM", "Medium"),
    ], default="HIGH")
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.blood_type} ({self.status})"
