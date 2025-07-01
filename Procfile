web: daphne nexatrade_backend.asgi:application
worker: celery -A nexatrade_backend worker --loglevel=info
beat: celery -A nexatrade_backend beat --loglevel=info
