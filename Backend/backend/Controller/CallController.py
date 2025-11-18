from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile, DateSTR2Datetime, str_to_datetime
from backend.models import Carro, ClienteAuten, Tecnico, ASSUNTO_CALL_CHOICES, Call, STATUS_CALL_CHOICES, AuthUser, CallChild
from slock.settings import DOMAIN_ASSETS
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from backend.Controller.BaseController import doLog
import datetime
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_http_methods

@login_required
@require_http_methods(["GET"])
def indexView(request):
    # Inicia o QuerySet com todos os registros
    calls = Call.objects.all()

    # Obtém os filtros via GET
    tecnico = request.GET.get('tecnico')
    cliente = request.GET.get('cliente')
    assunto = request.GET.get('assunto')
    status = request.GET.get('status')
    data = request.GET.get('data')

    # Aplica os filtros se os parâmetros estiverem presentes
    if tecnico:
        calls = calls.filter(tecnico=Tecnico.objects.get(id=tecnico))
    if cliente:
        calls = calls.filter(cliente_auten=ClienteAuten.objects.get(id=cliente))
    if assunto:
        calls = calls.filter(assunto=assunto)
    if status:
        if status == '-2': # Pendente + Em Atendimento (0 + 3)
            calls = calls.filter(Q(status=0) | Q(status=3))
        else:
            calls = calls.filter(status=status)            
    if data:
        today = timezone.now()

        if data == '1':
            date_limit = today - timedelta(days=90)
        elif data == '2':
            date_limit = today - timedelta(days=60)
        elif data == '3':
            date_limit = today - timedelta(days=30)
        
        calls = calls.filter(call_at__gte=date_limit)
        
    # Ordena os registros conforme a data do chamado
    calls = calls.order_by('call_at')

    context = {
        'data': calls,
        'qtd_atendimentos': len(calls),
        'DOMAIN_ASSETS': DOMAIN_ASSETS
    }

    return render(request, 'Call/index.html', context)

@login_required
@require_http_methods(["POST"])
def saveAnswer(request, call_id):

    call = Call.objects.get(id=call_id)
    resposta = request.POST.get('resposta', None)    
    call_at_child = request.POST.get('call_at_child', None)    
    next_action = request.POST.get('next_action', None)    
    status = request.POST.get('status', None)   
    
    if not status or not resposta:
        messages.add_message(request, messages.ERROR, 'Ops, faltou dados no seu formulário!')    
        return redirect('CallIndexView')
    
    cchild = CallChild()
    cchild.call = call        
    cchild.resposta = resposta
    cchild.next_action = next_action
    cchild.call_at = str_to_datetime(call_at_child)
    cchild.created_at = datetime.datetime.now()
    cchild.created_by = request.user.id
    cchild.save()
    
    call.resposta = resposta
    call.call_at = cchild.call_at
    call.status = int(status)
    call.updated_by = request.user.id
    call.updated_at = datetime.datetime.now()
    call.save()
    
    doLog('+CALL', f'CALL #{call.id} .<b>@{request.user.first_name}</b> alterou ({call.cliente_auten.nome}) o atendimento #{call.id} para <b>{call.get_status_display()}</b>', 2) # INFO
    
    messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')        
    
    return redirect('CallFilterView')

@login_required
@require_http_methods(["GET"])
def editView(request, call_id):
    
    call = Call.objects.get(id=call_id)
    
    callChilds = CallChild.objects.filter(call=call)

    context = {
        'call': call,
        'callChilds': callChilds,
        'DOMAIN_ASSETS': DOMAIN_ASSETS,
        'STATUS_CALL_CHOICES': STATUS_CALL_CHOICES
    }

    return render(request, 'Call/edit.html', context)

