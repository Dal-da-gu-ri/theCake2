"""
Django settings for theCake2 project.

Generated by 'django-admin startproject' using Django 3.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os
from . import my_settings



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = 'mesn+zp#bh1k#k16(cwwd=iu!$*4u%95kcpl3g263(1r95%-go'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['3.35.132.61', '172.0.0.1']

SECRET_KEY = my_settings.SECRET_KEY

EMAIL_BACKEND = my_settings.EMAIL['EMAIL_BACKEND']
EMAIL_USE_TLS = my_settings.EMAIL['EMAIL_USE_TLS']
EMAIL_PORT = my_settings.EMAIL['EMAIL_PORT']
EMAIL_HOST = my_settings.EMAIL['EMAIL_HOST']
EMAIL_HOST_USER = my_settings.EMAIL['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = my_settings.EMAIL['EMAIL_HOST_PASSWORD']
SERVER_EMAIL = my_settings.EMAIL['SERVER_EMAIL']
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
#DEFAULT_FROM_EMAIL = my_settings.EMAIL['DEFAULT_FROM_EMAIL']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sslserver',
    'customer',
    'baker',
    'visitor',
    'home',
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

ROOT_URLCONF = 'theCake2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'theCake2/templates')],
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

WSGI_APPLICATION = 'theCake2.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.mysql',
         'NAME': 'thecakedb',
         'USER': 'root',
         'PASSWORD': 'daldaguri',
         'HOST': 'thecake3.c6vvk46sjvco.ap-northeast-2.rds.amazonaws.com',
         'PORT': '3306',
     }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'ko-KR'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

# 정적 파일을 관리할 루트 static 디렉터리
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'baker', 'static'),
    os.path.join(BASE_DIR, 'customer', 'static'),
    os.path.join(BASE_DIR, 'theCake2', 'static')
]


# 미디어 파일을 관리할 루트 media 디렉터리
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# 각 media file에 대한 URL prefix
MEDIA_URL = '/media/'

