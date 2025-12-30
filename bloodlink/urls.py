from django.contrib import admin
from django.urls import path, include
from donation import views as donation_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home
    path('', donation_views.home, name='home'),

    # Auth
    path('login/', auth_views.LoginView.as_view(
        template_name='donation/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', donation_views.register, name='register'),

    # App routes
    path('donation/', include('donation.urls')),
]
