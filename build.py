import os

os.system("python3 manage.py migrate")
os.system("python3 manage.py collectstatic --noinput")
