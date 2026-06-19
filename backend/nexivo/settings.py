"""
Django settings for Nexivo project.
"""

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = config("DEBUG", default="0", cast=bool)
ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    # Local apps
    "apps.accounts.apps.AccountsConfig",
    "apps.datasets.apps.DatasetsConfig",
    "apps.dashboards.apps.DashboardsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.accounts.middleware.RoleMiddleware",
]

ROOT_URLCONF = "nexivo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "nexivo.wsgi.application"

# Database
# Detect if running inside Docker (DB_HOST defaults to 'postgres' in docker-compose)
def _resolve_db_host():
    host = config("DB_HOST", default="localhost")
    if host == "postgres" and not os.path.exists("/.dockerenv"):
        return "localhost"
    return host

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="nexivo"),
        "USER": config("POSTGRES_USER", default="nexivo_user"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="nexivo_pass"),
        "HOST": _resolve_db_host(),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "apps.accounts.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# JWT Settings
JWT_SECRET = config("SECRET_KEY", default=SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Superset Integration
SUPERSET_API_URL = config("SUPERSET_API_URL", default="http://superset:8088/api/v1")
SUPERSET_USERNAME = config("SUPERSET_USERNAME", default="admin")
SUPERSET_PASSWORD = config("SUPERSET_PASSWORD", default="admin")

# Redis / Celery
REDIS_URL = config("REDIS_URL", default="redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# DRF Spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    "TITLE": "Nexivo API",
    "DESCRIPTION": "Nexivo BI Platform API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Role choices
ROLE_FINANCE = "finance"
ROLE_SALES = "sales"
ROLE_CEO = "ceo"
ROLE_ADMIN = "admin"
ROLE_CHOICES = [
    (ROLE_FINANCE, "Finance"),
    (ROLE_SALES, "Sales"),
    (ROLE_CEO, "CEO"),
    (ROLE_ADMIN, "Admin"),
]
