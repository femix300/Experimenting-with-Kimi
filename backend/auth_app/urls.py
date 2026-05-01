from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.firebase_login, name="auth-firebase-login"),
    path("logout/", views.firebase_logout, name="auth-firebase-logout"),
    path("me/", views.me, name="auth-me"),
]
