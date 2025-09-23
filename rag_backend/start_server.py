#!/usr/bin/env python
"""
Django RAG Backend Startup Script
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_backend.settings')
    django.setup()
    
    # Run migrations
    print("Running database migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create superuser if needed
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        print("Creating admin user...")
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    
    # Start the server
    print("Starting Django development server...")
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
