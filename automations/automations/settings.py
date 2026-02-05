from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-automations-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'dashboard',
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

ROOT_URLCONF = 'automations.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'automations.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'turnover_data',
        'USER': 'powerbi',
        'PASSWORD': 'your_secure_password',
        'HOST': '167.88.43.168',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'

GOOGLE_DRIVE_FOLDER_ID = '1xPGTc8320el4HXmZ3tNsHcavGtZ4asIY'
GOOGLE_CLIENT_SECRET_FILE = str(BASE_DIR.parent / 'Turn over GABE tuesday update' / 'client_secret_929057555993-c86mkjhf08suobk6olcca6sgmudeg8l0.apps.googleusercontent.com.json')
GOOGLE_TOKEN_FILE = str(BASE_DIR / 'token.json')

# OneDrive settings
ONEDRIVE_CLIENT_ID = '43fbe5a9-6b5b-4c81-9067-7aff9ac3ed5a'
ONEDRIVE_TENANT_ID = 'b1504b1d-d096-409a-a0f0-6cc546dde993'
ONEDRIVE_CLIENT_SECRET = 'w6B8Q~W3ac9klXa8NkMDo4cPNyOsjEryVL5TwdhQ'
ONEDRIVE_REDIRECT_URI = 'http://localhost:8000/onedrive/callback'
ONEDRIVE_SCOPES = ['Files.Read.All', 'Files.ReadWrite.All']
ONEDRIVE_FOLDER_PATH = '/Automation Platform/Turn Over Automation Report'
ONEDRIVE_TOKEN_FILE = str(BASE_DIR / 'onedrive_token.json')
LAST_SYNC_FILE = str(BASE_DIR / 'last_sync.json')
