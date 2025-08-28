from django.shortcuts import redirect
from functools import wraps
from app_cg.models import Usuarios


def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')  # Redireciona para a página de login se não estiver logado
        return view_func(request, *args, **kwargs)
    return wrapper

def verifica_sessao_usuario(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')

        if user_id is None:
            return redirect('erro_sessao')  # Ou a view direta: redirect(erro_sessao)

        try:
            usuario = Usuarios.objects.get(codusuario=user_id)
        except Usuarios.DoesNotExist:
            return redirect('erro_sessao')

        # Armazena o usuário no request para uso dentro da view
        request.usuario_logado = usuario

        return view_func(request, *args, **kwargs)
    return wrapper
