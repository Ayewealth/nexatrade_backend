web: python manage.py deploy && daphne -b 0.0.0.0 -p $PORT nexatrade_backend.asgi:application
worker: celery -A nexatrade_backend worker --loglevel=info
beat: celery -A nexatrade_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
