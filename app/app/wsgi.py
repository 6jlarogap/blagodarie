"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys

activate_this = os.path.join(os.path.dirname(__file__), '..', '..', 'ENV', 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    exec(compile(open(activate_this).read(), activate_this, 'exec'), dict(__file__=activate_this))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

application = get_wsgi_application()
