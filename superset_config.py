import os

# Superset configuration for headless (embedded) usage

# Core
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "nexivo-superset-secret-key-change-me")
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_DATABASE_URI",
    f"postgresql://{os.environ.get('POSTGRES_USER', 'nexivo_user')}"
    f":{os.environ.get('POSTGRES_PASSWORD', 'nexivo_pass')}"
    f"@{os.environ.get('DB_HOST', 'postgres')}"
    f":{os.environ.get('DB_PORT', '5432')}"
    f"/{os.environ.get('POSTGRES_DB', 'nexivo')}"
)

# Security
WTF_CSRF_ENABLED = False
PREVENT_UNSAFE_DB_CONNECTIONS = False

# Feature flags for embedding
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ENABLE_EXPLORE_DRAG_AND_DROP": True,
}

# Allow all origins for development (restrict in production)
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": ["*"],
}

# Allow guest token creation
GUEST_ROLE_NAME = "Public"
GUEST_TOKEN_JWT_SECRET = os.environ.get("SUPERSET_SECRET_KEY", "nexivo-superset-secret-key-change-me")
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_HEADER_NAME = "X-GuestToken"
GUEST_TOKEN_JWT_EXP_SECONDS = 300  # 5 minutes

# Disable public role for security
PUBLIC_ROLE_LIKE = "Gamma"

# Enable REST API
FAB_API_SWAGGER_UI = True

# Redis caching (optional, falls back to in-memory)
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://redis:6379/0"),
}

# Data upload settings
UPLOAD_FOLDER = "/app/superset_home/uploads"
CSV_EXTENSIONS = {"csv", "tsv"}
EXCEL_EXTENSIONS = {"xlsx", "xls"}
ALLOWED_EXTENSIONS = CSV_EXTENSIONS | EXCEL_EXTENSIONS
