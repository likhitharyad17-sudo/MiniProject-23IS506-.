import json
import math
import re
from collections import Counter

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Donation, BloodRequest, Profile, BLOOD_TYPES


def home(request):
    """
    Home page: shows options for admin, login, register.
    """
    return render(request, 'donation/home.html')


def register(request):
    """
    Custom registration view with password strength validation.
    Rules:
      - At least 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character
      - Must match confirm password
    """
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Basic checks
        if not username or not email or not password or not confirm_password:
            messages.error(request, "Please fill all the fields.")
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        # Password rules
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("register")

        if not re.search(r"[A-Z]", password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect("register")

        if not re.search(r"[a-z]", password):
            messages.error(request, "Password must contain at least one lowercase letter.")
            return redirect("register")

        if not re.search(r"[0-9]", password):
            messages.error(request, "Password must contain at least one digit.")
            return redirect("register")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect("register")

        # Username uniqueness check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return redirect("register")

        # Email uniqueness (optional but good)
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Please login instead.")
            return redirect("register")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.save()

        messages.success(request, "Registration successful. Please login.")
        return redirect("login")

    return render(request, "donation/register.html")


@login_required
def dashboard(request):
    """
    Dashboard:
      - Shows nearby donors (distance sorted)
      - Shows live map markers for donors and blood requests
      - Shows summary of active (APPROVED) blood requests by blood group
      - Lists approved blood requests
    """
    profile = request.user.profile

    # All active donations
    donations = Donation.objects.filter(active=True)

    # Requests shown on dashboard (approved ones)
    approved_requests = BloodRequest.objects.filter(status='APPROVED')

    user_lat = profile.latitude
    user_lng = profile.longitude

    def haversine(lat1, lon1, lat2, lon2):
        """Return distance in km between two lat/lng points."""
        if None in (lat1, lon1, lat2, lon2):
            return None
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2) ** 2 +
            math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # ---------- Nearby donors ----------
    nearby_donations = []

    for d in donations:
        dist = None
        if user_lat is not None and user_lng is not None:
            dist = haversine(user_lat, user_lng, d.latitude, d.longitude)

        nearby_donations.append({
            "id": d.id,
            "donor": d.donor.username,
            "blood_type": d.blood_type,
            "units": d.units_available,
            "lat": d.latitude,
            "lng": d.longitude,
            # 999999 if distance unknown so sorting still works
            "distance": dist if dist is not None else 999999,
        })

    nearby_donations = sorted(nearby_donations, key=lambda x: x["distance"])

    # JSON string for JavaScript (donor map markers)
    donors_json = json.dumps(nearby_donations)

    # ---------- Requests data for map ----------
    requests_data = []
    for r in approved_requests:
        dist = None
        if user_lat is not None and user_lng is not None and r.latitude is not None and r.longitude is not None:
            dist = haversine(user_lat, user_lng, r.latitude, r.longitude)

        requests_data.append({
            "id": r.id,
            "patient_name": r.patient_name,
            "blood_type": r.blood_type,
            "units": r.units_needed,
            "lat": r.latitude,
            "lng": r.longitude,
            "hospital_name": r.hospital_name,
            "urgency": r.urgency,
            "distance": dist if dist is not None else 999999,
        })

    requests_json = json.dumps(requests_data)

    # ---------- Active requests summary (by blood group) ----------
    bt_counts = Counter(approved_requests.values_list('blood_type', flat=True))
    active_requests_summary = [
        {"blood_type": bt, "count": cnt}
        for bt, cnt in bt_counts.items()
    ]

    context = {
        "profile": profile,
        "nearby_donations": nearby_donations,
        "donors_json": donors_json,
        "requests_json": requests_json,               # 👈 NEW
        "blood_requests": approved_requests,
        "active_requests_summary": active_requests_summary,
    }
    return render(request, 'donation/dashboard.html', context)


@login_required
def donate_blood(request):
    """
    Donate blood:
      - Captures user blood type, units, and geolocation (from hidden fields).
      - Creates Donation entry.
      - Updates Profile as donor.
    """
    profile = request.user.profile

    if request.method == 'POST':
        blood_type = request.POST.get('blood_type')
        units = request.POST.get('units')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')

        if not (blood_type and units and lat and lng):
            messages.error(request, "Please fill all fields and allow location access.")
            return redirect('donate_blood')

        Donation.objects.create(
            donor=request.user,
            blood_type=blood_type,
            units_available=int(units),
            latitude=float(lat),
            longitude=float(lng),
        )

        # Update profile as donor
        profile.blood_type = blood_type
        profile.is_donor = True
        profile.latitude = float(lat)
        profile.longitude = float(lng)
        profile.save()

        messages.success(request, "Thank you! Your donation is now visible on the map.")
        return redirect('dashboard')

    return render(request, 'donation/donate.html', {"blood_types": BLOOD_TYPES})


@login_required
def request_blood(request):
    """
    Request blood:
      - User submits patient & hospital details with location.
      - Request stored as PENDING for admin approval.
    """
    if request.method == 'POST':
        patient_name = request.POST.get('patient_name')
        blood_type = request.POST.get('blood_type')
        units = request.POST.get('units')
        hospital_name = request.POST.get('hospital_name')
        address = request.POST.get('address')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        urgency = request.POST.get('urgency')

        if not all([patient_name, blood_type, units, hospital_name, address, lat, lng]):
            messages.error(request, "Please fill all fields and allow location access.")
            return redirect('request_blood')

        BloodRequest.objects.create(
            requester=request.user,
            patient_name=patient_name,
            blood_type=blood_type,
            units_needed=int(units),
            hospital_name=hospital_name,
            address=address,
            latitude=float(lat),
            longitude=float(lng),
            urgency=urgency or "HIGH",
            status="PENDING",   # admin will approve
        )

        messages.success(request, "Request submitted. Waiting for admin approval.")
        return redirect('dashboard')

    return render(request, 'donation/request.html', {"blood_types": BLOOD_TYPES})


@login_required
def profile(request):
    """
    Profile page:
      - Shows user's basic info + phone + radius preference.
      - Allows updating phone and radius_km.
    """
    profile = request.user.profile

    if request.method == 'POST':
        phone = request.POST.get('phone')
        radius = request.POST.get('radius_km')

        profile.phone = phone
        if radius:
            profile.radius_km = int(radius)

        profile.save()
        messages.success(request, "Profile updated.")
        return redirect('profile')

    return render(request, 'donation/profile.html', {"profile": profile})
