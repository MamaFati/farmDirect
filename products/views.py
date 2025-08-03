from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from guardian.shortcuts import assign_perm, get_objects_for_user

from .models import Product, Category
from carts.models import Order
from carts.serializers import OrderSerializer
from .serializers import ( ProductSerializer, CategorySerializer
)

class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (IsAuthenticated,)
    def get_queryset(self):
        # Filter products based on view permission
        return get_objects_for_user(self.request.user, 'users.view_product', Product,accept_global_perms=False)
    def perform_create(self, serializer):
        if not self.request.user.groups.filter(name='Farmers').exists():
            return Response({"detail": "Only farmers can create products"}, status=status.HTTP_403_FORBIDDEN)
        product = serializer.save(farmer=self.request.user)
        assign_perm('change_product', self.request.user, product)
        assign_perm('delete_product', self.request.user, product)
        assign_perm('view_product', self.request.user, product)
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('name', openapi.IN_QUERY, description="Search by product name", type=openapi.TYPE_STRING),
        openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('min_price', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
        openapi.Parameter('max_price', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
    ])
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        name = request.query_params.get('name')
        category = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if name:
            queryset = queryset.filter(name__icontains=name)
        if category:
            queryset = queryset.filter(category_id=category)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get']  # Read-only for browsing

class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Farmers').exists():
            products = get_objects_for_user(request.user, 'users.view_product', Product,accept_global_perms=False)
            orders = Order.objects.filter(items__product__farmer=request.user).distinct()
            data = {
                'products': ProductSerializer(products, many=True).data,
                'recent_orders': OrderSerializer(orders[:5], many=True).data
            }
        else:
            orders = Order.objects.filter(buyer=request.user)
            data = {
                'user': UserSerializer(request.user).data,
                'order_history': OrderSerializer(orders, many=True).data
            }
        return Response(data, status=status.HTTP_200_OK)