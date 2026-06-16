#! ../ENV/bin/python3
"""Django's command-line utility for administrative tasks."""
import os
import sys

activate_this = os.path.join(os.path.dirname(__file__), '..', 'ENV', 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    print("Activating %s" % activate_this)
    exec(open(activate_this).read(), dict(__file__=activate_this))

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
