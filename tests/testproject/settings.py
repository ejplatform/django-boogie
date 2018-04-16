import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'ss68t83q^4xx2d^3!!4%ccnh1xylz^kwu3&q!ev77+kb_%b@@t'
DEBUG = True
ALLOWED_HOSTS = []
AUTH_PASSWORD_VALIDATORS = []

INSTALLED_APPS = [
    'tests.testapp',
    'boogie',
    'rest_framework',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
]
MIDDLEWARE = []
ROOT_URLCONF = 'tests.testproject.urls'
WSGI_APPLICATION = 'tests.testproject.wsgi.application'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.basename(BASE_DIR), 'db.sqlite3'),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = False
USE_TZ = False
STATIC_URL = '/static/'
