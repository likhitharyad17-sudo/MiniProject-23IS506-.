from django.contrib import admin
from .models import Profile, Donation, BloodRequest


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'blood_type', 'is_donor')


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'blood_type', 'units_available', 'active', 'created_at')
    list_filter = ('blood_type', 'active')


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'blood_type', 'units_needed', 'hospital_name',
                    'status', 'created_at')
    list_filter = ('blood_type', 'status', 'urgency')
