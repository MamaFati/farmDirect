## User Story: Connecting Farmers and Buyers

**As a farmer**, I want to register on FarmDirect, upload my products, and connect with buyers so that I can sell my produce efficiently.

### How It Works

1. **Registration**
    - Farmers sign up using their details on the registration page.
    - After registration, they can log in to their dashboard.

2. **Product Upload**
    - Farmers add new products by providing details such as name, description, price, and images.
    - Uploaded products are listed in their dashboard and visible to buyers.

3. **Connecting with Buyers**
    - Buyers browse available products and view farmer profiles.
    - Buyers can contact farmers directly through the platform to negotiate and place orders.

### Example Workflow

1. Farmer visits FarmDirect and registers an account.
2. After logging in, the farmer navigates to "Add Product" and uploads details of their produce.
3. Buyers browse products, view farmer profiles, and initiate contact or purchase.
4. The platform facilitates communication and transactions between farmers and buyers.

This workflow helps farmers reach a wider market and buyers access fresh produce directly from the source.

## Setup Guide: Django REST Framework, drf-yasg, drf-simplejwt, python-decouple

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### 1. Install Dependencies

```bash
pip install django djangorestframework drf-yasg djangorestframework-simplejwt python-decouple
```

### 2. Add to `INSTALLED_APPS` in `settings.py`

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'drf_yasg',
]
```

### 3. Configure `python-decouple`

Create a `.env` file in your project root:

```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Update `settings.py`:

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',')])
```

### 4. Configure Django REST Framework and SimpleJWT

Add to `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
```

### 5. Add JWT URLs to `urls.py`

```python
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # ...
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

### 6. Setup drf-yasg for API Documentation

Add to `urls.py`:

```python
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="FarmDirect API",
        default_version='v1',
        description="API documentation for FarmDirect",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
```

### 7. Run Migrations and Start Server

```bash
python manage.py migrate
python manage.py runserver
```

Your Django project is now set up with DRF, JWT authentication, environment variable management, and interactive API docs.