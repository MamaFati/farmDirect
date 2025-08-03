from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from .models import  Product, Category
from users.models import UserProfile
from guardian.shortcuts import assign_perm
from django.urls import reverse
from datetime import date

class ProductTests(APITestCase):
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
        self.farmer = User.objects.create_user(username='farmer1', email='farmer1@example.com', password='password123')
        self.farmer2 = User.objects.create_user(username='farmer2', email='farmer2@example.com', password='password123')
        self.buyer = User.objects.create_user(username='buyer1', email='buyer1@example.com', password='password123')
        UserProfile.objects.create(user=self.farmer, role='farmer')
        UserProfile.objects.create(user=self.farmer2, role='farmer')
        UserProfile.objects.create(user=self.buyer, role='buyer')
        self.farmer.groups.add(self.farmers_group)
        self.farmer2.groups.add(self.farmers_group)
        self.buyer.groups.add(self.buyers_group)
        assign_perm('change_user', self.farmer, self.farmer)
        assign_perm('change_user', self.farmer2, self.farmer2)
        assign_perm('change_user', self.buyer, self.buyer)

        # Setup categories
        self.category1 = Category.objects.create(name='Vegetables')
        self.category2 = Category.objects.create(name='Fruits')

        # Setup products
        self.product = Product.objects.create(
            name='Carrots',
            description='Fresh carrots',
            price=2.50,
            category=self.category1,
            quantity_available=100,
            harvest_date=date(2025, 8, 1),
            expiry_date=date(2025, 12, 1),
            farmer=self.farmer
        )
        self.product2 = Product.objects.create(
            name='Apples',
            description='Fresh apples',
            price=3.00,
            category=self.category2,
            quantity_available=50,
            harvest_date=date(2025, 8, 1),
            expiry_date=date(2025, 12, 1),
            farmer=self.farmer
        )
        assign_perm('view_product', self.farmer, self.product)
        assign_perm('view_product', self.farmer, self.product2)
        assign_perm('view_product', self.farmer2, self.product)
        assign_perm('view_product', self.farmer2, self.product2)
        assign_perm('view_product', self.buyer, self.product)
        assign_perm('view_product', self.buyer, self.product2)
        assign_perm('change_product', self.farmer, self.product)
        assign_perm('delete_product', self.farmer, self.product)
        assign_perm('change_product', self.farmer, self.product2)
        assign_perm('delete_product', self.farmer, self.product2)

    def authenticate(self, user):
        """Helper to authenticate a user and return JWT token."""
        response = self.client.post(
            reverse('users:token_obtain_pair', kwargs={'version': 'v1'}),
            {'username': user.username, 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Authentication failed")
        return response.data['access']

    def test_create_product_farmer(self):
        """Test that a farmer can create a product."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
        data = {
            'name': 'Tomatoes',
            'description': 'Fresh tomatoes',
            'price': 1.50,
            'category_id': self.category1.id,
            'quantity_available': 200,
            'harvest_date': '2025-08-01',
            'expiry_date': '2025-12-01'
        }
        response = self.client.post(reverse('product-list', kwargs={'version': 'v1'}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Tomatoes')
        self.assertEqual(response.data['farmer'], self.farmer.username)
        self.assertEqual(Product.objects.count(), 3)
        product = Product.objects.get(name='Tomatoes')
        self.assertTrue(self.farmer.has_perm('products.change_product', product))
        self.assertTrue(self.farmer.has_perm('products.delete_product', product))

    def test_create_product_buyer_denied(self):
        """Test that a buyer cannot create a product."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        data = {
            'name': 'Tomatoes',
            'description': 'Fresh tomatoes',
            'price': 1.50,
            'category_id': self.category1.id,
            'quantity_available': 200,
            'harvest_date': '2025-08-01',
            'expiry_date': '2025-12-01'
        }
        response = self.client.post(reverse('product-list', kwargs={'version': 'v1'}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to perform this action.')
        self.assertEqual(Product.objects.count(), 2)

    def test_create_product_invalid_data(self):
        """Test creating a product with invalid data."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
        data = {
            'name': '',  # Invalid: empty name
            'description': 'Invalid product',
            'price': -1,  # Invalid: negative price
            'category_id': self.category1.id,
            'quantity_available': 200,
            'harvest_date': '2025-08-01',
            'expiry_date': '2025-12-01'
        }
        response = self.client.post(reverse('product-list', kwargs={'version': 'v1'}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('price', response.data)
        self.assertEqual(Product.objects.count(), 2)

    def test_list_products_buyer(self):
        """Test that a buyer can list products."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.get(reverse('product-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Carrots')
        self.assertEqual(response.data[1]['name'], 'Apples')

    def test_list_products_farmer(self):
        """Test that a farmer can list products."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
        response = self.client.get(reverse('product-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Carrots')
        self.assertEqual(response.data[1]['name'], 'Apples')

    def test_search_products_by_name(self):
        """Test searching products by name."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.get(
            reverse('product-list', kwargs={'version': 'v1'}),
            {'name': 'Carrot'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Carrots')

    def test_filter_products_by_category(self):
        """Test filtering products by category."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.get(
            reverse('product-list', kwargs={'version': 'v1'}),
            {'category': self.category1.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Carrots')

    def test_filter_products_by_price(self):
        """Test filtering products by price range."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.get(
            reverse('product-list', kwargs={'version': 'v1'}),
            {'min_price': 2.00, 'max_price': 2.50}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Carrots')

    def test_retrieve_product_buyer(self):
        """Test that a buyer can retrieve a product detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.get(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Carrots')
        self.assertEqual(response.data['price'], '2.50')

    def test_update_product_farmer(self):
        """Test that a farmer can update their own product."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
        data = {
            'name': 'Updated Carrots',
            'description': 'Updated fresh carrots',
            'price': 3.00,
            'category_id': self.category1.id,
            'quantity_available': 150,
            'harvest_date': '2025-08-01',
            'expiry_date': '2025-12-01'
        }
        response = self.client.put(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id}),
            data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Carrots')
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, 3.00)

    def test_update_product_buyer_denied(self):
        """Test that a buyer cannot update a product."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        data = {
            'name': 'Updated Carrots',
            'description': 'Updated fresh carrots',
            'price': 3.00,
            'category_id': self.category1.id,
            'quantity_available': 150,
            'harvest_date': '2025-08-01',
            'expiry_date': '2025-12-01'
        }
        response = self.client.put(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id}),
            data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Carrots')

    def test_update_product_other_farmer_denied(self):
        """Test that a farmer cannot update another farmer's product."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer2)}')
        data = {
            'name': 'Updated Carrots',
            'description': 'Updated fresh carrots',
            'price': 3.00,
            'category_id': self.category1.id,
            'quantity_available': 150,
            'harvest_date': '2025-08-01',
            'expiry_date': '2025-12-01'
        }
        response = self.client.put(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id}),
            data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Carrots')

    def test_delete_product_farmer(self):
        """Test that a farmer can delete their own product."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
        response = self.client.delete(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 1)

    def test_delete_product_buyer_denied(self):
        """Test that a buyer cannot delete a product."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.delete(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Product.objects.count(), 2)

    def test_delete_product_other_farmer_denied(self):
        """Test that a farmer cannot delete another farmer's product."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer2)}')
        response = self.client.delete(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Product.objects.count(), 2)

    def test_product_unauthenticated_access(self):
        """Test that unauthenticated users cannot access product endpoints."""
        self.client.credentials()  # Clear credentials
        response = self.client.get(reverse('product-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(
            reverse('product-list', kwargs={'version': 'v1'}),
            {'name': 'Tomatoes'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.put(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id}),
            {'name': 'Updated Carrots'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.delete(
            reverse('product-detail', kwargs={'version': 'v1', 'pk': self.product.id})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_model_creation(self):
        """Test Product and Category model creation."""
        category = Category.objects.create(name='Grains')
        product = Product.objects.create(
            name='Rice',
            description='Brown rice',
            price=4.00,
            category=category,
            quantity_available=300,
            harvest_date=date(2025, 8, 1),
            expiry_date=date(2025, 12, 1),
            farmer=self.farmer
        )
        self.assertEqual(product.name, 'Rice')
        self.assertEqual(product.category, category)
        self.assertEqual(product.farmer, self.farmer)
        self.assertEqual(product.price, 4.00)
        self.assertEqual(category.name, 'Grains')