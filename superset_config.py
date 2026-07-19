import os

# Superset config
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'supersecretkey123')
SQLALCHEMY_DATABASE_URI = "postgresql://nexivo_user:nexivo_pass@postgres:5432/nexivo"

# Disable CSRF for API
WTF_CSRF_ENABLED = False

# Allow all origins for dev
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['*'],
}
