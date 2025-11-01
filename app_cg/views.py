import ast
import os
import unicodedata
import boto3
import random
import requests
import pyotp
import io
import qrcode
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from datetime import datetime, date as dt
from .models import Empresas, Usuarios, Clientes, Contrato, Tipositensadicionais, Itensadicionais, Codtipoitens_itensadicionais, Visualizar_contratos
from .classes.Template import Template
from .classes.Variavel import Variavel
from .classes.ContratosC import ContratosC
from .classes.Empresa import Empresa
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.contrib import messages
from .decorators import login_required_custom, verifica_sessao_usuario
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404


#### caso haja alguma adição de módulos, é necessário rodar o seguinte comando:
#### pip freeze > requirements.txt
#### localmente, pois se não a Vercel terá problemas para instalar as dependências do projeto

# ORIENTAÇÕES PARA RODAR O CÓDIGO
# python manage.py runserver

#Caso dê um erro na hora de rodar, dizendo:
#### ""ModuleNotFoundError: No module named 'django'"
#### ImportError: Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?
# Então é necessário ativar o ambiente virtual. Basta rodar o seguinte comando:
#### .\venv\Scripts\activate

############## ORIENTAÇÕES PARA PULL NA VPS ##############
    # git fetch origin
    # git reset --hard origin/master
    # cp .env /home/alexandre/ContractGenerator/

############## ORIENTAÇÕES PARA CONFIGURAÇÃO NA VPS ##############
    # git clone https://github.com/HenriqueTorresA/ContractGenerator.git
    # entrar na pasta ContractGenerator/
    # python3 -m venv .venv
    # source .venv/bin/activate
    # pip install gunicorn
    # pip install -r requirements.txt
    # configurar o arquivo .env na pasta /home/alexandre/ContractGenerator/
    # sudo systemctl restart docflow.service #---> Substitui o runserver
    # sudo systemctl status  docflow.service #---> Permite o status do server no guncorn
        ## caso seja necessário criação do .env, criar com o seguinte comando: "nano .env"
        ## Caso seja necessário desativar o ambiente virtual, basta rodar o comando: "deactivate"
        ## Caso seja necessário visualizar arquivos ocultos, utilizar comando: "ls -lha" ou "ls -la"

############## ORIENTAÇÕES PARA ERRO DE TIMEOUT EM WORKER NA VPS ##############
        ### [CRITICAL] WORKER TIMEOUT (pid:59587)
        ### [ERROR] Worker (pid:59587) was sent SIGKILL! Perhaps out of memory?
    # sudo lsof -i :8000
    # sudo kill -9 59585
        ### Comandos para ver logs de erro do Django na VPS. Um para ver os logs, e outro para ver em tempo real
    # sudo journalctl -u docflow.service -n 50 --no-pager
    # sudo journalctl -u docflow.service -f

#from contract_generator.contract_generator import settings
from django.conf import settings

s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

def inicio(request):
    return render(request, 'cg/inicio.html')

def contato(request):
    if request.method == "POST":
        nome = request.POST.get('nome')
        mensagem = request.POST.get('mensagem')

        # Aqui mando para o WhatsApp
        whatsapp_number = "5562998359213" #Alterar o número, coloquei o meu para teste
        url = f"https://wa.me/{whatsapp_number}?text=Nome:%20{nome}%0AMensagem:%20{mensagem}"
        return redirect(url)

    return render(request, 'cg/inicio.html')

def login(request):
    # Obter logo da aplicação
    context = {
        'logo_url': f'{settings.URL_IMAGENS_AWS}/logo_fundo_transparente-160x160-cortado.png'
    }
    # Retorna a página de login
    if request.method == "GET":
        return render(request, 'cg/login.html', context)

    login_input = request.POST.get('cpf')
    senha = request.POST.get('senha')

    try:
        usuario = Usuarios.objects.get(login=login_input)
    except Usuarios.DoesNotExist:
        messages.error(request, 'Usuário não encontrado!')
        return render(request, 'cg/login.html', context)

    if check_password(senha, usuario.senha):
        # Verifica se utiliza ou não 2FA
        if usuario.utiliza_dois_fatores:
            # Guarda o usuário temporariamente na sessão
            request.session['temp_user_id'] = usuario.codusuario
            if usuario.dois_fatores: # Se 2FA já ativo → vai para tela de verificação
                return redirect('verificar_otp')
            else: # Se ainda não configurou → vai para tela de ativação QR
                return redirect('habilitar_2fa')
        else:
            request.session['user_id'] = usuario.codusuario
            return redirect('home')
    else:
        messages.error(request, 'Senha incorreta!')
        return render(request, 'cg/login.html', context)
    
import base64

