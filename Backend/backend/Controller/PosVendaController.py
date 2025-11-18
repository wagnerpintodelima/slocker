from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
import datetime
from django.utils import timezone
import json
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from backend.models import Viagem, ClienteAuten, Client, Carro, Tecnico, PosVenda, ViagemInstalacao, ViagemInstalacaoKit, ViagemInstalacaoKitChild, STATUS_CHOICES
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers
from django.db import transaction
from backend.Controller.BaseController import str_to_datetime
from backend.Controller.BaseController import doLog

@login_required
def indexView(request):

    # Inicia o QuerySet com todos os registros
    posvendas = PosVenda.objects.all()

    # Obtém os filtros via GET
    tecnico = request.GET.get('tecnico')
    cliente = request.GET.get('cliente')
    status = request.GET.get('status')
    data = request.GET.get('data')

    # Aplica os filtros se os parâmetros estiverem presentes
    if tecnico:
        posvendas = posvendas.filter(viagem_instalacao__viagem__tecnico=Tecnico.objects.get(id=tecnico))
    if cliente:
        posvendas = posvendas.filter(viagem_instalacao__viagem__cliente_auten=ClienteAuten.objects.get(id=cliente))    
    if status:
        if status == '0': # Pendente
            posvendas = posvendas.filter(Q(status=0) | Q(status=0))
        else:
            posvendas = posvendas.filter(status=status)            
    if data:
        today = timezone.now()

        if data == '1':
            date_limit = today - timedelta(days=90)
        elif data == '2':
            date_limit = today - timedelta(days=60)
        elif data == '3':
            date_limit = today - timedelta(days=30)
        
        posvendas = posvendas.filter(data_programada_ligacao__gte=date_limit)

    # Ordena os registros conforme a data do chamado
    posvendas = posvendas.order_by('data_programada_ligacao')    

    context = {
        'data': posvendas,
        'data_hora_atual': datetime.datetime.now()
    }

    return render(request, 'PosVenda/index.html', context)

@login_required
@require_http_methods(["GET"])
def editView(request, posvenda_id):
    
    posvendas = PosVenda.objects.get(id=posvenda_id)    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')
    carros = Carro.objects.filter(status=True).order_by('modelo')
    tecnicos = Tecnico.objects.filter(status=True).order_by('nome')
    
    context = {
        'item': posvendas,        
        'empresas': clients,
        'carros': carros,
        'tecnicos': tecnicos
    }
    
    return render(request, 'PosVenda/edit.html', context)

@login_required
@require_http_methods(["POST"])
def editSaveAction(request, posvenda_id):

    try:        
        pv = PosVenda.objects.get(id=posvenda_id)

        with transaction.atomic():

            descricao = request.POST.get('descricao', None)
            satisfacao_cliente = request.POST.get('satisfacao_cliente', None)

            #------------------ Editar Pós Vendas
            pv = PosVenda.objects.get(id=posvenda_id)
            pv.descricao = descricao
            pv.satisfacao_cliente = satisfacao_cliente
            pv.status = 1
            pv.updated_by = request.user.id
            pv.updated_at = datetime.datetime.now()
            pv.save()
            
            doLog('Pós Vendas', f'Pós-Vendas #{pv.id} .O Usuário <b>@{request.user.first_name}</b> Fez a ligação do cliente {pv.viagem_instalacao.viagem.cliente_auten.nome}.', 1) # Success

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('PosVendaIndexView')

    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('PosVendaIndexView')

@login_required         
@require_http_methods(["GET"])
def filterView(request):        

    tecnicos = Tecnico.objects.filter(status=True)
    clientes = ClienteAuten.objects.filter(status=True)

    context = {
        'tecnicos': tecnicos,
        'clientes': clientes,
        'STATUS_CHOICES': STATUS_CHOICES
    }

    return render(request, 'PosVenda/filter.html', context)

@login_required        
@require_http_methods(["POST"])
def filterAction(request):
    tecnico = request.POST.get('tecnico')
    cliente = request.POST.get('cliente')    
    status = request.POST.get('status')
    data = request.POST.get('data')

    # Cria um dicionário com os filtros se eles estiverem presentes
    params = {}
    if tecnico and tecnico != '-1': # Todos
        params['tecnico'] = tecnico
    if cliente and cliente != '-1': # Todos
        params['cliente'] = cliente    
    if status and status != '-1':   # Todos
        params['status'] = status
    if data and data != '-1':       # Todos
        params['data'] = data

    # Constrói a URL com os parâmetros
    url = f"{reverse('PosVendaIndexView')}?{urlencode(params)}"
    return redirect(url)
    
    
    