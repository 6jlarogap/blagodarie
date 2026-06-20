import getpass
import os

from .settings import *  # noqa

SECRET_KEY = 'local-test-secret'

TEST_DB_USER = os.environ.get('BLAGODARIE_TEST_DB_USER') or \
    os.environ.get('PGUSER') or getpass.getuser()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('BLAGODARIE_TEST_DB_NAME', 'blagodarie'),
        'USER': TEST_DB_USER,
        'PASSWORD': os.environ.get('BLAGODARIE_TEST_DB_PASSWORD', ''),
        'HOST': os.environ.get('BLAGODARIE_TEST_DB_HOST', ''),
        'PORT': os.environ.get('BLAGODARIE_TEST_DB_PORT', ''),
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}
