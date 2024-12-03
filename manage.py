#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'B2B_Backend.settings')
    try:
        from django.core.management import execute_from_command_line

        if 'runserver' in sys.argv:
            import django
            django.setup()
            from django.conf import settings

            if settings.DEBUG:  # Check the DEBUG setting from Django
                print("DEBUG is enabled. Running auto-migrations...")
                execute_from_command_line(['manage.py', 'makemigrations', '--noinput'])
                execute_from_command_line(['manage.py', 'migrate', '--noinput'])
                create_default_admin()

    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


def create_default_admin():
    """Create a default superuser if it doesn't already exist."""
    from django.contrib.auth.models import User
    from django.conf import settings

    # Read admin credentials from environment variables (with fallback defaults)
    admin_username = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('DJANGO_ADMIN_PASSWORD', 'admin')

    if not User.objects.filter(username=admin_username).exists():
        print(f"Creating default admin user: {admin_username}")
        User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
    else:
        print(f"Default admin user '{admin_username}' already exists.")


if __name__ == '__main__':
    main()
