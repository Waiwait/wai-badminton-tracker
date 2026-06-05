#!/bin/sh

echo "🚀 Starting Wai Badminton Tracker..."

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser from .env if it doesn"t exist
echo "Checking/Creating superuser..."

python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin123")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser created: {username} / {password}")
else:
    print(f"✅ Superuser "{username}" already exists")
EOF

echo "✅ Starting Gunicorn..."
exec gunicorn wai_badminton_tracker.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --log-level info