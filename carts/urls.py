from django.urls import path, include
from .views import  CartView, OrderView

urlpatterns = [

    path('', CartView.as_view(), name='cart'),
    path('orders/', OrderView.as_view(), name='orders'),
]