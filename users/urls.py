from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserView
urlpatterns = [
    # Auth
    path("auth/login/",TokenObtainPairView.as_view(),name="login-view"),
    path("auth/refresh/",TokenRefreshView.as_view(),name="refresh-view"),
    path("auth/register/",RegisterView.as_view(),name="register-view"),

    # Users
    path("users/<int:pk>/",UserView.as_view(),name="user-view"),

]
