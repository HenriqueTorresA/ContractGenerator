import ast, re
import os
import unicodedata
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from datetime import datetime, date as dt
from .models import Empresas, Usuarios, Clientes, Contrato, Tipositensadicionais, Itensadicionais, Codtipoitens_itensadicionais, Visualizar_contratos, Templates, Variaveis
from .classes.Template import Template
from .classes.Variavel import Variavel
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from docx import Document
from .decorators import login_required_custom, verifica_sessao_usuario
from collections import defaultdict
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import boto3

#### caso haja alguma adição de módulos, é necessário rodar o seguinte comando:
#### pip freeze > requirements.txt
#### localmente, pois se não a Vercel terá problemas para instalar as dependências do projeto

# ORIENTAÇÕES PARA RODAR O CÓDIGO
# Bibliotecas para instalar:
    
# python manage.py runserver

#Caso dê um erro na hora de rodar, dizendo:
#### ""ModuleNotFoundError: No module named 'django'"
#### ImportError: Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?
# Então é necessário ativar o ambiente virtual. Basta rodar o seguinte comando:
#### .\venv\Scripts\activate

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
    if request.method == "GET":
        return render(request, 'cg/login.html')
    
    else: 
        login = request.POST.get('cpf')
        senha = request.POST.get('senha')

        # Tente encontrar o usuário com o login fornecido
        try:
            usuario = Usuarios.objects.get(login=login)  # Busca pelo login no modelo Usuarios
        except Usuarios.DoesNotExist:
            messages.error(request, 'Usuário não encontrado!')
            return render(request, 'cg/login.html')

        # Verifica se a senha fornecida é correta
        if check_password(senha, usuario.senha):  # Compara a senha fornecida com a armazenada
            # Inicia a sessão do usuário
            request.session['user_id'] = usuario.codusuario
            request.session.set_expiry(30 * 60)  # Define que a sessão expira em 30 minutos
            return redirect('home')  # Redireciona para a página home após o login bem-sucedido
        
        else:
            messages.error(request, 'Senha incorreta!')
            return render(request, 'cg/login.html')

def erro_sessao(request):
    return render(request, 'cg/erros/erro_sessao.html')

@login_required_custom
def home(request):
    # Pega o usuário logado da sessão
    usuario = Usuarios.objects.get(codusuario=request.session['user_id'])

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
    return render(request, 'cg/home.html', {'usuario': usuario})

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
def lista_usuarios(request):
    usuarios = Usuarios.objects.all()  # Busca todos os usuários do banco de dados
    return render(request, 'cg/usuarios.html', {'usuarios': usuarios})

# View para editar o usuário
@login_required_custom
def editar_usuario(request, codusuario):
    usuario = get_object_or_404(Usuarios, codusuario=codusuario)
    
    if request.method == "POST":
        usuario.nome = request.POST.get('nome')
        usuario.email = request.POST.get('email')
        usuario.login = request.POST.get('login')
        
        # Verifica se a senha foi alterada
        nova_senha = request.POST.get('senha')
        if nova_senha:
            # Se o usuário fornecer uma nova senha, ela é criptografada
            usuario.senha = make_password(nova_senha)
        
        usuario.permissoes = request.POST.get('permissao')
        usuario.save()
        
        return redirect('lista_usuarios')
    
    return render(request, 'cg/editar_usuario.html', {'usuario': usuario})

# View para excluir o usuário
@login_required_custom
def excluir_usuario(request, codusuario):
    usuario = get_object_or_404(Usuarios, codusuario=codusuario)
    if request.method == "POST":
        usuario.delete()
        return redirect('lista_usuarios')

    return render(request, 'cg/excluir_usuario.html', {'usuario': usuario})

def cadastro(request):
    if request.method == "GET":
        return render(request, 'cg/cadastro.html')
    else:
        nome = request.POST.get('nome')
        login = request.POST.get('cpf')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        # Verifica se o usuário já existe no seu modelo personalizado
        if Usuarios.objects.filter(login=login).exists():
            # Redireciona para a página de cadastro com uma mensagem de erro na URL
            return HttpResponseRedirect(f"{reverse('cadastro')}?error=Já existe um usuário com esse CPF/CNPJ cadastrado")

        # Cria um novo usuário no seu modelo personalizado com codempresa fixo em 1
        usuario = Usuarios.objects.create(
            nome=nome,
            login=login,
            email=email,
            senha=make_password(senha),  # Armazena a senha como um hash
            codempresa_id=1  # Define codempresa como 1
        )
        usuario.save()

        return redirect('cadastro')  # Redireciona para a página de cadastro

def logout(request):
    # Remove a sessão do usuário e redireciona para a página de login
    request.session.flush()  # Limpa todos os dados da sessão
    return redirect('login')

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

