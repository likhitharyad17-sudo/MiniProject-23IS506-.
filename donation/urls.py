from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('donate/', views.donate_blood, name='donate_blood'),
    path('request/', views.request_blood, name='request_blood'),
    path('profile/', views.profile, name='profile'),
]
