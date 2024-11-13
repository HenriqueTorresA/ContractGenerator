"""
Django settings for contract_generator project.

Generated by 'django-admin startproject' using Django 5.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path# settings.py
import dj_database_url
from decouple import config
from dotenv import load_dotenv
load_dotenv()



#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PWA_SERVICE_WORKER_PATH = os.path.join (BASE_DIR, 'app_cg/static/js', 'service-worker.js')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-k*^0a0u91jjt^r01#tq6)1eq!ug=#4w+!jytx*hxmf3=wtnt5x'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['.vercel.app', 'now.sh', '127.0.0.1', '*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pwa',
    'app_cg',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'contract_generator.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'app_cg', 'templates')],  # Este campo pode estar vazio
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

WSGI_APPLICATION = 'contract_generator.wsgi.application'

# Conexão do banco de homologação, caso necessário:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'neondb',
#         'USER': 'neondb_owner',
#         'PASSWORD': 'BWHcOTCQ9p2E',
#         'HOST': 'ep-proud-wildflower-a5cpnkjf-pooler.us-east-2.aws.neon.tech',  # ou o IP/URL do seu servidor de banco de dados
#         'PORT': '5432',      # porta padrão do PostgreSQL
#     }
# }

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
} # --> Necessário deixar essa constante, pois a Vercel irá ignorar o valor dessa constante, pois o valor 
#   --> está configurado no arquivo .env do projeto, e o mesmo está no gitIgnore, ou seja, a Vercel 
#   --> Irá utilizar a conexão que está configurada nas variáveis de ambiente da Vercel, que é a conexão 
#   --> do banco de dados de Produção, de forma que, em ambiente de desenvolvimento, local, será utilizada
#   --> conexão com o banco de homologação, e depois que é feito deployment na Vercel, será utilizado banco em produção


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'  # URL prefix para arquivos estáticos
# MEDIA_URL = '/media/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_ROOT = BASE_DIR/'static'
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'app_cg', 'static')]  # Local onde os arquivos estáticos estão armazenados
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

PWA_APP_NAME = 'ContractGenerator'
PWA_APP_DESCRIPTION = "ContractGenerator Django PWA"
PWA_APP_THEME_COLOR = '#000000'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {
        'src': '/static/images/contract-image-160x103.jpg',
        'sizes': '160x103'
    },
    {
        'src': '/static/images/icon-192x192.png',
        'sizes': '192x192'
    },
    {
        'src': '/static/images/icon-512x512.png',
        'sizes': '512x512'
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/images/contract-image-160x103.jpg',
        'sizes': '160x103'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/images/contract-image-160x103.jpg',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'


# Tempo de expiração da sessão em segundos (30 minutos = 30 * 60 segundos)
SESSION_COOKIE_AGE = 30 * 60

# Define que a sessão expira quando o usuário fechar o navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Define que a sessão será renovada a cada nova requisição dentro do período de 30 minutos
SESSION_SAVE_EVERY_REQUEST = True

