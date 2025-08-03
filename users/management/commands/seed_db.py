from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm
from decouple import config
from users.models import UserProfile
from products.models import Product, Category
from carts.models import Cart, CartItem, Order, OrderItem
from datetime import date, timedelta
import random

def setup_groups():
    """Create Farmers and Buyers groups with appropriate permissions."""
    user_content_type = ContentType.objects.get_for_model(User)
    product_content_type = ContentType.objects.get_for_model(Product)

    farmers_group, _ = Group.objects.get_or_create(name='Farmers')
    farmers_perms = [
        ('view_user', user_content_type),
        ('change_user', user_content_type),
        ('add_product', product_content_type),
        ('change_product', product_content_type),
        ('delete_product', product_content_type),
        ('view_product', product_content_type),
    ]
    farmers_group.permissions.set([
        Permission.objects.get(codename=codename, content_type=content_type)
        for codename, content_type in farmers_perms
    ])

    buyers_group, _ = Group.objects.get_or_create(name='Buyers')
    buyers_perms = [
        ('view_user', user_content_type),
        ('change_user', user_content_type),
        ('view_product', product_content_type),
    ]
    buyers_group.permissions.set([
        Permission.objects.get(codename=codename, content_type=content_type)
        for codename, content_type in buyers_perms
    ])

    return farmers_group, buyers_group

def setup_categories():
    """Create default categories."""
    categories = ['Vegetables', 'Fruits', 'Grains', 'Dairy', 'Herbs']
    for name in categories:
        Category.objects.get_or_create(name=name)

def create_user(username, email, password, role, first_name, last_name, farmers_group, buyers_group):
    """Create a user with profile and assign to appropriate group."""
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        UserProfile.objects.create(user=user, role=role)
        group = farmers_group if role == 'farmer' else buyers_group
        user.groups.add(group)
        assign_perm('change_user', user, user)
        assign_perm('view_user', user, user)
        if role == 'buyer':
            Cart.objects.create(buyer=user)
        return user
    return None

def create_superuser(username, email, password, farmers_group):
    """Create a superuser with profile and assign to Farmers group."""
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Admin',
            last_name='User'
        )
        UserProfile.objects.create(user=user, role='farmer')
        user.groups.add(farmers_group)
        assign_perm('change_user', user, user)
        assign_perm('view_user', user, user)
        return user
    return None

def create_sample_product(farmer, index, category, buyers):
    """Create a sample product for a farmer and assign view permissions to buyers."""
    product = Product.objects.create(
        name=f"Product {index} by {farmer.username}",
        description=f"Sample product from {farmer.username}",
        price=5.00 + (index * 2.50),  # Vary price for realism
        category=category,
        quantity_available=random.randint(50, 200),
        harvest_date=date(2025, 8, 1),
        expiry_date=date(2025, 12, 1),
        farmer=farmer
    )
    assign_perm('change_product', farmer, product)
    assign_perm('delete_product', farmer, product)
    assign_perm('view_product', farmer, product)
    # Assign view_product permission to all buyers
    for buyer in buyers:
        assign_perm('view_product', buyer, product)
    return product

def create_sample_cart_item(cart, product):
    """Create a sample cart item for a buyer's cart."""
    return CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=random.randint(1, 5)
    )

def create_sample_order(buyer, products):
    """Create a sample order with order items for a buyer."""
    total_amount = 0
    order = Order.objects.create(
        buyer=buyer,
        total_amount=0  # Will update after adding items
    )
    # Add 1-3 random products to the order
    selected_products = random.sample(products, random.randint(1, min(3, len(products))))
    for product in selected_products:
        quantity = random.randint(1, 5)
        price_at_time = product.price
        total_amount += quantity * price_at_time
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price_at_time=price_at_time
        )
    order.total_amount = total_amount
    order.save()
    return order

class Command(BaseCommand):
    help = "Seeds the database with users, categories, products, carts, cart items, and orders"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Seeding database..."))

        # Setup groups and categories
        farmers_group, buyers_group = setup_groups()
        setup_categories()
        self.stdout.write(self.style.SUCCESS("Created Farmers and Buyers groups and categories"))

        # Get configurable counts from .env
        num_farmers = config('SEED_FARMERS', default=5, cast=int)
        num_buyers = config('SEED_BUYERS', default=5, cast=int)
        num_products_per_farmer = config('SEED_PRODUCTS_PER_FARMER', default=2, cast=int)
        num_orders_per_buyer = config('SEED_ORDERS_PER_BUYER', default=1, cast=int)

        # Seed farmers
        farmers = []
        for i in range(1, num_farmers + 1):
            username = f"farmer{i}"
            email = f"farmer{i}@example.com"
            password = "password123!"
            first_name = f"Farmer{i}"
            last_name = f"User{i}"
            user = create_user(username, email, password, 'farmer', first_name, last_name, farmers_group, buyers_group)
            if user:
                self.stdout.write(self.style.SUCCESS(f"Created farmer: {username}"))
                farmers.append(user)
            else:
                self.stdout.write(self.style.WARNING(f"Farmer {username} already exists"))

        # Seed buyers
        buyers = []
        for i in range(1, num_buyers + 1):
            username = f"buyer{i}"
            email = f"buyer{i}@example.com"
            password = "password123!"
            first_name = f"Buyer{i}"
            last_name = f"User{i}"
            user = create_user(username, email, password, 'buyer', first_name, last_name, farmers_group, buyers_group)
            if user:
                self.stdout.write(self.style.SUCCESS(f"Created buyer: {username}"))
                buyers.append(user)
            else:
                self.stdout.write(self.style.WARNING(f"Buyer {username} already exists"))

        # Seed superuser
        superuser_data = {
            "username": config('SUPERUSER_USERNAME', default='admin'),
            "email": config('SUPERUSER_EMAIL', default='admin@example.com'),
            "password": config('SUPERUSER_PASSWORD', default='admin123!')
        }
        if create_superuser(**superuser_data, farmers_group=farmers_group):
            self.stdout.write(self.style.SUCCESS(f"Created superuser: {superuser_data['username']}"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser {superuser_data['username']} already exists"))

        # Seed products for each farmer
        products = []
        for farmer in farmers:
            for j in range(1, num_products_per_farmer + 1):
                category = Category.objects.order_by('?').first()  # Random category
                product = create_sample_product(farmer, j, category, buyers)
                products.append(product)
                self.stdout.write(self.style.SUCCESS(f"Created product: {product.name}"))

        # Seed cart items for each buyer's cart
        for buyer in buyers:
            cart = Cart.objects.get(buyer=buyer)
            # Add 1-3 random products to cart
            selected_products = random.sample(products, random.randint(1, min(3, len(products))))
            for product in selected_products:
                cart_item = create_sample_cart_item(cart, product)
                self.stdout.write(self.style.SUCCESS(f"Created cart item: {cart_item.product.name} for {buyer.username}"))

        # Seed orders for each buyer
        for buyer in buyers:
            for k in range(1, num_orders_per_buyer + 1):
                order = create_sample_order(buyer, products)
                # Use the correct reverse accessor (assuming related_name='items')
                order_item_count = len(order.items.all()) if hasattr(order, 'items') else OrderItem.objects.filter(order=order).count()
                self.stdout.write(self.style.SUCCESS(f"Created order {k} for {buyer.username} with {order_item_count} items"))

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully."))