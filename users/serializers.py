from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from products.serializers import ProductSerializer
from .models import UserProfile

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
    username = serializers.CharField()
    email = serializers.CharField()
    password = serializers.CharField()
    password2 = serializers.CharField()

    class Meta:
        fields = [
            "username",
            "email",    
            "password",
            "password2",
        ]

    def validate(self, attrs):
        password = attrs.get("password");
        password2 = attrs.get("password2");
        username = attrs.get("username");
        email = attrs.get("email");

        if password != password2:
            raise ValidationError(detail="passwords do not match")
        
        if User.objects.filter(username=username).exists():
            raise ValidationError(detail="username already exists")
        
        if User.objects.filter(email=email).exists():
            raise ValidationError(detail="email already exists")


        return attrs