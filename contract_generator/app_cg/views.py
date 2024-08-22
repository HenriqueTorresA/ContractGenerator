import os
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

#from contract_generator.contract_generator import settings
from django.conf import settings

# Create your views here.
def home(request):

    return render(request, 'cg/home.html')

#PROCURANDO O CAMINHO DO SERVICE WORKER
class ServiceWorkerView(View):
    def get(self, request, *args, **kwargs):
        service_worker_path = os.path.join(settings.BASE_DIR, 'static/js', 'service-worker.js')
        try:
            with open(service_worker_path, 'r') as service_worker:
                response = HttpResponse(service_worker.read(), content_type='application/javascript')
                return response
        except FileNotFoundError:
            return HttpResponse(status=404)
        
# ACESSAR TELA DE NEGOCIAÇÃO DO CONTRATO
def trading_screen(request):
    return render(request, 'cg/new_contract/negociacao.html')

# CARREGAR AS INFORMAÇÕES DA NEGOCIAÇÃO DO CONTRATO
def trading_data(request):
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
    eventValue = request.POST.get('event-value')
    antecipatedValue = request.POST.get('antecipated-value')

    if request.POST:
        for key in request.POST:
            # Verifica se a chave começa com 'other-items'
            if key.startswith('other-items'):
                otherItems[key] = request.POST.get(key)




    return redirect(f'/resumo-do-contrato/?name={name}&address={address}&cpf={cpf}&phone={phone}&have10tables={have10tables}&checkSeparateTables={checkSeparateTables}&squareTables={squareTables}&roundTables={roundTables}&checkSeparateChairs={checkSeparateChairs}&amountChairs={amountChairs}&checkSeparateTowels={checkSeparateTowels}&amountTowels={amountTowels}&otherItems={otherItems}&date={date}&entryTime={entryTime}&departureTime={departureTime}&eventType={eventType}&eventValue={eventValue}&antecipatedValue={antecipatedValue}')

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
    date = request.GET.get('date')
    entryTime = request.GET.get('entryTime')
    departureTime = request.GET.get('departureTime')
    eventType = request.GET.get('eventType')
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
               'date':date,
               'entryTime':entryTime,
               'departureTime':departureTime,
               'eventType':eventType,
               'eventValue':eventValue,
               'antecipatedValue':antecipatedValue,
               }

    return render(request,'cg/new_contract/resumo.html',context)

def generate_pdf(request):
    template_path = 'cg/new_contract/teste.html' #template_contrato.html

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
    otherItems = request.GET.get('otherItems')
    date = request.GET.get('date')
    entryTime = request.GET.get('entryTime')
    departureTime = request.GET.get('departureTime')
    eventType = request.GET.get('eventType')
    eventValue = request.GET.get('eventValue')
    antecipatedValue = request.GET.get('antecipatedValue')

    if name is None: name = '__________________________'
    if address is None: address = '____________________________________'
    if cpf is None: cpf = '__________________'
    itemhave10tables = '10 jogos de mesas quadradas (fornecido pelo espaço);' if have10tables == 'True' else ''
    havesquaretables = f'{squareTables} mesas quadradas avulsas;' if checkSeparateTables == 'True' and squareTables is not '' else ''
    haveroundtables = f'{roundTables} mesas redondas avulsas;' if checkSeparateTables == 'True' and roundTables is not '' else ''
    haveamountchairs = f'{amountChairs} cadeiras avulsas;' if checkSeparateChairs == 'True' and amountChairs is not '' else ''
    haveamounttowels = f'{amountTowels} cadeiras avulsas;' if checkSeparateTowels == 'True' and amountTowels is not '' else ''
    haveotheritems = f'{otherItems}' if otherItems is not '' else ''
    #otherItems = '<li>'+otherItems
    # usar 
    if phone is None: phone = '_____________________'
    if date is None: date = '__________________________'
    if entryTime is None: entryTime = '__________________________________'
    if departureTime is None: departureTime = '__________________________________'
    if eventType is None: eventType = '__________________________'
    if eventValue is None: eventValue = '_____________'
    if antecipatedValue is None: antecipatedValue = '_____________'

    #print(f'================\n  checkSeparateTables = {checkSeparateTables} \n  squareTables = {squareTables}\n  havesquaretables = {havesquaretables} \n================')

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
               'haveotheritems':haveotheritems,
               'otherItems':otherItems,
               'date':date,
               'entryTime':entryTime,
               'departureTime':departureTime,
               'eventType':eventType,
               'eventValue':eventValue,
               'antecipatedValue':antecipatedValue,
               }
    
    # Renderizar o template em HTML
    html = render_to_string(template_path, context)
    
    # Criar um response como PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="arquivo.pdf"'
    
    # Criar o PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=400)
    
    return response
