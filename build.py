import os

print("Executando migrate...")
os.system("python3 manage.py migrate app_cg --fake")

print("Executando collectstatic...")
os.system("python3 manage.py collectstatic --noinput")
