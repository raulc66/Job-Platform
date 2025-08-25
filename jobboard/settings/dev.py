from .base import *

# Development-specific settings

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database configuration for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Additional development settings can be added here

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'