@login_required_custom
@verifica_sessao_usuario
def templates(request):
    # Capturar usuário da sessão
    usuario = request.usuario_logado
    
    # Capturar templates da empresa do usuário da sessão
    t = Template()
    ListaObjetosTemplates = t.obterTemplates(usuario.codempresa)
    
    context = {
        'templates': ListaObjetosTemplates
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
    dtatualiz = dt.today()
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
        return redirect('templates')
    # Atualizacao de um cadastro já existente
    ## Se codtemplate for 0, entende-se que não foi selecionado nenhum template em tela
    ## e por isso não será atualizado nenhum template.
    if codtemplate != 0:
        t.atualizarTemplate(template)
    # Registra log no console:
    print(f'\nDEBUG= Atualizando template.\n  Codigo={t.codtemplate}\n  Caminho={t.template_url}')
    return redirect('templates')

@login_required_custom
@verifica_sessao_usuario
def deletar_template(request):
    t = Template(codtemplate=int(request.POST.get('deletar-codtemplate')))
    t.excluirTemplate() # Exclui objeto tanto do banco quanto do S3
    # Registra log no console:
    print(f'\nDEBUG= Deletando template.\n  Codigo={t.codtemplate}\n')
    return redirect('templates')

@login_required_custom
@verifica_sessao_usuario
def gerenciar_variaveis(request, codtemplate):
    usuario = request.usuario_logado
    vazio = 1 # Informa se as variáveis estão vazias
    variavel_obj = Variavel(codtemplate=codtemplate).obterVariavelCompletaPorCodtemplate()
    template_obj = Template().obterTemplates(usuario.codempresa, codtemplate)
    permiteAtualizavariaveis = 1 # Permite ou não atualizar variáveis, de acordo com o dtatualiz do template
    data = dt.today()
    jsonVariaveis = {}

    if variavel_obj:
        vazio = 0
        data = variavel_obj.dtatualiz
        permiteAtualizavariaveis = 0 if template_obj.dtatualiz < variavel_obj.dtatualiz else 1
        jsonVariaveis = variavel_obj.variaveis
    
    context = {
        'jsonVariaveis': jsonVariaveis,
        'template':template_obj,
        'dtatualiz':data,
        'vazio': vazio, 
        'permiteAtualizavariaveis': permiteAtualizavariaveis
    }

    return render(request, 'cg/variaveis/gerenciar_variaveis.html', context)

@login_required_custom
@verifica_sessao_usuario
def atualizar_variaveis(request, codtemplate):
    usuario = request.usuario_logado

    template = Template() # Obtém informações do template selecionado
    template.obterInstanciaTemplateCompletoPorCodtemplate(usuario.codempresa, codtemplate)
    template.atualizar_variaveis() # Atualiza variáveis do template selecionado

    return redirect('templates')
    # redirect(gerenciar_variaveis(request, template_obj.codtemplate))

@verifica_sessao_usuario
@login_required_custom
def cadastrar_contrato(request):
    codtemplate = request.POST.get('codtemplate')
    variaveis = Variaveis.objects.filter(codtemplate=codtemplate).first()
    dadosFormulario = {}
    ####    PROXIMO PASSO É CRIAR LÓGICA PARA REGISTRAR AS VARIAVEIS NO TEMPLATE, CRIANDO O PDF
    ####    E SALVAR O ARQUIVO PDF NO BANCO DE DADOS
    ####    DEPOIS CRIAR MAIS UM CAMPO PARA O CONTRATO, QUE É A LISTA COMUM
    ####    DEPOIS DISSO CRIAR TELA PARA CONTRATOS, QUE MOSTRA LISTA DE CONTRATOS E BOTÃO PARA NOVO CONTRATO
    ####    BOTÃO DE NOVO CONTRATO LEVA PARA UMA TELA QUE PERMITE SELECIONAR TEMPLATES (MOSTRA SOMENTE CARDS DE BOTÕES COM NOMES DOS TEMPLATES) (TENTAR FAZER COMO MODEL PRIMEIRO)
    # criar variável no template


    if request.method == "POST":
        # Rodar a lista de itens adicionais
        dadosItensAdicionais = defaultdict(lambda: {"titulo": "", "itens": []})
        for key, value in request.POST.items():
            if key.startswith("titulo-"):
                _, titulo_id, _, lista_id = key.split("-")
                dadosItensAdicionais[(lista_id, titulo_id)]["titulo"] = value
            elif key.startswith("item-"):
                _, item_id, _, titulo_id, _, lista_id = key.split("-")
                dadosItensAdicionais[(lista_id, titulo_id)]["itens"].append(value)

        # coletar os demais elementos do formulário
        for v in variaveis:
            nome_var = str(v.get('nome')).strip().capitalize()
            valor_var = str(request.POST.get(nome_var)).strip()
            dadosFormulario[nome_var] = valor_var
        dados_json = {"dados_json": dadosFormulario}

        # Regex para identificar as expressões no formato <?tipo:nome:descricao?>
        padrao = r"<\?([a-zA-Z0-9_]+):([a-zA-Z0-9_]+):.*?\?>"

    print(f'\nDEBUG:\n{dadosItensAdicionais}\n')

    return redirect('templates')

@verifica_sessao_usuario
@login_required_custom
def form_contrato(request, codtemplate):
    # usuario = request.usuario_logado
    html_string = ""

    v = Variavel(codtemplate=codtemplate) # Instanciar as variáveis do template selecionado
    v.obterVariavelCompletaPorCodtemplate() # Obter informações no banco sobre a variável
    html_string = v.GerarForularioDinamico() # Gerar formulário

    context = {
        'formulario': html_string,
        'nometemplate':v.codtemplate.nome
    }

    return render(request, 'cg/contratos/form_contrato.html', context)


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