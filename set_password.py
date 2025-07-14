import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrm.settings')
django.setup()

from django.contrib.auth.models import User

# Set password for user 'qwe'
user = User.objects.get(username='qwe')
user.set_password('qwe')
user.save()

print("Password set successfully for user 'qwe'") 