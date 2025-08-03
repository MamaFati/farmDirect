from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from users.models import UserProfile
from products.models import Product, Category
from .models import Cart, CartItem, Order, OrderItem
from guardian.shortcuts import assign_perm
from django.urls import reverse
from datetime import date

from django.contrib.contenttypes.models import ContentType

# class CartTests(APITestCase):
#     def setUp(self):
#         self.client = APIClient()

#         # Setup content types
#         user_content_type = ContentType.objects.get_for_model(User)
#         product_content_type = ContentType.objects.get_for_model(Product)

#         # Setup groups
#         self.farmers_group, _ = Group.objects.get_or_create(name='Farmers')
#         self.buyers_group, _ = Group.objects.get_or_create(name='Buyers')

#         # Setup permissions
#         farmers_perms = [
#             ('view_user', user_content_type),
#             ('change_user', user_content_type),
#             ('add_product', product_content_type),
#             ('change_product', product_content_type),
#             ('delete_product', product_content_type),
#             ('view_product', product_content_type),
#         ]
#         buyers_perms = [
#             ('view_user', user_content_type),
#             ('change_user', user_content_type),
#             ('view_product', product_content_type),
#         ]
#         self.farmers_group.permissions.set([
#             Permission.objects.get(codename=codename, content_type=content_type)
#             for codename, content_type in farmers_perms
#         ])
#         self.buyers_group.permissions.set([
#             Permission.objects.get(codename=codename, content_type=content_type)
#             for codename, content_type in buyers_perms
#         ])

#         # Setup users
#         self.buyer = User.objects.create_user(username='buyer1', email='buyer1@example.com', password='password123')
#         self.farmer = User.objects.create_user(username='farmer1', email='farmer1@example.com', password='password123')
#         UserProfile.objects.create(user=self.buyer, role='buyer')
#         UserProfile.objects.create(user=self.farmer, role='farmer')
#         self.buyer.groups.add(self.buyers_group)
#         self.farmer.groups.add(self.farmers_group)
#         assign_perm('change_user', self.buyer, self.buyer)
#         assign_perm('change_user', self.farmer, self.farmer)

#         # Setup category and product
#         self.category = Category.objects.create(name='Vegetables')
#         self.product = Product.objects.create(
#             name='Carrots',
#             description='Fresh carrots',
#             price=2.50,
#             category=self.category,
#             quantity_available=100,
#             harvest_date=date(2025, 8, 1),
#             expiry_date=date(2025, 12, 1),
#             farmer=self.farmer
#         )
#         assign_perm('view_product', self.buyer, self.product)
#         assign_perm('view_product', self.farmer, self.product)
#         assign_perm('change_product', self.farmer, self.product)
#         assign_perm('delete_product', self.farmer, self.product)

#         # Setup cart
#         self.cart = Cart.objects.create(buyer=self.buyer)

#     def authenticate(self, user):
#         """Helper to authenticate a user and return JWT token."""
#         response = self.client.post(
#             reverse('users:token_obtain_pair', kwargs={'version': 'v1'}),
#             {'username': user.username, 'password': 'password123'},
#             format='json'
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK, "Authentication failed")
#         return response.data['access']

#     def test_add_item_to_cart_buyer(self):
#         """Test that a buyer can add an item to their cart."""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
#         data = {'product_id': self.product.id, 'quantity': 2}
#         response = self.client.post(reverse('cart', kwargs={'version': 'v1'}), data, format='json')
        
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['items'][0]['quantity'], 2)
#         self.assertEqual(response.data['items'][0]['product']['id'], self.product.id)
#         self.assertEqual(CartItem.objects.count(), 1)

#     def test_add_item_to_cart_farmer_denied(self):
#         """Test that a farmer cannot add items to a cart."""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
#         data = {'product_id': self.product.id, 'quantity': 2}
#         response = self.client.post(reverse('cart', kwargs={'version': 'v1'}), data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.assertEqual(response.data['detail'], 'Only buyers can manage carts')
#         self.assertEqual(CartItem.objects.count(), 0)