def habilitar_2fa(request):
    # Busca o usuário temporário da sessão
    usuario_id = request.session.get("temp_user_id")
    if not usuario_id:
        return redirect('login')

    usuario = Usuarios.objects.get(codusuario=usuario_id)

    # Gera segredo se não existir
    secret = usuario.gerar_otp_secret()

    # Cria URI compatível com Google/Microsoft Authenticator
    totp = pyotp.TOTP(secret)
    otp_uri = totp.provisioning_uri(name=usuario.email, issuer_name="DocFlow")

    # Gera QR Code em memória
    qr = qrcode.make(otp_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    # Converte a imagem para Base64 para exibir no template
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Se for POST, valida o código inserido
    if request.method == "POST":
        codigo = request.POST.get("codigo")
        if totp.verify(codigo):
            usuario.dois_fatores = True
            usuario.save()
            # Login completo
            request.session['user_id'] = usuario.codusuario
            del request.session['temp_user_id']
            messages.success(request, "2FA ativado com sucesso!")
            return redirect('home')
        else:
            messages.error(request, "Código inválido. Tente novamente.")

    # print(f'-----\nDEBUG: OTP URI para {usuario.email}: {otp_uri}\n-----')
    return render(request, "cg/habilitar_2fa.html", {"qr_code": img_base64, "otp_uri": otp_uri})
        
def confirmar_2fa(request):
    temp_user_id = request.session.get('temp_user_id')
    if not temp_user_id:
        return redirect('login')

    user = Usuarios.objects.get(codusuario=temp_user_id)

    if request.method == "POST":
        codigo = request.POST.get("codigo")
        totp = pyotp.TOTP(user.otp_secret)

        if totp.verify(codigo):
            user.dois_fatores = True
            user.save()
            # Autentica o usuário de vez
            request.session['user_id'] = user.codusuario
            del request.session['temp_user_id']
            messages.success(request, "2FA ativado com sucesso!")
            return redirect('home')
        else:
            messages.error(request, "Código inválido. Tente novamente.")

    return render(request, "cg/confirmar_2fa.html")

def verificar_otp(request):
    temp_user_id = request.session.get('temp_user_id')
    if not temp_user_id:
        return redirect('login')

    user = Usuarios.objects.get(codusuario=temp_user_id)

    if request.method == "POST":
        codigo = request.POST.get("codigo")
        totp = pyotp.TOTP(user.otp_secret)

        if totp.verify(codigo):
            # Login completo
            request.session['user_id'] = user.codusuario
            del request.session['temp_user_id']
            return redirect('home')
        else:
            messages.error(request, "Código inválido. Tente novamente.")

    return render(request, "cg/verificar_otp.html")

def erro_sessao(request):
    return render(request, 'cg/erros/erro_sessao.html')

@login_required_custom
def home(request):
    # Pega o usuário logado da sessão
    usuario = Usuarios.objects.get(codusuario=request.session['user_id'])
    img_url = f'{settings.URL_IMAGENS_AWS}/logo_fundo_branco-160x160-Sem_Titulo.jpg'

    # Lógica para criar itens adicionais, se não existirem no banco
    additional_items = {'Religioso', 'Hall de Entrada', 'Mesa de Bolo', 'Cortesia', 'Forracao', 'Mesa dos Pais', 'Centro de Mesa', 'Outros Itens'}
    items_types = Tipositensadicionais.objects.all()  # Obtém todos os tipos de itens adicionais do banco
    items_types_list = [item.nome for item in items_types]  # Cria uma lista de nomes de itens existentes

    for item in additional_items:  # Itera sobre os itens adicionais padrão
        if item not in items_types_list:  # Se o item não estiver no banco, adiciona
            contract_type = 'E' if item == 'Outros Itens' else 'D'  # Define o tipo de contrato
            new_item = Tipositensadicionais(nome=item, tipocontrato=contract_type)
            new_item.save()  # Salva o novo item no banco
            print(f'-----\nDEBUG: Item adicional "{item}" adicionado no banco de dados com sucesso!\n-----')

    # Lógica para criar uma empresa no banco, se não existir
    if not Empresas.objects.exists(): #ajustar
        name = 'Star Dokmus'
        reason = '32.846.467 Rosania Flores De Andrade Gama'
        cnpj = '32.846.467/0001-43'
        new_enterprise = Empresas(nome=name, razaosocial=reason, cnpj=cnpj)
        new_enterprise.save()  # Salva a nova empresa no banco
        print(f'-----\nDEBUG: Empresa "{name}" adicionada no banco de dados com sucesso!\n-----')

    # Renderiza o template home com o usuário logado
    return render(request, 'cg/home.html', {'usuario': usuario, 'img_url': img_url})

# Classe para lidar com o Service Worker
class ServiceWorkerView(View):
    def get(self, request, *args, **kwargs):
        service_worker_path = os.path.join(settings.BASE_DIR, 'static/js', 'service-worker.js')
        try:
            with open(service_worker_path, 'r') as service_worker_file:
                return HttpResponse(service_worker_file.read(), content_type='application/javascript')
        except FileNotFoundError:
            return HttpResponse(status=404)

@login_required_custom
@verifica_sessao_usuario
def lista_usuarios(request):
    usuario_logado = request.usuario_logado
    if usuario_logado.permissoes == 'colaborador':
        messages.error(request, "Você não possui permissão para acessar este módulo.")
        return redirect('home')

    operacao = request.POST.get('operacao')
    codempresa = request.POST.get('codempresa')
    if operacao == "1":
        codigo_empresa = codempresa
        usuarios = Usuarios.objects.filter(codempresa=codigo_empresa)
        messages.info(request, f'Exibindo usuários da empresa {codempresa}')
    else:
        codigo_empresa = usuario_logado.codempresa.codempresa
        usuarios = Usuarios.objects.filter(codempresa=codigo_empresa)  # Busca todos os usuários do banco de dados
    # for u in usuarios: print(f'\n---DEBUG---\nNome: {u.nome}\nUtiliza 2FA: {u.utiliza_dois_fatores}')
    context = {
        'usuarios':usuarios,
        'usuario':usuario_logado,
        # Somente usuários que já são administradores pode visualizar outros usuários administradores
        'podemostraradmin': 1 if usuario_logado.permissoes == 'admin' else 0,
        'codempresa': codigo_empresa
    }
    return render(request, 'cg/usuarios.html', context)

# View para excluir o usuário
@login_required_custom
def excluir_usuario(request):
    if request.method == "POST":
        codigo_usuario = request.POST.get('deletar-codusuario') # Coleta código do usuário
        usuario = get_object_or_404(Usuarios, codusuario=codigo_usuario) # Obtém objeto usuário do banco
        aux = str(usuario.nome) # Obtém o nome do usuário
        usuario.delete() # Exclui o usuário do banco
        messages.success(request, f'Usuário "{aux}" excluído com sucesso!')
        return redirect('lista_usuarios')
    else:
        messages.error(request, "Requisição inválida para exclusão de usuário.")
    return render(request, 'cg/lista_usuarios.html')
    # return render(request, 'cg/excluir_usuario.html', {'usuario': usuario})

@verifica_sessao_usuario
def cadastro(request):
    if request.method == "GET":
        return render(request, 'cg/usuarios.html')
    else:
        usuario_logado = request.usuario_logado
        if usuario_logado.permissoes == 'colaborador':
            messages.error(request, "Você não possui permissão para acessar este módulo.")
            return redirect('home')
        elif usuario_logado.permissoes == 'admin':
            codempresa = request.POST.get('codempresa')
        elif usuario_logado.permissoes == 'gestor':
            codempresa = usuario_logado.codempresa.codempresa

        # Coletar os itens do formulário
        operacao = request.POST.get('operacao') # Define se é cadastro (0) ou edição (1)
        nome = str(request.POST.get('nome')).strip() # nome do usuário
        login = str(request.POST.get('cpf')).strip() # CPF/Login do usuário
        email = str(request.POST.get('email')).strip() # E-mail do usuário
        permissoes = request.POST.get('permissao') # Tipo de permissão do usuário
        utiliza2fa = True if request.POST.get('check2fa') == 'on' else False # Utiliza ou não 2FA

        if operacao == "0": # Cadastrar novo usuário
            senha = request.POST.get('senha')

            # Verifica se o usuário já existe no seu modelo personalizado
            if Usuarios.objects.filter(login=login).exists():
                # Redireciona para a página de cadastro com uma mensagem de erro
                messages.error(request, 'Já existe um usuário com esse CPF cadastrado')
                return redirect('lista_usuarios')
            
            # Criação do usuário no banco de dados
            usuario = Usuarios.objects.create(
                nome=nome,
                login=login,
                email=email,
                senha=make_password(senha),  # Armazena a senha como um hash
                permissoes=permissoes.lower(),
                utiliza_dois_fatores=utiliza2fa,
                codempresa_id=codempresa  # Define codempresa como 1
            )
            usuario.save()
            messages.success(request, f'Usuário "{usuario.nome}" cadastrado com sucesso!')
            return redirect('lista_usuarios')  # Redireciona para a página de cadastro
        
        elif operacao == "1": # Editar usuário existente 
            codusuario_template = request.POST.get('codusuario')
            usuario = get_object_or_404(Usuarios, codusuario=codusuario_template) # Encontra o usuário no banco
            # Usuários que não são admin não podem editar usuários de outras empresas
            if usuario_logado.codempresa.codempresa != usuario.codempresa.codempresa and usuario_logado.permissoes != 'admin':
                messages.error(request, "Você não possui permissão para editar este usuário.")
                return redirect('lista_usuarios')
            
            # Só atualiza a senha do usuário se ela tiver sido alterada em tela
            nova_senha = request.POST.get('senha')
            if nova_senha:
                # Se o usuário fornecer uma nova senha, ela é criptografada
                usuario.senha = make_password(nova_senha)
            if permissoes=='Gestor' or permissoes=='colaborador' or permissoes=='admin':
                permissoes = permissoes.lower()
                usuario.permissoes = permissoes # Atualiza a permissão do usuário
            # Atualizar os demais dados do usuário
            usuario.nome = nome
            # usuario.login = login # O login/CPF não pode ser alterado
            usuario.email = email
            usuario.utiliza_dois_fatores = utiliza2fa
            usuario.save() # Salver as atualizações no banco de dados
            messages.success(request, f'Usuário "{usuario.nome}" atualizado com sucesso!')
            return redirect('lista_usuarios')
        messages.error(request, 'Operação inválida.')
        return redirect('lista_usuarios')
def logout(request):
    # Remove a sessão do usuário e redireciona para a página de login
    request.session.flush()  # Limpa todos os dados da sessão
    return redirect('login')

@verifica_sessao_usuario
@login_required_custom
def empresas(request):
    usuario = request.usuario_logado
    e = Empresa() # Inicia instância da empresa
    if usuario.permissoes == "admin": # Restrição de acesso
        context = {
            'usuario': usuario,
            'lista_empresas': e.obterTodasEmpresas() # Obtém empresas do BD
        }
        return render(request, 'cg/administracao/empresas.html', context)
    # Caso o usuário não tenha permissão necessária:
    messages.error(request, "Você não possui permissão para acessar este módulo")
    return redirect('home')

@verifica_sessao_usuario
@login_required_custom
def cadastrar_empresa(request):
    usuario = request.usuario_logado
    # Obter informações do formulário
    operacao = request.POST.get('operacao')
    codempresa = request.POST.get('codempresa')
    nome = request.POST.get('nome')
    razaosocial = request.POST.get('razaosocial')
    cnpj = request.POST.get('cnpj')

    if usuario.permissoes == "admin": # Acesso restrito
        if operacao == "0": # Cadastro
            e = Empresa(nome=nome,razaosocial=razaosocial, cnpj=cnpj) # Instancia a empresa
            e.salvarEmpresa() # Salva o objeto no banco de dados
            messages.success(request, 'Empresa cadastrada com sucesso!')
            return redirect('empresas')
        else: # Edição
            e = Empresa(codempresa=codempresa, nome=nome, razaosocial=razaosocial, cnpj=cnpj)
            e.atualizarEmpresa() # Atualiza o objeto no banco de dados
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('empresas')
    messages.error('Você não possui permissão para realizar essa ação.')
    return redirect('home')

@verifica_sessao_usuario
@login_required_custom
def excluir_empresa(request):
    usuario = request.usuario_logado
    codempresa = request.POST.get('deletar-empresa')

    if usuario.permissoes == "admin": # Acesso restrito
        e = Empresa(codempresa=codempresa) # Instancia a empresa
        resultado = e.excluirEmpresa() # Exclui o objeto no banco de dados
        if resultado == False:
            messages.error(request, f'Não foi possível excluir esta empresa. Existem Templates ou Contratos vinculados a ela.')
            return redirect('empresas')
        messages.success(request, f'Empresa excluída com sucesso!')
        return redirect('empresas')

    messages.error('Você não possui permissão para realizar essa ação.')
    return redirect('home')

# ACESSAR TELA DE NEGOCIAÇÃO DO CONTRATO
@login_required_custom
def trading_screen(request):
    return render(request, 'cg/new_contract/negociacao.html')

# ACESSAR TELA DE NEGOCIAÇÃO DO CONTRATO DE DECORAÇÃO
@login_required_custom
def trading_screen_decoration(request):
    return render(request, 'cg/new_contract_decoration/negociacao.html')

# CARREGAR AS INFORMAÇÕES DA NEGOCIAÇÃO DO CONTRATO E LEVA-OS PARA A VIEW summary_contract()
@login_required_custom
def trading_data(request):
    codcontrato_old = request.POST.get('codcontrato_old')
    operacao = request.POST.get('operacao')
    name = request.POST.get('name') ## Ele tenta pegar o atributo name do input do HTML
    address = request.POST.get('address')
    cpf = request.POST.get('cpf')
    phone = request.POST.get('phone')
    have10tables = request.POST.get('have-10-tables')
    have10tables = False if have10tables == None else True # Se não der certo como boolean, posso tentar como "sim" e "não"
    checkSeparateTables = request.POST.get('check-separate-tables')
    checkSeparateTables = False if checkSeparateTables == None else True
    squareTables = request.POST.get('square-tables')
    if checkSeparateTables == False and squareTables == None: squareTables = 0
    roundTables = request.POST.get('round-tables')
    if checkSeparateTables == False and roundTables == None: roundTables = 0
    checkSeparateChairs = request.POST.get('check-separate-chairs')
    checkSeparateChairs = False if checkSeparateChairs == None else True
    amountChairs = request.POST.get('amount-chairs')
    if checkSeparateChairs == False or amountChairs == None: amountChairs = 0
    checkSeparateTowels = request.POST.get('check-separate-towels')
    checkSeparateTowels = False if checkSeparateTowels == None else True
    amountTowels = request.POST.get('amount-towels')
    if checkSeparateTowels == False or amountTowels == None: amountTowels = 0 
    #otherItems = request.POST.get('other-items')
    otherItems = {}
    date = request.POST.get('date') # Resultado de exemplo: 2024-08-17
    entryTime = request.POST.get('entry-time') # Resultado de exemplo: 18:51
    departureTime = request.POST.get('departure-time') # Resultado de exemplo: 18:51
    eventType = request.POST.get('event-type')
    numberOfPeople = request.POST.get('number-of-people')
    eventValue = request.POST.get('event-value')
    antecipatedValue = request.POST.get('antecipated-value')

    if request.POST:
        for key in request.POST:
             #Verifica se a chave começa com 'other-items'
            if key.startswith('other-items'):
                otherItems[key] = request.POST.get(key)

    otherItemsList = []
    for value in otherItems.values():
        if value is not None and value != '':
            otherItemsList.append(f'{value}')

    return redirect(f'/generate-pdf/?codcontrato_old={codcontrato_old}&operacao={operacao}&name={name}&address={address}&cpf={cpf}&phone={phone}&have10tables={have10tables}&checkSeparateTables={checkSeparateTables}&squareTables={squareTables}&roundTables={roundTables}&checkSeparateChairs={checkSeparateChairs}&amountChairs={amountChairs}&checkSeparateTowels={checkSeparateTowels}&amountTowels={amountTowels}&otherItems={otherItems}&otherItemsList={otherItemsList}&date={date}&entryTime={entryTime}&departureTime={departureTime}&eventType={eventType}&numberOfPeople={numberOfPeople}&eventValue={eventValue}&antecipatedValue={antecipatedValue}')

# CARREGAR AS INFORMAÇÕES DA NEGOCIAÇÃO DO CONTRATO DE DECORAÇÃO E LEVA-OS PARA A VIEW summary_contract_decoration()
@login_required_custom
def trading_data_decoration(request):
    codcontrato_old = request.POST.get('codcontrato_old')
    operacao = request.POST.get('operacao')
    name = request.POST.get('name') ## Ele tenta pegar o atributo name do input do HTML
    address = request.POST.get('address')
    eventAddress = request.POST.get('event-address')
    cpf = request.POST.get('cpf')
    phone = request.POST.get('phone')

    religious = {}
    entraceHall = {}
    cakeTable = {}
    courtesy = {}
    lining = {}
    parentsTable = {}
    centerpiece = {}

    date = request.POST.get('date') # Resultado de exemplo: 2024-08-17
    eventTime = request.POST.get('event-time') # Resultado de exemplo: 18:51
    eventValue = request.POST.get('event-value')
    antecipatedValue = request.POST.get('antecipated-value')
    displacementValue = request.POST.get('displacement-value')
# ------------
    if request.POST:
        for key in request.POST:
             #Verifica se a chave começa com 'religious'
            if key.startswith('religious'):
                religious[key] = request.POST.get(key)

    religiousList = []
    for value in religious.values():
        if value is not None and value != '':
            religiousList.append(f'{value}')
# ------------
    if request.POST:
        for key in request.POST:
             #Verifica se a chave começa com 'entrace-hall'
            if key.startswith('entrace-hall'):
                entraceHall[key] = request.POST.get(key)

    entraceHallList = []
    for value in entraceHall.values():
        if value is not None and value != '':
            entraceHallList.append(f'{value}')
# ------------
    if request.POST:
        for key in request.POST:
             #Verifica se a chave começa com 'cake-table'
            if key.startswith('cake-table'):
                cakeTable[key] = request.POST.get(key)

    cakeTableList = []
    for value in cakeTable.values():
        if value is not None and value != '':
            cakeTableList.append(f'{value}')
# ------------
    if request.POST:
        for key in request.POST:
             #Verifica se a chave começa com 'courtesy'
            if key.startswith('courtesy'):
                courtesy[key] = request.POST.get(key)

    courtesyList = []
    for value in courtesy.values():
        if value is not None and value != '':
            courtesyList.append(f'{value}')
# ------------
# ------------
    if request.POST:
        for key in request.POST:
             #Verifica se a chave começa com 'Lining'
            if key.startswith('Lining'):
                lining[key] = request.POST.get(key)

    liningList = []
    for value in lining.values():
        if value is not None and value != '':
            liningList.append(f'{value}')
# ------------
    if request.POST:
        for key in request.POST:
             #Verifica se a chave começa com 'ParentsTable'
            if key.startswith('ParentsTable'):
                parentsTable[key] = request.POST.get(key)

    parentsTableList = []
    for value in parentsTable.values():
        if value is not None and value != '':
            parentsTableList.append(f'{value}')
# ------------
    if request.POST:
        for key in request.POST:
             #Verifica se a chave começa com 'Centerpiece'
            if key.startswith('Centerpiece'):
                centerpiece[key] = request.POST.get(key)

    centerpieceList = []
    for value in centerpiece.values():
        if value is not None and value != '':
            centerpieceList.append(f'{value}')
# ------------
    return redirect(f'/generate-pdf-decoration/?codcontrato_old={codcontrato_old}&operacao={operacao}&name={name}&address={address}&eventAddress={eventAddress}&cpf={cpf}&phone={phone}&religiousList={religiousList}&entraceHallList={entraceHallList}&cakeTableList={cakeTableList}&courtesyList={courtesyList}&liningList={liningList}&parentsTableList={parentsTableList}&centerpieceList={centerpieceList}&date={date}&eventTime={eventTime}&eventValue={eventValue}&antecipatedValue={antecipatedValue}&displacementValue={displacementValue}')

# ABRE O RESUMO DO CONTRATO PASSANDO OS DADOS NO CONTEXTO
@login_required_custom
def summary_contract(request):
    name = request.GET.get('name', '')
    address = request.GET.get('address', '')
    cpf = request.GET.get('cpf')
    phone = request.GET.get('phone')
    have10tables = request.GET.get('have10tables')
    checkSeparateTables = request.GET.get('checkSeparateTables')
    squareTables = request.GET.get('squareTables')
    roundTables = request.GET.get('roundTables')
    checkSeparateChairs = request.GET.get('checkSeparateChairs')
    amountChairs = request.GET.get('amountChairs')
    checkSeparateTowels = request.GET.get('checkSeparateTowels')
    amountTowels = request.GET.get('amountTowels')
    otherItems = request.GET.get('otherItems')
    otherItemsList = request.GET.get('otherItemsList')
    otherItemsList = ast.literal_eval(otherItemsList)
    date = request.GET.get('date')
    entryTime = request.GET.get('entryTime')
    departureTime = request.GET.get('departureTime')
    eventType = request.GET.get('eventType')
    numberOfPeople = request.GET.get('numberOfPeople')
    eventValue = request.GET.get('eventValue')
    antecipatedValue = request.GET.get('antecipatedValue')

    context = {'name':name,
               'address':address,
               'cpf':cpf,
               'phone':phone,
               'have10tables':have10tables,
               'checkSeparateTables':checkSeparateTables,
               'squareTables':squareTables,
               'roundTables':roundTables,
               'checkSeparateChairs':checkSeparateChairs,
               'amountChairs':amountChairs,
               'checkSeparateTowels':checkSeparateTowels,
               'amountTowels':amountTowels,
               'otherItems':otherItems,
               'otherItemsList':otherItemsList,
               'date':date,
               'entryTime':entryTime,
               'departureTime':departureTime,
               'eventType':eventType,
               'numberOfPeople':numberOfPeople,
               'eventValue':eventValue,
               'antecipatedValue':antecipatedValue,
               }

    return render(request,'cg/new_contract/resumo.html',context)

# ABRE O RESUMO DO CONTRATO DE DECORAÇÃO PASSANDO OS DADOS NO CONTEXTO
@login_required_custom
def summary_contract_decoration(request):
    name = request.GET.get('name', '')
    address = request.GET.get('address', '')
    eventAddress = request.GET.get('eventAddress', '')
    cpf = request.GET.get('cpf')
    phone = request.GET.get('phone')

    religiousList = request.GET.get('religiousList')
    religiousList = ast.literal_eval(religiousList)

    entraceHallList = request.GET.get('entraceHallList')
    entraceHallList = ast.literal_eval(entraceHallList)

    cakeTableList = request.GET.get('cakeTableList')
    cakeTableList = ast.literal_eval(cakeTableList)

    courtesyList = request.GET.get('courtesyList')
    courtesyList = ast.literal_eval(courtesyList)

    liningList = request.GET.get('liningList')
    liningList = ast.literal_eval(liningList)

    parentsTableList = request.GET.get('parentsTableList')
    parentsTableList = ast.literal_eval(parentsTableList)

    centerpieceList = request.GET.get('centerpieceList')
    centerpieceList = ast.literal_eval(centerpieceList)

    date = request.GET.get('date')
    eventTime = request.GET.get('eventTime')
    eventValue = request.GET.get('eventValue')
    antecipatedValue = request.GET.get('antecipatedValue')
    displacementValue = request.GET.get('displacementValue')

    context = {'name':name,
               'address':address,
               'eventAddress':eventAddress,
               'cpf':cpf,
               'phone':phone,
               'religiousList':religiousList,
               'entraceHallList':entraceHallList,
               'cakeTableList':cakeTableList,
               'courtesyList':courtesyList,
               'liningList':liningList,
               'parentsTableList':parentsTableList,
               'centerpieceList':centerpieceList,
               'date':date,
               'eventTime':eventTime,
               'eventValue':eventValue,
               'antecipatedValue':antecipatedValue,
               'displacementValue':displacementValue,
               }

    return render(request,'cg/new_contract_decoration/resumo.html',context)

# CARREGA O TEMPLATE DO CONTRATO EM HTML, INSERE OS DADOS NO TEMPLATE E CRIA O ARQUIVO PDF
@login_required_custom
def generate_pdf(request):
    template_path = 'cg/new_contract/template_contrato.html' #template_contrato.html
    codcontrato_old = int(request.GET.get('codcontrato_old'))
    operacao = int(request.GET.get('operacao'))
    name = request.GET.get('name')
    address = request.GET.get('address')
    cpf = request.GET.get('cpf')
    phone = request.GET.get('phone')
    have10tables = request.GET.get('have10tables')
    checkSeparateTables = request.GET.get('checkSeparateTables')
    squareTables = request.GET.get('squareTables')
    roundTables = request.GET.get('roundTables')
    checkSeparateChairs = request.GET.get('checkSeparateChairs')
    amountChairs = request.GET.get('amountChairs')
    checkSeparateTowels = request.GET.get('checkSeparateTowels')
    amountTowels = request.GET.get('amountTowels')
    #otherItems = request.GET.get('otherItems')
    otherItemsList = request.GET.get('otherItemsList')
    otherItemsList = ast.literal_eval(otherItemsList)
    date = request.GET.get('date')
    day, month, year = transforma_data(date)
    entryTime = request.GET.get('entryTime')
    departureTime = request.GET.get('departureTime')
    eventType = request.GET.get('eventType')
    numberOfPeople = request.GET.get('numberOfPeople')
    eventValue = request.GET.get('eventValue')
    antecipatedValue = request.GET.get('antecipatedValue')
    currentDate = dt.today()
    currentDate = str(currentDate)
    creationDate = currentDate
    currentDay, currentMonth, currentYear = transforma_data(currentDate)
    fileName = ''.join(['_' if i == ' ' else i for i in name])

    if operacao == 1:
        contracts = Contrato.objects.all()
        # Coletar a data de criação do contrato a ser atualizado
        for c in contracts:
            if c.codcontrato == codcontrato_old:
                creationDate = c.dtcriacao

    # -----> Tratando os dados para gravar no banco de dados
    if name == '': name = None
    if address == '': address = None
    if phone == '': phone = None
    if cpf == '': cpf = None
    if date == '': date = None
    if entryTime== '': entryTime = None 
    if departureTime == '': departureTime = None
    if eventType == '': eventType = None
    if numberOfPeople == '': numberOfPeople = None
    if eventValue== '': eventValue = None
    if antecipatedValue == '': antecipatedValue = None

    # Caso a operação a ser realizada seja de cadastrar um novo contrato ou de editar, então salvar o contrato
    if operacao != 2:
        ## -----> Gravar os dados no banco de dados tabela de CLIENTES
        clients = Clientes.objects.all() # Recebe os clientes do banco de dados
        encontrouCliente = False

        for c in clients: # Percorrer a lista de clientes, e ver se o cliente deste contrato já existe
            if name == c.nome and cpf == c.cpf:
                print(f"-----\nDEBUG: O cliente atual é o {name}, e já existe na lista de clientes.")
                Client = c # Se existir, reutilizado
                encontrouCliente = True

        if encontrouCliente == False: # Caso o cliente não exista, então salvar ele no banco de dados, como um novo cliente
            Client = Clientes(nome=name, endereco=address, telefone=phone, cpf=cpf)
            Client.save() # Salvar um novo cliente
            print(f"-----\nDEBUG: Cliente {name} salvo com sucesso!")

        ## -----> Gravar os dados no banco de dados tabela de CONTRATOS
        mesasinclusas = 'S' if have10tables == 'True' else 'N'
        mesasqavulsas = squareTables if checkSeparateTables == 'True' and squareTables != '' else None
        mesasravulsas = roundTables if checkSeparateTables == 'True' and roundTables != '' else None
        cadeirasavulsas = amountChairs if checkSeparateChairs == 'True' and amountChairs != '' else None
        toalhasavulsas = amountTowels if checkSeparateTowels == 'True' and amountTowels != '' else None
        contrato = Contrato(codcliente=Client, tipocontrato='E',status='A',dtcriacao=creationDate,dtatualiz=currentDate,dtevento=date,
                                            horaentrada=entryTime,horasaida=departureTime,tipoevento=eventType,qtdconvidados=numberOfPeople,
                                            valortotal=eventValue,valorsinal=antecipatedValue,mesasinclusas=mesasinclusas,mesasqavulsas=mesasqavulsas,
                                            mesasravulsas=mesasravulsas,cadeirasavulsas=cadeirasavulsas,toalhasavulsas=toalhasavulsas)
        contrato.save()
        print(f'-----\nDEBUG: Contrato "{contrato.codcontrato}" adicionado no banco de dados com sucesso!\n-----')

        ## -----> Gravar os itens adicionais na tabela de itens adicionais no banco de dados
        itemType = Tipositensadicionais.objects.get(nome='Outros Itens')
        print(f'-----\nDEBUG: Código do tipo do item: {itemType.codtipoitem}')
        for c in otherItemsList:
            additionalItem = Itensadicionais(codcontrato=contrato,codtipoitem=itemType,nome=c,dtatualiz=currentDate)
            additionalItem.save()

    # Caso a operação a ser realizada seja apenas de editar um contrato existente, então excluir o antigo, pois o novo já está salvo
    if operacao == 1:
        contracts = Contrato.objects.all()
        additionalItems_old = Itensadicionais.objects.all()
        # Deletar os itens adicionais:
        for i in additionalItems_old:
            if i.codcontrato.codcontrato == codcontrato_old:
                i.delete()
                print(f'-----\nDEBUG: Itens do contrato: {codcontrato_old} deletados com sucesso!')
        # Deletar o contrato:
        for c in contracts:
            if c.codcontrato == codcontrato_old:
                c.delete()
                print(f'-----\nDEBUG: Contrato: {codcontrato_old} deletado com sucesso!')

    if name is None: name = '____________________________'
    if address is None: address = '___________________________________________'
    if cpf is None: cpf = '_______________'
    itemhave10tables = '10 jogos de mesas quadradas (fornecido pelo espaço);' if have10tables == 'True' else ''
    havesquaretables = f'{squareTables} mesas quadradas avulsas;' if checkSeparateTables == 'True' and squareTables != '' else ''
    haveroundtables = f'{roundTables} mesas redondas avulsas;' if checkSeparateTables == 'True' and roundTables != '' else ''
    haveamountchairs = f'{amountChairs} cadeiras avulsas;' if checkSeparateChairs == 'True' and amountChairs != '' else ''
    haveamounttowels = f'{amountTowels} toalhas avulsas;' if checkSeparateTowels == 'True' and amountTowels != '' else ''
    if otherItemsList is None: otherItemsList = ''
    if phone is None or phone == '': phone = '_____________________'
    if date is None: date = '__________________________'
    if day is None or day == '': day = '_____'
    if month is None or month == '': month = '__________________'
    if year is None or year == '': year = '_________'
    if entryTime is None: entryTime = '__________________________________'
    if departureTime is None: departureTime = '__________________________________'
    if eventType is None: eventType = '__________________________'
    if numberOfPeople is None: numberOfPeople = '__________'
    if eventValue is None: eventValue = '_____________'
    if antecipatedValue is None: antecipatedValue = '_____________'
    if currentDay is None or currentDay == '': currentDay = '_____'
    if currentMonth is None or currentMonth == '': currentMonth = '__________________'
    if currentYear is None or currentYear == '': currentYear = '_________'
    
    context = {'name':name,
               'address':address,
               'cpf':cpf,
               'phone':phone,
               'itemhave10tables':itemhave10tables,
               'havesquaretables':havesquaretables,
               'haveroundtables':haveroundtables,
               'haveamountchairs':haveamountchairs,
               'haveamounttowels':haveamounttowels,
               'squareTables':squareTables,
               'roundTables':roundTables,
               'amountChairs':amountChairs,
               'amountTowels':amountTowels,
               'otherItemsList':otherItemsList,
               'day':day,
               'month':month,
               'year':year,
               'entryTime':entryTime,
               'departureTime':departureTime,
               'eventType':eventType,
               'numberOfPeople':numberOfPeople,
               'eventValue':eventValue,
               'antecipatedValue':antecipatedValue,
               'currentDay':currentDay, 
               'currentMonth':currentMonth, 
               'currentYear':currentYear
               }
    
    # Renderizar o template em HTML
    html = render_to_string(template_path, context)
    
    # Criar um response como PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Contrato-Star-Dokmus-{fileName}.pdf"'
    
    # Criar o PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=400)
    
    return response

# CARREGA O TEMPLATE DO CONTRATO DE DECORAÇÃO EM HTML, INSERE OS DADOS NO TEMPLATE E CRIA O ARQUIVO PDF
@login_required_custom
def generate_pdf_decoration(request):
    template_path = 'cg/new_contract_decoration/template_contrato_decoracao.html'

    codcontrato_old = int(request.GET.get('codcontrato_old'))
    operacao = int(request.GET.get('operacao'))
    name = request.GET.get('name')
    address = request.GET.get('address')
    cpf = request.GET.get('cpf')
    phone = request.GET.get('phone')
    eventAddress = request.GET.get('eventAddress')

    religiousList = request.GET.get('religiousList')
    religiousList = ast.literal_eval(religiousList)

    entraceHallList = request.GET.get('entraceHallList')
    entraceHallList = ast.literal_eval(entraceHallList)

    cakeTableList = request.GET.get('cakeTableList')
    cakeTableList = ast.literal_eval(cakeTableList)

    courtesyList = request.GET.get('courtesyList')
    courtesyList = ast.literal_eval(courtesyList)

    liningList = request.GET.get('liningList')
    liningList = ast.literal_eval(liningList)

    parentsTableList = request.GET.get('parentsTableList')
    parentsTableList = ast.literal_eval(parentsTableList)

    centerpieceList = request.GET.get('centerpieceList')
    centerpieceList = ast.literal_eval(centerpieceList)

    date = request.GET.get('date')
    day, month, year = transforma_data(date)
    eventTime = request.GET.get('eventTime')
    eventValue = request.GET.get('eventValue')
    antecipatedValue = request.GET.get('antecipatedValue')
    displacementValue = request.GET.get('displacementValue')
    
    currentDate = dt.today()
    currentDate = str(currentDate)
    creationDate = currentDate
    currentDay, currentMonth, currentYear = transforma_data(currentDate)
    fileName = ''.join(['_' if i == ' ' else i for i in name])

    ## Definindo valores padrão para as variáveis antes de salvar no banco de dados
    if name == '': name = None
    if address == '': address = None
    if cpf == '': cpf = None
    if phone == '': phone = None
    if eventAddress == '': eventAddress = None
    if date == '': date = None
    if eventTime == '': eventTime = None
    if eventValue == '': eventValue = None
    if antecipatedValue == '': antecipatedValue = None
    if displacementValue == '': displacementValue = None

    if operacao == 1: #Somente edição de contrato
        contracts = Contrato.objects.all()
        # Coletar a data de criação do contrato a ser atualizado
        for c in contracts:
            if c.codcontrato == codcontrato_old:
                creationDate = c.dtcriacao

    if operacao != 2: #Edição de contrato ou criação de novo contrato
        ## Salvando ou criando cliente no banco de dados
        clients = Clientes.objects.all() # Recebe os clientes do banco de dados
        encontrouCliente = False

        for c in clients: # Percorrer a lista de clientes, e ver se o cliente deste contrato já existe
            if name == c.nome and cpf == c.cpf:
                print(f"-----\nDEBUG: O cliente atual é o {name}, e já existe na lista de clientes.")
                Client = c # Se existir, reutilizado
                encontrouCliente = True

        if encontrouCliente == False: # Caso o cliente não exista, então salvar ele no banco de dados, como um novo cliente
            Client = Clientes(nome=name, endereco=address, telefone=phone, cpf=cpf)
            Client.save() # Salvar um novo cliente
            print(f"-----\nDEBUG: Cliente {name} salvo com sucesso!")
        
        ## Salvando o contrato no banco de dados
        Contract = Contrato(codcliente=Client,tipocontrato='D',status='A',
                            dtcriacao=creationDate,dtatualiz=currentDate,dtevento=date,
                            enderecoevento=eventAddress,horaentrada=eventTime,
                            valortotal=eventValue,valorsinal=antecipatedValue,valordeslocamento=displacementValue)
        Contract.save()

        ## Salvando a lista do Religioso no banco de dados
        typeItemList = Tipositensadicionais.objects.get(nome='Religioso')
        for r in religiousList:
            item = Itensadicionais(codcontrato=Contract,codtipoitem=typeItemList,nome=r,dtatualiz=currentDate)
            item.save()

        ## Salvando a lista do hall de entrada no banco de dados
        typeItemList = Tipositensadicionais.objects.get(nome='Hall de Entrada')
        for e in entraceHallList:
            item = Itensadicionais(codcontrato=Contract,codtipoitem=typeItemList,nome=e,dtatualiz=currentDate)
            item.save()
        
        ## Salvando a lista de mesa de bolo no banco de dados
        typeItemList = Tipositensadicionais.objects.get(nome='Mesa de Bolo')
        for c in cakeTableList:
            item = Itensadicionais(codcontrato=Contract,codtipoitem=typeItemList,nome=c,dtatualiz=currentDate)
            item.save()

        ## Salvando a lista de cortesia no banco de dados 
        typeItemList = Tipositensadicionais.objects.get(nome='Cortesia')
        for c in courtesyList:
            item = Itensadicionais(codcontrato=Contract,codtipoitem=typeItemList,nome=c,dtatualiz=currentDate)
            item.save()

        ## Salvando a lista de forração no banco de dados 
        typeItemList = Tipositensadicionais.objects.get(nome='Forracao')
        for l in liningList:
            item = Itensadicionais(codcontrato=Contract,codtipoitem=typeItemList,nome=l,dtatualiz=currentDate)
            item.save()

        ## Salvando a lista de mesa dos pais no banco de dados 
        typeItemList = Tipositensadicionais.objects.get(nome='Mesa dos Pais')
        for p in parentsTableList:
            item = Itensadicionais(codcontrato=Contract,codtipoitem=typeItemList,nome=p,dtatualiz=currentDate)
            item.save()

        ## Salvando a lista de mesa dos pais no banco de dados 
        typeItemList = Tipositensadicionais.objects.get(nome='Centro de Mesa')
        for c in centerpieceList:
            item = Itensadicionais(codcontrato=Contract,codtipoitem=typeItemList,nome=c,dtatualiz=currentDate)
            item.save()

    # Caso a operação a ser realizada seja apenas de editar um contrato existente, então excluir o antigo, pois o novo já está salvo
    if operacao == 1:
        contracts = Contrato.objects.all()
        additionalItems_old = Itensadicionais.objects.all()
        # Deletar os itens adicionais:
        for i in additionalItems_old:
            if i.codcontrato.codcontrato == codcontrato_old:
                i.delete()
                print(f'-----\nDEBUG: Itens do contrato: {codcontrato_old} deletados com sucesso!')
        # Deletar o contrato:
        for c in contracts:
            if c.codcontrato == codcontrato_old:
                c.delete()
                print(f'-----\nDEBUG: Contrato: {codcontrato_old} deletado com sucesso!')
        print(f'-----\nDEBUG: Edição do contrato {codcontrato_old} realizada com sucesso!')

    ## Adicionar linhas nas variáveis caso não tenha valor, para apresentá-las no contrato
    if name is None: name = '__________________________'
    if address is None: address = '__________________________________'
    if eventAddress is None: eventAddress = '__________________________________'
    if cpf is None: cpf = '__________________'
    if phone is None: phone = '_____________________'

    if date is None or date == '': date = '__________________________'
    if day is None or day == '': day = '_____'
    if month is None or month == '': month = '__________________'
    if year is None or year == '': year = '_________'
    if eventTime is None or eventTime== '': eventTime = '_____________'
    if eventValue is None or eventValue== '': eventValue = '_____________'
    if antecipatedValue is None or antecipatedValue == '': antecipatedValue = '_____________'
    if displacementValue is None or displacementValue== '': displacementValue = '_____________'
    if currentDay is None or currentDay == '': currentDay = '_____'
    if currentMonth is None or currentMonth == '': currentMonth = '__________________'
    if currentYear is None or currentYear == '': currentYear = '_________'
    
    context = {'name':name,
               'address':address,
               'eventAddress':eventAddress,
               'cpf':cpf,
               'phone':phone,
               'religiousList':religiousList,
               'entraceHallList':entraceHallList,
               'cakeTableList':cakeTableList,
               'courtesyList':courtesyList,
               'liningList':liningList,
               'parentsTableList':parentsTableList,
               'centerpieceList':centerpieceList,
               'day':day,
               'month':month,
               'year':year,
               'eventTime':eventTime,
               'eventValue':eventValue,
               'antecipatedValue':antecipatedValue,
               'displacementValue':displacementValue,
               'currentDay':currentDay, 
               'currentMonth':currentMonth, 
               'currentYear':currentYear
               }
    
    # Renderizar o template em HTML
    html = render_to_string(template_path, context)
    
    # Criar um response como PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Contrato-Decoracao-StarDokmus-{fileName.strip()}.pdf"'
    
    # Criar o PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=400)
    
    return response

# CARREGA A TELA DE VISUALIZAÇÃO DE CONTRATOS
@login_required_custom
def preview_contract(request, operacao): # operacao --> 1=ContratosAtivos, 2=ContratosVencidos
    v_contracts = Visualizar_contratos.objects.all()
    currentDate = dt.today()
    operacao_texto = "Ativos"
    
    contractsvList = []
    listaContratoDecoracao = []
    listaContratoEspaco = []

    for c in v_contracts: contractsvList.append(c)
    if operacao == 1: #Define a visualização, mostrando apenas ativos, ou apenas vencidos
        contractsvList = [c for c in v_contracts if c.status != 'D' and c.dtevento != None and datetime.strptime(c.dtevento, "%Y-%m-%d").date() >= currentDate] # tratativa CRASH
    else:
        contractsvList = [c for c in v_contracts if c.status != 'D' and (c.dtevento == None or datetime.strptime(c.dtevento, "%Y-%m-%d").date() <= currentDate)] # CRASH
        contractsIds = [c.codcontrato for c in contractsvList]
        # Atualizar status para 'V' nos contrato que já estão vencidos 
        Contrato.objects.filter(codcontrato__in=contractsIds).exclude(status='V').update(status='V')
        operacao_texto = "Vencidos"
    
    # Separa contratos de decoração para contratos de Espaço
    for c in contractsvList:
        if c.dtevento: # Trata a visualização da data para o formato Brasileiro
            if isinstance(c.dtevento, str):
                c.dtevento = datetime.strptime(c.dtevento, "%Y-%m-%d").date()  # Supondo que o formato seja 'YYYY-MM-DD'
            c.dtevento = c.dtevento.strftime("%d-%m-%Y")
        if c.tipocontrato == 'D': # Tipo contrato de Decoração
            listaContratoDecoracao.append(c)
        else: # Tipo contrato de Espaço
            listaContratoEspaco.append(c)    

    context = {
        'listaContratoDecoracao': listaContratoDecoracao,
        'listaContratoEspaco': listaContratoEspaco,
        'operacao': operacao,
        'operacao_texto': operacao_texto
    }
    
    # print(f'-----\nDEBUG: Pesquisando os contratos existentes\n{contractsvList}\n{listaContratoEspaco}\n{listaContratoDecoracao}\n-----')
    # print(f'-----\nDEBUG: TiposItensAdicionais: {v_tiposItemsList}\n-----')
    return render(request, 'cg/contract_preview/lista_contratos.html', context)

# VISUALIZAR O CONTRATO SELECIONADO
@login_required_custom
def visualizar_contrato(request, codcontrato):
    # Obtém o contrato
    contrato = get_object_or_404(Contrato, codcontrato=codcontrato) 
    # Obtém os itens adicionais
    codigo = int(contrato.codcontrato)
    # Filtrar Itens Adicionais deste contrato
    additionalItems = Itensadicionais.objects.filter(codcontrato=codigo) 
    v_tiposItems = Codtipoitens_itensadicionais.objects.filter(codcontrato_id=codigo)
    operacao = 2 #operacao --> 1=ContratosAtivos, 2=ContratosVencidos
    
    additionalItemsList = []
    v_tiposItemsList = []
    
    # Transformar datas em formato visível ao usuário
    if contrato.dtevento:
        if isinstance(contrato.dtevento, str):
            contrato.dtevento = datetime.strptime(contrato.dtevento, "%Y-%m-%d").date()
        if contrato.dtevento >= dt.today(): # Se não entrar aqui, o contrato será Vencido
            operacao = 1 # Definir contrato como Ativo
        contrato.dtevento = contrato.dtevento.strftime("%d-%m-%Y")
    if contrato.dtatualiz:
        if isinstance(contrato.dtatualiz, str):
            contrato.dtatualiz = datetime.strptime(contrato.dtatualiz, "%Y-%m-%d").date()
        contrato.dtatualiz = contrato.dtatualiz.strftime("%d-%m-%Y")
    if contrato.dtcriacao:
        if isinstance(contrato.dtcriacao, str):
            contrato.dtcriacao = datetime.strptime(contrato.dtcriacao, "%Y-%m-%d").date()
        contrato.dtcriacao = contrato.dtcriacao.strftime("%d-%m-%Y")

    #Criar lista de objetos dos itens adicionais deste contrato
    for c in additionalItems: additionalItemsList.append(c)
    for c in v_tiposItems: v_tiposItemsList.append(c)
    
    context = {
        'contrato':contrato,
        'itensAdicionais':additionalItemsList,
        'tiposItensAdicionais':v_tiposItemsList,
        'operacao': operacao
    }
    
    print(f'-----\nDEBUG: Buscando Contrato\n-----')
    # print(f'-----\nDEBUG: TiposItensAdicionais: {v_tiposItemsList}\n-----')
    return render(request, 'cg/contract_preview/visualizar_contrato.html', context)

# DELETAR OS CONTRATOS
@login_required_custom
def deletar_contrato(request, codcontrato):
    contrato = get_object_or_404(Contrato, codcontrato=codcontrato)
    contratos = Contrato.objects.all()
    lista_contratos = [c for c in contratos]
    for c in lista_contratos:
        if c.codcontrato == contrato.codcontrato:
            contrato.status = 'D'
            contrato.save()
            print(f'-----\nDEBUG: Status do contrato "{contrato.codcontrato}", do cliente: "{c.codcliente.nome}" atualizado para D com sucesso! \n-----')
    return redirect(preview_contract)

# RENDENIZAR A TELA DE EDIÇÃO DE CONTRATO
@login_required_custom
def editar_contrato(request, codcontrato):
    allContracts = Contrato.objects.all()
    allClients = Clientes.objects.all()
    allAdittionalItems = Itensadicionais.objects.all()
    itensAdicionais = []

    for c in allContracts:
        if c.codcontrato == codcontrato:
            contrato = c
    for c in allClients:
        if contrato.codcliente.codcliente == c.codcliente:
            cliente = c
    for t in allAdittionalItems:
        if contrato.codcontrato == t.codcontrato.codcontrato:
            itensAdicionais.append(t)

    # Evitar que seja enviado o valor None para os campos no HTML
    if cliente.telefone is None: cliente.telefone = ''
    if cliente.endereco is None: cliente.endereco = ''
    if cliente.cpf is None: cliente.cpf = ''
    if contrato.enderecoevento is None: contrato.enderecoevento = ''
    if contrato.dtevento is None: contrato.dtevento = ''
    if contrato.mesasinclusas is None: contrato.mesasinclusas = ''
    if contrato.mesasqavulsas is None: contrato.mesasqavulsas = ''
    if contrato.mesasravulsas is None: contrato.mesasravulsas = ''
    if contrato.cadeirasavulsas is None: contrato.cadeirasavulsas = ''
    if contrato.toalhasavulsas is None: contrato.toalhasavulsas = ''
    if contrato.horaentrada is None: contrato.horaentrada = ''
    if contrato.horasaida is None: contrato.horasaida = ''
    if contrato.tipoevento is None: contrato.tipoevento = ''
    if contrato.qtdconvidados is None: contrato.qtdconvidados = ''
    if contrato.valortotal is None: contrato.valortotal = ''
    if contrato.valorsinal is None: contrato.valorsinal = ''
    if contrato.valordeslocamento is None: contrato.valordeslocamento = ''

    context = {
        'contrato': contrato,
        'cliente': cliente,
        'itensAdicionais': itensAdicionais
        }
    
    if contrato.tipocontrato == 'E':
        return render(request, 'cg/edit_contract/espaco.html', context)
    else:
        return render(request, 'cg/edit_contract/decoracao.html', context)

# COMPARTILHAR CONTRATO SELECIONADO (por enquanto carrega o arquivo novamente com o mesmo layout)
@login_required_custom
def compartilhar_contrato(request, codcontrato):
    Items = Itensadicionais.objects.all()
    ItemsList = []
    religiousList = []
    entraceHallList = []
    cakeTableList = []
    courtesyList = []
    liningList = []
    parentsTableList = []
    centerpieceList = []

    contract = Contrato.objects.get(codcontrato=codcontrato)
    print(f'-----\n'+ 
          f'DEBUG: Compartilhando contrato...: ' + 
          f'\n codcontrato: {contract.codcontrato}' + 
          f'\n cliente: {contract.codcliente.nome}' + 
          f'\n data do evento: {contract.dtevento}' + 
          f'\n-----')

    for i in Items:
        if i.codcontrato.codcontrato == int(codcontrato):
            if i.codtipoitem.codtipoitem == 1:
                ItemsList.append(i.nome)
            if i.codtipoitem.codtipoitem == 6:
                religiousList.append(i.nome)
            if i.codtipoitem.codtipoitem == 5:
                entraceHallList.append(i.nome)
            if i.codtipoitem.codtipoitem == 7:
                cakeTableList.append(i.nome)
            if i.codtipoitem.codtipoitem == 4:
                courtesyList.append(i.nome)
            if i.codtipoitem.codtipoitem == 8:
                liningList.append(i.nome)
            if i.codtipoitem.codtipoitem == 3:
                parentsTableList.append(i.nome)
            if i.codtipoitem.codtipoitem == 2:
                centerpieceList.append(i.nome)
    
    if contract.tipocontrato == 'E':
        print(f'-----\nDEBUG: Compartilhando contrato do Espaço: CODCONTRATO: {contract.codcontrato}, Cliente: {contract.codcliente.codcliente} - {contract.codcliente.nome}')
        return redirect(f'/generate-pdf/?codcontrato_old={0}&operacao={2}&name={contract.codcliente.nome}&address={contract.codcliente.endereco}&cpf={contract.codcliente.cpf}&phone={contract.codcliente.telefone}&have10tables={contract.mesasinclusas}&checkSeparateTables={None}&squareTables={contract.mesasqavulsas}&roundTables={contract.mesasravulsas}&checkSeparateChairs={None}&amountChairs={contract.cadeirasavulsas}&checkSeparateTowels={None}&amountTowels={contract.toalhasavulsas}&otherItems={None}&otherItemsList={ItemsList}&date={contract.dtevento}&entryTime={contract.horaentrada}&departureTime={contract.horasaida}&eventType={contract.tipoevento}&numberOfPeople={contract.qtdconvidados}&eventValue={contract.valortotal}&antecipatedValue={contract.valorsinal}')
    else:
        print(f'-----\nDEBUG: Compartilhando contrato de Decoração: CODCONTRATO: {contract.codcontrato}, Cliente: {contract.codcliente.codcliente} - {contract.codcliente.nome}')
        return redirect(f'/generate-pdf-decoration/?codcontrato_old={0}&operacao={2}&name={contract.codcliente.nome}&address={contract.codcliente.endereco}&eventAddress={contract.enderecoevento}&cpf={contract.codcliente.cpf}&phone={contract.codcliente.telefone}&religiousList={religiousList}&entraceHallList={entraceHallList}&cakeTableList={cakeTableList}&courtesyList={courtesyList}&liningList={liningList}&parentsTableList={parentsTableList}&centerpieceList={centerpieceList}&date={contract.dtevento}&eventTime={contract.horaentrada}&eventValue={contract.valortotal}&antecipatedValue={contract.valorsinal}&displacementValue={contract.valordeslocamento}')

# -------------------------------------------------------- DOCFLOW --------------------------------------------------------
@login_required_custom
@verifica_sessao_usuario
def templates(request):
    # Capturar usuário da sessão
    usuario = request.usuario_logado
    
    # Capturar templates da empresa do usuário da sessão
    t = Template()
    ListaObjetosTemplates = t.obterTemplates(usuario.codempresa)
    
    context = {
        'templates': ListaObjetosTemplates,
        'usuario':usuario
    }
    return render(request, 'cg/templates/lista_templates.html', context)

@login_required_custom
@verifica_sessao_usuario
def cadastrar_template(request):
    # Coletando informações passadas em tela
    usuario = request.usuario_logado
    nome = request.POST.get('nome')
    descricao = request.POST.get('descricao')
    template = request.FILES.get('template')
    operacao = int(request.POST.get('operacao'))
    codtemplate = int(request.POST.get('codtemplate'))
    dtatualiz = datetime.now()
    status = 1
    # Instância de Template.
    t = Template(codtemplate=codtemplate, codempresa=usuario.codempresa, nome=nome, 
                    descricao=descricao, dtatualiz=dtatualiz, status=status)
    if operacao == 0: # Novo cadastro
        t.salvarTemplate(template)
        # Registra log no console:
        print(f'\nDEBUG= Cadastrando template.\n  Codigo={t.codtemplate}\n  Caminho={t.template_url}')
        # Retorna para a tela de templates caso tenha criado um novo cadastro. 
        # Caso contrário, segue adiante para atualização de cadastro existente
        messages.success(request, f"O Template \"{t.nome}\" foi cadastrado com sucesso!")
        return redirect('templates')
    # Atualizacao de um cadastro já existente
    ## Se codtemplate for 0, entende-se que não foi selecionado nenhum template em tela
    ## e por isso não será atualizado nenhum template.
    if codtemplate != 0:
        t.atualizarTemplate(template)
    # Registra log no console:
    print(f'\nDEBUG= Atualizando template.\n  Codigo={t.codtemplate}\n  Caminho={t.template_url}')
    messages.success(request, f"O Template \"{t.nome}\" foi atualizado com sucesso!")
    return redirect('templates')

@login_required_custom
@verifica_sessao_usuario
def baixar_template(request):
    usuario = request.usuario_logado
    codtemplate = request.POST.get('codtemplate')

    t = Template()
    t.obterInstanciaTemplateCompletoPorCodtemplate(codempresa=usuario.codempresa, codtemplate=codtemplate)
    arquivo_template = t.obterArquivoTemplate()
    nome_arquivo = f'{t.nome}.docx'
    response = FileResponse(arquivo_template, as_attachment=True, filename=nome_arquivo)
    try:
        return response
    except Exception:
        raise Http404("Arquivo não encontrado.")

@login_required_custom
@verifica_sessao_usuario
def deletar_template(request):
    t = Template(codtemplate=int(request.POST.get('deletar-codtemplate')))
    retorno = t.excluirTemplate() # Exclui objeto tanto do banco quanto do S3
    # print(f'\nDEBUG= Deletando template.\n  Codigo={t.codtemplate}\n')
    # Obter mensagens de retorno para o usuário
    if retorno == 1: messages.success(request, f"O Template \"{t.nome}\" foi deletado com sucesso!")
    elif retorno == 2: messages.warning(request, f"Existem documentos gerados vinculados a este template. Ele será apenas desativado.")
    elif retorno == 3: messages.error(request, f"Ocorreu um erro ao tentar deletar o template \"{t.nome}\". Tente novamente mais tarde.")
    return redirect('templates')

@login_required_custom
@verifica_sessao_usuario
def gerenciar_variaveis(request, codtemplate):
    usuario = request.usuario_logado
    vazio = 1 # Informa se as variáveis estão vazias
    variavel_obj = Variavel(codtemplate=codtemplate).obterVariavelCompletaPorCodtemplate()
    template_obj = Template().obterTemplates(usuario.codempresa, codtemplate) # Também verifica a empresa do usuário
    permiteAtualizavariaveis = 1 # Permite ou não atualizar variáveis, de acordo com o dtatualiz do template
    data = datetime.now()
    jsonVariaveis = {}

    if variavel_obj:
        vazio = 0
        data = variavel_obj.dtatualiz
        permiteAtualizavariaveis = 0 if template_obj.dtatualiz < variavel_obj.dtatualiz else 1
        jsonVariaveis = variavel_obj.variaveis
    
    if not template_obj: # Se não encontrou o template, redireciona para a tela de templates com erro na tela
        messages.error(request, 'Template não encontrado!')
        return redirect('templates')
    
    context = {
        'jsonVariaveis': jsonVariaveis,
        'template':template_obj,
        'dtatualiz':data,
        'vazio': vazio, 
        'permiteAtualizavariaveis': permiteAtualizavariaveis,
        'usuario':usuario
    }

    return render(request, 'cg/variaveis/gerenciar_variaveis.html', context)

@login_required_custom
@verifica_sessao_usuario
def atualizar_variaveis(request, codtemplate):
    usuario = request.usuario_logado

    template = Template() # Obtém informações do template selecionado
    template.obterInstanciaTemplateCompletoPorCodtemplate(usuario.codempresa, codtemplate)
    resultado = template.atualizar_variaveis() # Atualiza variáveis do template selecionado
    if resultado:
        messages.success(request, f'Variáveis do template \"{template.nome}\" atualizadas com sucesso!')
    else:
        messages.warning(request, f'Não foi encontrada nenhuma variável no template \"{template.nome}\".')
    url = reverse('gerenciar_variaveis', kwargs={'codtemplate':codtemplate})
    return redirect(url)
    # return redirect('gerenciar_variaveis', codtemplate=codtemplate)
    # redirect(gerenciar_variaveis(request, codtemplate))

@verifica_sessao_usuario
@login_required_custom
def cadastrar_contrato(request):
    usuario = request.usuario_logado
    codtemplate = request.POST.get('codtemplate')
    variavel_obj = Variavel().obterVariavel(codtemplate=codtemplate)
    dadosFormulario = {}
    nomeArquivo = request.POST.get('nome_arquivo_finale').strip()

    # Garantir que o template selecionado seja da empresa do usuário logado
    if usuario.codempresa != variavel_obj.codtemplate.codempresa:
        return redirect('templates')
    
    # Garantir que o nome do arquivo não esteja vazio
    if nomeArquivo is None or str(nomeArquivo).strip() == "":
        messages.error(request, "O nome do arquivo não pode estar vazio!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
       
    ####    1 - CRIAR MAIS UM CAMPO PARA O CONTRATO, A "LISTA COMUM"
    ####    2 - CRIAR TELA PARA CONTRATOS, QUE MOSTRA LISTA DE CONTRATOS E BOTÃO PARA NOVO CONTRATO
    ####    BOTÃO DE NOVO CONTRATO LEVA PARA UMA TELA QUE PERMITE SELECIONAR TEMPLATES (MOSTRA SOMENTE CARDS DE BOTÕES COM NOMES DOS TEMPLATES) (TENTAR FAZER COMO MODEL PRIMEIRO)

    if request.method == "POST":
        # Rodar a lista de itens adicionais
        dadosItensAdicionais = {} # POR ENQUANTO NÃO ESTÁ FUNCIONANDO CORRETAMENTE
        for key, value in request.POST.items():
            # TITULOS (ex: titulo2, titulo3...)
            if key.startswith("titulo"):
                titulo_id = int(key.replace("titulo", ""))
                lista_id = 1  # se tiver várias listas, extraia de outro campo do POST
                dadosItensAdicionais[(lista_id, titulo_id)] = {"titulo": value, "itens": []}

            # ITENS (ex: item-2-titulo-2-lista-1)
            elif key.startswith("item-"):
                _, item_id, _, titulo_id, _, lista_id = key.split("-")
                lista_id = int(lista_id)
                titulo_id = int(titulo_id)

                if (lista_id, titulo_id) not in dadosItensAdicionais:
                    dadosItensAdicionais[(lista_id, titulo_id)] = {"titulo": "", "itens": []}

                dadosItensAdicionais[(lista_id, titulo_id)]["itens"].append(value)

        # converter para lista de objetos
        lista_itens = []
        for (lista_id, titulo_id), valores in dadosItensAdicionais.items():
            lista_itens.append({
                "lista": lista_id,
                "titulo_id": titulo_id,
                "titulo": valores["titulo"],
                "itens": valores["itens"]  # já vem agrupado corretamente
            })

        # Montar JSON das variáveis com seus respectivos valores preenchidos pelo usuário no formulário
        for v in variavel_obj.variaveis:
            nome_var = str(v.get('nome')).strip().capitalize()
            valor_var = str(request.POST.get(nome_var)).strip()
            dadosFormulario[nome_var] = valor_var if valor_var != 'None' else ''
        dados_json = {"dados_json": dadosFormulario}
        ## Exemplo de JSON: {'dados_json': {'Nome': 'Henrique Torres', 'Idade': '21', 'Valor': '150,00', 'Cpf': '000.111.222-33', 'Telefone': '(62) 9 1234-5678', 'Dataevento': '2025-09-11', 'Hora': '15:17', 'Listaitens': ''}}
        # DEBUG:
        # print(f'\nDEBUG:\n  dadosItensAdicionaisFormatado: {lista_itens} '+
        #     f'\n  dadadosFormulario: {dadosFormulario} '+
        #     f'\n  dados_json: {dados_json}')
        
        # Criar objeto de contrato
        c = ContratosC(codusuario=usuario, codtemplate=variavel_obj.codtemplate, codempresa=usuario.codempresa,
                       contrato_json=dados_json,nome_arquivo=nomeArquivo, status=1, dtatualiz=datetime.now())
        retorno = c.gerarContrato() # Salvar o contrato
        if retorno: # Se o contrato foi gerado com sucesso
            messages.success(request, f'O documento \"{c.nome_arquivo}\" foi gerado com sucesso!')
        else:
            messages.error(request, 'Ocorreu um erro ao gerar o documento. Tente novamente.')
    return redirect('contratos')

@verifica_sessao_usuario
@login_required_custom
def form_contrato(request, codtemplate):
    usuario = request.usuario_logado
    html_string = ""
    # Garantir que o template seja da empresa do usuário
    template_obj = Template().obterTemplates(usuario.codempresa, codtemplate=codtemplate)
    if template_obj:
        v = Variavel(codtemplate=template_obj.codtemplate) # Instanciar as variáveis do template selecionado
        v.obterVariavelCompletaPorCodtemplate() # Obter informações no banco sobre a variável
    else: # Caso não encontre o template informado
        messages.error(request, 'Template não encontrado!')
        return redirect('templates')
    
    possui_variavel = 0 if v.variaveis == [] else 1
    html_string = v.GerarForularioDinamico() # Gerar formulário

    nometemplate = v.codtemplate.nome if v.variaveis else ''

    context = {
        'formulario': html_string,
        'nometemplate': nometemplate,
        'codtemplate': codtemplate,
        'possui_variavel': possui_variavel,
        'usuario':usuario
    }

    return render(request, 'cg/contratos/form_contrato.html', context)

@verifica_sessao_usuario
@login_required_custom
def contratos(request):
    usuario = request.usuario_logado
    # Buscar os contratos da empresa do usuário logado 
    listaObjetosContratos = ContratosC().obterContratos(usuario.codempresa)
    listaObjetosTemplates = Template().obterTemplates(usuario.codempresa)

    vazio = 0 if listaObjetosContratos else 1 # Informar se a lista é vazia
    # Enviar lista para a página HTML
    context = {
        'listaObjetosContratos':listaObjetosContratos,
        'listaObjetosTemplates':listaObjetosTemplates,
        # 'vazio':vazio,
        'usuario':usuario
    }
    # return render(request, 'cg/contratos/lista_contratos-card.html', context) # Visualização em cards
    return render(request, 'cg/contratos/lista_contratos-table.html', context) # Visualização em tabela

@login_required_custom
@verifica_sessao_usuario
def baixar_contrato(request):
    usuario = request.usuario_logado
    codcontrato = request.POST.get('codcontrato')

    c = ContratosC()
    retorno = c.obterContratos(codempresa=usuario.codempresa, codcontrato=codcontrato)
    if retorno is None:
        messages.error(request, 'O documento informado não foi encontrado.')
        return redirect('contratos')
    arquivo_template = c.obterArquivoContrato()
    if not arquivo_template:
        messages.error(request, 'O documento não possui arquivo.')
        return redirect('contratos')
    nome_arquivo = f'{c.nome_arquivo}.docx'
    response = FileResponse(arquivo_template, as_attachment=True, filename=nome_arquivo)
    try:
        return response
    except Exception:
        raise Http404("Arquivo não encontrado.")

def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', texto)
        if not unicodedata.combining(c)
    )

# Transforma variável do tipo date em 3 variáveis, dia, mês e ano
def transforma_data(date):
    c = 0
    day = ''
    month = ''
    year = ''
    for i in date:
        if i == '-': c+=1
        if c == 0 and i != '-':year+=i 
        if c == 1 and i != '-':month+=i
        if c == 2 and i != '-':day+=i
    if month == '01': month = 'Janeiro'
    elif month == '02': month = 'Fevereiro'
    elif month == '03': month = 'Março'
    elif month == '04': month = 'Abril'
    elif month == '05': month = 'Maio'
    elif month == '06': month = 'Junho'
    elif month == '07': month = 'Julho'
    elif month == '08': month = 'Agosto'
    elif month == '09': month = 'Setembro'
    elif month == '10': month = 'Outubro'
    elif month == '11': month = 'Novembro'
    elif month == '12': month = 'Dezembro'

    print(f'===============================\n Day: {day}\n Month: {month}\n Year: {year}\n=============================== ')

    return day, month, year