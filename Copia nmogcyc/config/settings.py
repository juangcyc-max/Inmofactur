# config/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "clave-insegura-cambiar")
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    'corsheaders',  # ← AÑADE ESTO AL PRINCIPIO
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'facturacion',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'inmogcyc',
        'USER': 'postgres',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

ROOT_URLCONF = 'config.urls'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ← AÑADE ESTO
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',  # ← Esta línea ya existe
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# settings.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = '9cc89e001@smtp-brevo.com'   # ← ¡ESTE ES EL USUARIO SMTP!
EMAIL_HOST_PASSWORD = 'G2Mp5NQ9Z0dPR1ra'        # ← tu clave SMTP
DEFAULT_FROM_EMAIL = 'Inmobiliaria Soluciones <juangcyc@gmail.com>'  # ← este SÍ puede ser tu email
# config/settings.py
# ===== CONFIGURACIÓN DE CORS =====
CORS_ALLOW_ALL_ORIGINS = False  # ¡No lo pongas en True en producción!
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",  # ← Tu frontend Angular
    "http://127.0.0.1:4200",
]

# Opcional: Si quieres permitir todas las solicitudes (solo para desarrollo)
# CORS_ALLOW_ALL_ORIGINS = True
# =========================
# DJANGO REST FRAMEWORK
# =========================
INSTALLED_APPS += [
    'rest_framework',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
