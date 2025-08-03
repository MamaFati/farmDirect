from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from products.serializers import ProductSerializer
from .models import UserProfile
import re

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    products = ProductSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', 'products']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(max_length=254, required=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='buyer')

    def validate_username(self, value):
        """Validate username format (alphanumeric and underscores only)."""
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError("Username must contain only letters, numbers, and underscores.")
        if len(value) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        if User.objects.filter(username__iexact=value).exists():
            raise ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        """Normalize email to lowercase and check for duplicates."""
        normalized_email = value.lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise ValidationError("Email already exists.")
        return normalized_email

    def validate_password(self, value):
        """Validate password complexity."""
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'\d', value):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError("Password must contain at least one special character.")
        return value

    def validate(self, attrs):
        """Validate that passwords match."""
        password = attrs.get("password")
        password2 = attrs.get("password2")
        if password != password2:
            raise ValidationError({"password2": "Passwords do not match."})
        return attrs