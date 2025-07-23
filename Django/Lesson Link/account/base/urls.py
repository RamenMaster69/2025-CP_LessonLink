from django.urls import path, include
from .views import authView, home
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", home, name="home"),
    path("signup/", authView, name="signup"),  # Sign up page
    path("login/", auth_views.LoginView.as_view(), name="login"),  # Corrected this line
    path("accounts/", include("django.contrib.auth.urls")),
]
