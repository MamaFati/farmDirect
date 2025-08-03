from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from guardian.shortcuts import get_objects_for_user
from products.models import Product
from .models import Cart, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer


class CartView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(request_body=CartItemSerializer)
    def post(self, request, *args, **kwargs):
        if not request.user.groups.filter(name="Buyers").exists():
            return Response(
                {"detail": "Only buyers can manage carts"},
                status=status.HTTP_403_FORBIDDEN,
            )
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(cart=cart)
            return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            cart = Cart.objects.get(buyer=request.user)
            return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response(
                {"detail": "Cart not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(request_body=CartItemSerializer)
    def delete(self, request, *args, **kwargs):
        try:
            cart = Cart.objects.get(buyer=request.user)
            item_id = request.data.get("item_id")
            if item_id:
                cart.items.filter(id=item_id).delete()
                return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
            return Response(
                {"detail": "Item ID required"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Cart.DoesNotExist:
            return Response(
                {"detail": "Cart not found"}, status=status.HTTP_404_NOT_FOUND
            )


class OrderView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if not request.user.groups.filter(name="Buyers").exists():
            return Response(
                {"detail": "Only buyers can place orders"},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            cart = Cart.objects.get(buyer=request.user)
            if not cart.items.exists():
                return Response(
                    {"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )
            order = Order.objects.create(buyer=request.user)
            total_amount = 0
            for item in cart.items.all():
                total_amount += item.product.price * item.quantity
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_time=item.product.price,
                )
            order.total_amount = total_amount
            order.save()
            cart.items.all().delete()  # Clear cart
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Cart.DoesNotExist:
            return Response(
                {"detail": "Cart not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, *args, **kwargs):
        if request.user.groups.filter(name="Farmers").exists():
            orders = Order.objects.filter(
                items__product__farmer=request.user
            ).distinct()
        else:
            orders = Order.objects.filter(buyer=request.user)
        return Response(
            OrderSerializer(orders, many=True).data, status=status.HTTP_200_OK
        )

    # permission_classes = (IsAuthenticated,)
    # def get(self, request, *args, **kwargs):
    #     if request.user.groups.filter(name='Farmers').exists():
    #         products = get_objects_for_user(request.user, 'users.view_product', Product)
    #         orders = Order.objects.filter(items__product__farmer=request.user).distinct()
    #         data = {
    #             'products': ProductSerializer(products, many=True).data,
    #             'recent_orders': OrderSerializer(orders[:5], many=True).data
    #         }
    #     else:
    #         orders = Order.objects.filter(buyer=request.user)
    #         data = {
    #             'user': UserSerializer(request.user).data,
    #             'order_history': OrderSerializer(orders, many=True).data
    #         }
    #     return Response(data, status=status.HTTP_200_OK)