#     def test_add_item_invalid_product(self):
#         """Test adding an item with an invalid product ID."""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
#         data = {'product_id': 999, 'quantity': 2}
#         response = self.client.post(reverse('cart', kwargs={'version': 'v1'}), data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn('product_id', response.data)
#         self.assertEqual(CartItem.objects.count(), 0)

#     def test_get_cart_buyer(self):
#         """Test that a buyer can retrieve their cart."""
#         CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
#         response = self.client.get(reverse('cart', kwargs={'version': 'v1'}))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data['items']), 1)
#         self.assertEqual(response.data['items'][0]['quantity'], 3)

#     def test_get_cart_farmer_denied(self):
#         """Test that a farmer cannot retrieve a cart."""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
#         response = self.client.get(reverse('cart', kwargs={'version': 'v1'}))
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#         self.assertEqual(response.data['detail'], 'Cart not found')

#     def test_remove_item_from_cart_buyer(self):
#         """Test that a buyer can remove an item from their cart."""
#         cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
#         data = {'item_id': cart_item.id}
#         response = self.client.delete(reverse('cart', kwargs={'version': 'v1'}), data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(CartItem.objects.count(), 0)

#     def test_remove_item_invalid_id(self):
#         """Test removing an item with an invalid ID."""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
#         data = {'item_id': 999}
#         response = self.client.delete(reverse('cart', kwargs={'version': 'v1'}), data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(CartItem.objects.count(), 0)

#     def test_remove_item_farmer_denied(self):
#         """Test that a farmer cannot remove items from a cart."""
#         cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
#         data = {'item_id': cart_item.id}
#         response = self.client.delete(reverse('cart', kwargs={'version': 'v1'}), data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#         self.assertEqual(response.data['detail'], 'Only buyers can manage carts')
#         self.assertEqual(CartItem.objects.count(), 1)

#     def test_cart_model_creation(self):
#         """Test Cart and CartItem model creation."""
#         cart, _ = Cart.objects.get_or_create(buyer=self.buyer)
#         cart_item = CartItem.objects.create(cart=cart, product=self.product, quantity=5)
#         self.assertEqual(cart.buyer, self.buyer)
#         self.assertEqual(cart_item.cart, cart)
#         self.assertEqual(cart_item.product, self.product)
#         self.assertEqual(cart_item.quantity, 5)

