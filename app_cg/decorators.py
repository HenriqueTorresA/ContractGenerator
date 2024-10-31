from django.shortcuts import redirect

def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')  # Redireciona para a página de login se não estiver logado
        return view_func(request, *args, **kwargs)
    return wrapper
