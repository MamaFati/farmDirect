from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm
from decouple import config
from users.models import UserProfile
from products.models import Product, Category 
from carts.models import Cart

def setup_groups():
    """Create Farmers and Buyers groups with appropriate permissions."""
    farmers_group, _ = Group.objects.get_or_create(name='Farmers')
    farmers_perms = ['auth.view_user', 'auth.change_user', 'users.add_product', 'users.change_product', 'users.delete_product', 'users.view_product']
    farmers_group.permissions.set(
        Permission.objects.filter(codename__in=[p.split('.')[-1] for p in farmers_perms])
    )

    buyers_group, _ = Group.objects.get_or_create(name='Buyers')
    buyers_perms = ['auth.view_user', 'auth.change_user', 'users.view_product']
    buyers_group.permissions.set(
        Permission.objects.filter(codename__in=[p.split('.')[-1] for p in buyers_perms])
    )

    return farmers_group, buyers_group

def setup_categories():
    """Create default categories."""
    categories = ['Vegetables', 'Fruits', 'Grains', 'Dairy']
    for name in categories:
        Category.objects.get_or_create(name=name)

def create_user(username, email, password, role, farmers_group, buyers_group):
    """Create a user with profile and assign to appropriate group."""
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, role=role)
        group = farmers_group if role == 'farmer' else buyers_group
        user.groups.add(group)
        assign_perm('change_user', user, user)
        if role == 'buyer':
            Cart.objects.create(buyer=user)
        return user
    return None

def create_superuser(username, email, password, farmers_group):
    """Create a superuser with profile and assign to Farmers group."""
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, role='farmer')
        user.groups.add(farmers_group)
        return user
    return None

def create_sample_product(farmer, index, category):
    """Create a sample product for a farmer."""
    product = Product.objects.create(
        name=f"Product {index} by {farmer.username}",
        description=f"Sample product from {farmer.username}",
        price=10.00 + index,
        category=category,
        quantity_available=100,
        harvest_date='2025-08-01',
        expiry_date='2025-12-01',
        farmer=farmer
    )
    assign_perm('change_product', farmer, product)
    assign_perm('delete_product', farmer, product)
    assign_perm('view_product', farmer, product)
    return product

class Command(BaseCommand):
    help = "Seeds the database with 5 farmers, 5 buyers, 1 superuser, and categories"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Seeding database..."))

        # Setup groups and categories
        farmers_group, buyers_group = setup_groups()
        setup_categories()
        self.stdout.write(self.style.SUCCESS("Created Farmers and Buyers groups and categories"))

        # Seed 5 farmers
        for i in range(1, 6):
            username = f"farmer{i}"
            email = f"farmer{i}@example.com"
            password = "password123"
            user = create_user(username, email, password, 'farmer', farmers_group, buyers_group)
            if user:
                self.stdout.write(self.style.SUCCESS(f"Created farmer: {username}"))
                # Create 2 sample products per farmer
                for j in range(1, 3):
                    category = Category.objects.order_by('?').first()  # Random category
                    product = create_sample_product(user, j, category)
                    self.stdout.write(f"Created product: {product.name}")
            else:
                self.stdout.write(self.style.SUCCESS(f"Farmer {username} already exists"))

        # Seed 5 buyers
        for i in range(1, 6):
            username = f"buyer{i}"
            email = f"buyer{i}@example.com"
            password = "password123"
            user = create_user(username, email, password, 'buyer', farmers_group, buyers_group)
            if user:
                self.stdout.write(self.style.SUCCESS(f"Created buyer: {username}"))
            else:
                self.stdout.write(self.style.ERROR(f"Buyer {username} already exists"))

        # Seed 1 superuser
        superuser_data = {
            "username": config('SUPERUSER_USERNAME', default='admin'),
            "email": config('SUPERUSER_EMAIL', default='admin@example.com'),
            "password": config('SUPERUSER_PASSWORD', default='admin123')
        }
        if create_superuser(**superuser_data, farmers_group=farmers_group):
            self.stdout.write(self.style.SUCCESS(f"Created superuser: {superuser_data['username']}"))
        else:
            self.stdout.write(self.style.ERROR(f"Superuser {superuser_data['username']} already exists"))

        self.stdout.write(self.style.ERROR("Seeding completed."))