@csrf_exempt
@require_http_methods(["GET"])
def getDataForNewCall(request):

    """
    Essa fn é executada toda vez que alguém clica em nova ligação.
    Basicamente ela é responsável por carregar os selects de clientes,
    colaboradores e etc...
    """
    
    try:        
        
        clientes = ClienteAuten.objects.filter(status=True).values('id', 'nome', 'telefone', 'cidade', 'uf')
        tecnicos = Tecnico.objects.filter(status=True).values('id', 'nome', 'telefone')        
        
        return JsonResponse({
            'ASSUNTO_CALL_CHOICES': ASSUNTO_CALL_CHOICES,
            'clientes': list(clientes),
            'tecnicos': list(tecnicos)
        }) 

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def saveAction(request):

    try:        

        dados = json.loads(request.body)
        
        call = Call()
        call.cliente_auten = ClienteAuten.objects.get(id=dados['cliente'])
        call.tecnico = Tecnico.objects.get(id=dados['tecnico'])
        call.assunto = dados['assunto']
        call.descricao = dados['problema']
        call.call_at = str_to_datetime(dados['dataehora'])
        call.status = 0 # Pendente
        call.created_at = datetime.datetime.now()        
        call.save()
        
        doLog('+CALL', f'Nova Ligação agendada para o <b>@{call.tecnico.nome}</b>. {call.cliente_auten.telefone}. Cliente: {call.cliente_auten.nome}', 2) # Info

        return JsonResponse({
            'status': 200,
            'description': 'Ligação agendada com sucesso!'
        }) 

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@login_required
def deleteAction(request, carro_id):

    item = Carro.objects.get(id=carro_id)        
   
    try:
        item.delete()
        messages.add_message(request, messages.SUCCESS, "Excluído com sucesso!")
    except Exception as e:
        messages.add_message(request, messages.ERROR, "Ocorreu esse erro: {}".format(e))


    context = {
        'status': 200,
        'descricao': 'Excluído com sucesso'
    }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@login_required
@require_http_methods(["GET"])
def transferView(request, call_id):
            
    call = Call.objects.get(id=call_id)
    tecnicos = Tecnico.objects.filter(status=True)

    context = {
        'call': call,
        'DOMAIN_ASSETS': DOMAIN_ASSETS,
        'tecnicos': tecnicos
    }

    return render(request, 'Call/transfer.html', context)

@require_http_methods(["POST"])
def transferAction(request, call_id):
            
    call = Call.objects.get(id=call_id)
    old_tecnico = call.tecnico
    
    tecnico = Tecnico.objects.get(id=request.POST.get('tecnico', None))
    
    call.tecnico = tecnico    
    call.updated_at = datetime.datetime.now()
    call.updated_by = request.user.id
    call.save()
    
    cchild = CallChild()
    cchild.call = call        
    cchild.resposta = f'{request.user.first_name} transferiu o atendimento que estava em {old_tecnico.nome} para {tecnico.nome}.'
    cchild.next_action = cchild.resposta
    cchild.call_at = datetime.datetime.now()
    cchild.created_at = datetime.datetime.now()
    cchild.created_by = request.user.id
    cchild.save()
    
    doLog('+Transferência de Atendimento', f'Transferência de Atendimento #{call.id}. <b>@{tecnico.nome}</b> você tem um novo atedimento que estava sob as responsabilidades de <b>@{old_tecnico.nome}</b> transferiu para você! Cliente: <b>{call.cliente_auten.nome}</b>', 2) # INFO

    messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')    
    
    return redirect('CallIndexAtenderView', call_id)

@login_required
@require_http_methods(["GET"])
def filterView(request):        
            
    tecnicos = Tecnico.objects.filter(status=True)
    clientes = ClienteAuten.objects.filter(status=True)

    context = {
        'tecnicos': tecnicos,
        'clientes': clientes,
        'DOMAIN_ASSETS': DOMAIN_ASSETS,
        'ASSUNTO_CALL_CHOICES': ASSUNTO_CALL_CHOICES,
        'STATUS_CALL_CHOICES': STATUS_CALL_CHOICES
    }

    return render(request, 'Call/filter.html', context)

@login_required
@require_http_methods(["POST"])
def filterAction(request):
    tecnico = request.POST.get('tecnico')
    cliente = request.POST.get('cliente')
    assunto = request.POST.get('assunto')
    status = request.POST.get('status')
    data = request.POST.get('data')

    # Cria um dicionário com os filtros se eles estiverem presentes
    params = {}
    if tecnico and tecnico != '-1': # Todos
        params['tecnico'] = tecnico
    if cliente and cliente != '-1': # Todos
        params['cliente'] = cliente
    if assunto and assunto != '-1': # Todos
        params['assunto'] = assunto
    if status and status != '-1':   # Todos
        params['status'] = status
    if data and data != '-1':       # Todos
        params['data'] = data

    # Constrói a URL com os parâmetros
    url = f"{reverse('CallIndexView')}?{urlencode(params)}"
    return redirect(url)

