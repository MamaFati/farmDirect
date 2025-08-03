from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from users.models import UserProfile
from products.models import Product
from carts.models import Cart
from guardian.shortcuts import assign_perm
from django.urls import reverse
from datetime import date

# Existing CartTests, OrderTests, and ProductTests classes (unchanged, omitted for brevity)

class UserTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Setup content types
        user_content_type = ContentType.objects.get_for_model(User)
        product_content_type = ContentType.objects.get_for_model(Product)

        # Setup groups
        self.farmers_group, _ = Group.objects.get_or_create(name='Farmers')
        self.buyers_group, _ = Group.objects.get_or_create(name='Buyers')

        # Setup permissions
        farmers_perms = [
            ('view_user', user_content_type),
            ('change_user', user_content_type),
            ('add_product', product_content_type),
            ('change_product', product_content_type),
            ('delete_product', product_content_type),
            ('view_product', product_content_type),
        ]
        buyers_perms = [
            ('view_user', user_content_type),
            ('change_user', user_content_type),
            ('view_product', product_content_type),
        ]
        self.farmers_group.permissions.set([
            Permission.objects.get(codename=codename, content_type=content_type)
            for codename, content_type in farmers_perms
        ])
        self.buyers_group.permissions.set([
            Permission.objects.get(codename=codename, content_type=content_type)
            for codename, content_type in buyers_perms
        ])

        # Setup users
        self.buyer = User.objects.create_user(username='buyer1', email='buyer1@example.com', password='password123')
        self.farmer = User.objects.create_user(username='farmer1', email='farmer1@example.com', password='password123')

        UserProfile.objects.create(user=self.buyer, role='buyer')
        UserProfile.objects.create(user=self.farmer, role='farmer')
        self.buyer.groups.add(self.buyers_group)
        self.farmer.groups.add(self.farmers_group)

        assign_perm('change_user', self.buyer, self.buyer)
        assign_perm('change_user', self.farmer, self.farmer)
        assign_perm('view_user', self.buyer, self.buyer)
        assign_perm('view_user', self.farmer, self.farmer)

    def authenticate(self, user):
        """Helper to authenticate a user and return JWT token."""
        response = self.client.post(
            reverse('users:token_obtain_pair', kwargs={'version': 'v1'}),
            {'username': user.username, 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Authentication failed")
        return response.data['access']

    def test_register_buyer(self):
        """Test registering a new buyer."""
        data = {
            'username': 'buyer2',
            'email': 'buyer2@example.com',
            'password': 'password123',
            'password2': 'password123',
            'role': 'buyer'
        }
        response = self.client.post(reverse('users:register-view', kwargs={'version': 'v1'}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'User created successfully, please login')

        user = User.objects.get(username='buyer2')
        self.assertEqual(UserProfile.objects.get(user=user).role, 'buyer')
        self.assertTrue(user.groups.filter(name='Buyers').exists())
        self.assertTrue(user.has_perm('auth.change_user', user))
        self.assertTrue(Cart.objects.filter(buyer=user).exists())
        self.assertEqual(User.objects.count(), 4)

    def test_register_farmer(self):
        """Test registering a new farmer."""
        data = {
            'username': 'farmer2',
            'email': 'farmer2@example.com',
            'password': 'password123',
            'password2': 'password123',
            'role': 'farmer'
        }
        response = self.client.post(reverse('users:register-view', kwargs={'version': 'v1'}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'User created successfully, please login')
        user = User.objects.get(username='farmer2')
        self.assertEqual(UserProfile.objects.get(user=user).role, 'farmer')
        self.assertTrue(user.groups.filter(name='Farmers').exists())
        self.assertTrue(user.has_perm('auth.change_user', user))
        self.assertFalse(Cart.objects.filter(buyer=user).exists())
        self.assertEqual(User.objects.count(), 4)

    def test_register_invalid_role(self):
        """Test registering with an invalid role."""
        data = {
            'username': 'invaliduser',
            'email': 'invalid@example.com',
            'password': 'password123',
            'password2': 'password123',
            'role': 'invalid'
        }
        response = self.client.post(reverse('users:register-view', kwargs={'version': 'v1'}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', response.data)
        self.assertEqual(User.objects.count(), 3)

    def test_register_duplicate_username(self):
        """Test registering with a duplicate username."""
        data = {
            'username': 'buyer1',
            'email': 'newbuyer@example.com',
            'password': 'password123',
            'password2': 'password123',
            'role': 'buyer'
        }
        response = self.client.post(reverse('users:register-view', kwargs={'version': 'v1'}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 3)

    def test_register_invalid_data(self):
        """Test registering with invalid data (e.g., missing fields)."""
        data = {
            'username': '',
            'email': 'invalid',
            'password': 'short',
            'password2': 'password123',
            'role': 'buyer'
        }
        response = self.client.post(reverse('users:register-view', kwargs={'version': 'v1'}), data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
        self.assertEqual(User.objects.count(), 3)

    def test_get_own_user_profile(self):
        """Test that a user can retrieve their own profile."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.get(
            reverse('users:user-view', kwargs={'version': 'v1', 'pk': self.buyer.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'buyer1')
        self.assertEqual(response.data['email'], 'buyer1@example.com')

    # def test_get_other_user_profile_denied(self):
    #     """Test that a user cannot retrieve another user's profile without permission."""
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
    #     response = self.client.get(
    #         reverse('users:user-view', kwargs={'version': 'v1', 'pk': self.farmer.id})
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(response.data['detail'], 'Permission denied')

    # def test_get_other_user_profile_allowed(self):
    #     """Test that a user can retrieve another user's profile with permission."""
    #     assign_perm('auth.view_user', self.buyer, self.farmer)
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
    #     response = self.client.get(
    #         reverse('users:user-view', kwargs={'version': 'v1', 'pk': self.farmer.id})
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['username'], 'farmer1')
    #     self.assertEqual(response.data['email'], 'farmer1@example.com')

    # def test_get_user_nonexistent(self):
    #     """Test retrieving a nonexistent user."""
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
    #     response = self.client.get(
    #         reverse('users:user-view', kwargs={'version': 'v1', 'pk': 999})
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #     self.assertEqual(response.data['detail'], 'No user found')

    # def test_user_unauthenticated_access(self):
    #     """Test that unauthenticated users cannot access user endpoints."""
    #     self.client.credentials()  # Clear credentials
    #     response = self.client.get(
    #         reverse('users:user-view', kwargs={'version': 'v1', 'pk': self.buyer.id})
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     # RegisterView allows unauthenticated access, so test invalid registration
    #     response = self.client.post(
    #         reverse('users:register-view', kwargs={'version': 'v1'}),
    #         {'username': ''}, format='json'
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_user_model_creation(self):
    #     """Test User and UserProfile model creation."""
    #     user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
    #     profile = UserProfile.objects.create(user=user, role='buyer')
    #     user.groups.add(self.buyers_group)
    #     assign_perm('change_user', user, user)
    #     self.assertEqual(user.username, 'testuser')
    #     self.assertEqual(profile.role, 'buyer')
    #     self.assertTrue(user.groups.filter(name='Buyers').exists())
    #     self.assertTrue(user.has_perm('auth.change_user', user))
    #     self.assertTrue(Cart.objects.filter(buyer=user).exists())