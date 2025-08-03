from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from guardian.shortcuts import assign_perm

from .serializers import RegisterSerializer, UserSerializer 
from .models import UserProfile

User = get_user_model()

class RegisterView(APIView):
    permission_classes = (AllowAny,)
    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            UserProfile.objects.create(user=user, role=serializer.validated_data['role'])
            group_name = 'Farmers' if serializer.validated_data['role'] == 'farmer' else 'Buyers'
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            assign_perm('change_user', user, user)
            if serializer.validated_data['role'] == 'buyer':
                Cart.objects.create(buyer=user)  # Create cart for buyers
            return Response({"detail": "User created successfully, please login"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, pk, *args, **kwargs):
        try:
            user = User.objects.get(pk=pk)
            if not request.user.has_perm('auth.view_user', user):
                return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            data = UserSerializer(user).data
            return Response(data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "No user found"}, status=status.HTTP_404_NOT_FOUND)


