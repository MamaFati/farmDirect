from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Swagger API Info
schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version='v1',
        description="API documentation for your Django project",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def redirect_to_doc(request):
    return redirect("schema-swagger-ui")

urlpatterns = [
    path('farmer-direct/', admin.site.urls),
    # path('api/<version>/', include('rest_framework.urls')),
    path('', redirect_to_doc,name="redirect-to-doc"),
    
    path('api/<version>/', include('users.urls')),
    path('api/<version>/carts/', include('carts.urls')),
    path('api/<version>/products/', include('products.urls')),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # Add your app URLs here
]