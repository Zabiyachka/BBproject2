import os
import sys

# путь к папке проекта (где manage.py)
# ⚠️ ЗАМЕНИ YOUR_USERNAME на твой реальный логин в cPanel
path = '/home/basketag/bbproject2'

if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bb_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()