#     def test_cart_unauthenticated_access(self):
#         """Test that unauthenticated users cannot access cart endpoints."""
#         self.client.credentials()  # Clear credentials
#         response = self.client.get(reverse('cart', kwargs={'version': 'v1'}))
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         response = self.client.post(reverse('cart', kwargs={'version': 'v1'}),
#                                   {'product_id': self.product.id, 'quantity': 2}, format='json')
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         response = self.client.delete(reverse('cart', kwargs={'version': 'v1'}),
#                                     {'item_id': 1}, format='json')
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_buyer_access_other_cart(self):
#         """Test that a buyer cannot access another buyer's cart."""
#         other_buyer = User.objects.create_user(username='buyer2', email='buyer2@example.com', password='password123')
#         UserProfile.objects.create(user=other_buyer, role='buyer')
#         other_buyer.groups.add(self.buyers_group)
#         other_cart = Cart.objects.create(buyer=other_buyer)
#         CartItem.objects.create(cart=other_cart, product=self.product, quantity=3)
        
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
#         response = self.client.get(reverse('cart', kwargs={'version': 'v1'}))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['buyer'], self.buyer.id)
#         self.assertNotEqual(response.data['buyer'], other_buyer.id)


class OrderTests(APITestCase):
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
        self.buyer2 = User.objects.create_user(username='buyer2', email='buyer2@example.com', password='password123')
        UserProfile.objects.create(user=self.buyer, role='buyer')
        UserProfile.objects.create(user=self.farmer, role='farmer')
        UserProfile.objects.create(user=self.buyer2, role='buyer')
        self.buyer.groups.add(self.buyers_group)
        self.farmer.groups.add(self.farmers_group)
        self.buyer2.groups.add(self.buyers_group)
        assign_perm('change_user', self.buyer, self.buyer)
        assign_perm('change_user', self.farmer, self.farmer)
        assign_perm('change_user', self.buyer2, self.buyer2)

        # Setup category and product
        self.category = Category.objects.create(name='Vegetables')
        self.product = Product.objects.create(
            name='Carrots',
            description='Fresh carrots',
            price=2.50,
            category=self.category,
            quantity_available=100,
            harvest_date=date(2025, 8, 1),
            expiry_date=date(2025, 12, 1),
            farmer=self.farmer
        )
        assign_perm('view_product', self.buyer, self.product)
        assign_perm('view_product', self.farmer, self.product)
        assign_perm('view_product', self.buyer2, self.product)
        assign_perm('change_product', self.farmer, self.product)
        assign_perm('delete_product', self.farmer, self.product)

        # Setup cart
        self.cart = Cart.objects.create(buyer=self.buyer)

    def authenticate(self, user):
        """Helper to authenticate a user and return JWT token."""
        response = self.client.post(
            reverse('users:token_obtain_pair', kwargs={'version': 'v1'}),
            {'username': user.username, 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Authentication failed")
        return response.data['access']

    def test_place_order_buyer(self):
        """Test that a buyer can place an order from their cart."""
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.post(reverse('orders', kwargs={'version': 'v1'}), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['buyer'], self.buyer.username)
        self.assertEqual(response.data['total_amount'], '5.00')  # 2 * $2.50
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['quantity'], 2)
        self.assertEqual(CartItem.objects.count(), 0)  # Cart cleared
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_place_order_empty_cart(self):
        """Test that a buyer cannot place an order with an empty cart."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.post(reverse('orders', kwargs={'version': 'v1'}), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Cart is empty')
        self.assertEqual(Order.objects.count(), 0)

    def test_place_order_farmer_denied(self):
        """Test that a farmer cannot place an order."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
        response = self.client.post(reverse('orders', kwargs={'version': 'v1'}), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Only buyers can place orders')
        self.assertEqual(Order.objects.count(), 0)

    def test_get_order_history_buyer(self):
        """Test that a buyer can retrieve their order history."""
        cart, _ = Cart.objects.get_or_create(buyer=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        order = Order.objects.create(buyer=self.buyer, total_amount=5.00)
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price_at_time=2.50)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer)}')
        response = self.client.get(reverse('orders', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['buyer'], self.buyer.username)
        self.assertEqual(response.data[0]['total_amount'], '5.00')

    def test_get_order_history_farmer(self):
        """Test that a farmer can retrieve orders for their products."""
        cart,_ = Cart.objects.get_or_create(buyer=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        order = Order.objects.create(buyer=self.buyer, total_amount=5.00)
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price_at_time=2.50)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.farmer)}')
        response = self.client.get(reverse('orders', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['items'][0]['product']['id'], self.product.id)

    def test_buyer_access_other_orders(self):
        """Test that a buyer cannot see another buyer's orders."""
        cart,_ = Cart.objects.get_or_create(buyer=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        order = Order.objects.create(buyer=self.buyer, total_amount=5.00)
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price_at_time=2.50)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.authenticate(self.buyer2)}')
        response = self.client.get(reverse('orders', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # buyer2 sees no orders

    def test_order_unauthenticated_access(self):
        """Test that unauthenticated users cannot access order endpoints."""
        self.client.credentials()  # Clear credentials
        response = self.client.get(reverse('orders', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(reverse('orders', kwargs={'version': 'v1'}), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_model_creation(self):
        """Test Order and OrderItem model creation."""
        order = Order.objects.create(buyer=self.buyer, total_amount=5.00)
        order_item = OrderItem.objects.create(
            order=order, product=self.product, quantity=2, price_at_time=2.50
        )
        self.assertEqual(order.buyer, self.buyer)
        self.assertEqual(order.total_amount, 5.00)
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.price_at_time, 2.50)