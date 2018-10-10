import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'ss68t83q^4xx2d^3!!4%ccnh1xylz^kwu3&q!ev77+kb_%b@@t'
DEBUG = True
ALLOWED_HOSTS = []
AUTH_PASSWORD_VALIDATORS = []

INSTALLED_APPS = [
    'tests.testapp',
    'boogie.apps.users',
    # 'boogie.apps.tasks',
    'boogie',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
]
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
ROOT_URLCONF = 'tests.testproject.urls'
WSGI_APPLICATION = 'tests.testproject.wsgi.application'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
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
