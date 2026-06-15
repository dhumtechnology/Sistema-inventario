#!/bin/sh

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_data

exec python manage.py runserver 0.0.0.0:8000
