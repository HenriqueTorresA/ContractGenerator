import os
from django.core.management import call_command

print("Executando makemigrations...")
call_command('makemigrations')

print("Executando migrate...")
os.system("python3 manage.py migrate")

print("Executando collectstatic...")
os.system("python3 manage.py collectstatic --noinput")
