web:python manage.py runserver
web: gunicorn app.wsgi --log-file -
heroku ps:scale web=1
