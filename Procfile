web: python manage.py collectstatic --noinput && python manage.py migrate && gunicorn sri_service.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 60
