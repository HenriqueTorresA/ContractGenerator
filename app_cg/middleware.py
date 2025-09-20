# Interceptar exceções no banco de dados

from django.db import OperationalError
from psycopg2 import OperationalError as Psycopg2OperationalError
from django.shortcuts import render

class DatabaseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except (OperationalError, Psycopg2OperationalError):
            # Mostra uma página customizada
            # messages.error(request, "Não foi possível conectar ao banco de dados. Verifique sua conexão com a internet.")
            # return redirect('home')  
            return render(request, "cg/erros/sem_conexao.html", status=503)
