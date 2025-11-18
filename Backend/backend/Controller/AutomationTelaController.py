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
from backend.models import Tela, ClienteAuten, Automation, AutomationType
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers
from django.db import transaction
from backend.Controller.BaseController import doLog

@login_required
def indexView(request, automation_type):
    data = Tela.objects.filter(status=True).order_by('-id')

    context = {
        'data': data,
        'automation_type': automation_type
    }

    return render(request, 'Automation/Tela/index.html', context)

@login_required
def newView(request, automation_type):    
    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')
    
    context = {        
        'clients': clients,
        'automation_type': automation_type
    }

    return render(request, 'Automation/Tela/new.html', context)

@login_required
@require_http_methods(["POST"])
def saveAction(request, automation_type):
    
    try:
        with transaction.atomic():
            automationType = AutomationType.objects.get(id=automation_type)            
            client_id = request.POST.get('client_id', None)
            version = request.POST.get('version_current', None)
            description = request.POST.get('description', None)        
            status = request.POST.get('status', 0)            
            
            # Criar automation
            automation = Automation()
            if client_id != '0':                
                automation.cliente_auten = ClienteAuten.objects.get(id=client_id)
            automation.description = 'VicSensor - Tela'
            automation.status = status
            automation.automation_type = automationType
            automation.type_location = 'Lavoura'
            automation.created_by = request.user.id
            automation.created_at = datetime.datetime.now()
            automation.save()
            
            # Criar V2
            t = Tela()
            t.automation = automation            
            t.version_current = version
            t.description = description
            t.status = status
            t.created_by = request.user.id
            t.created_at = datetime.datetime.now()
            t.save()

            doLog('TELA +1', f'TELA #{t.id} .O Usuário <b>@{request.user.first_name}</b> add o cadastro!', 1) # Success

            messages.add_message(request, messages.SUCCESS, f'Registro salvo com sucesso! ID #{t.id}')
            return redirect('TelaIndexView', automation_type)
    
    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('AutomationIndexView')
        
@login_required
@require_http_methods(["GET"])
def editView(request, automation_type, tela_id):
    
    tela = Tela.objects.get(id=tela_id)    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')    
    
    context = {
        'tela': tela,
        'automation_type': automation_type,
        'clients': clients
    }
    
    return render(request, 'Automation/Tela/edit.html', context)

@login_required
@require_http_methods(["POST"])
def editSaveAction(request, automation_type, tela_id):

    try:
        with transaction.atomic():
            automationType = AutomationType.objects.get(id=automation_type)
            client_id = int(request.POST.get('client_id', None))
            version = request.POST.get('version_current', None)
            description = request.POST.get('description', None)
            status = request.POST.get('status', 0)                                                                            
                
            t = Tela.objects.get(id=tela_id)
            if client_id != 0:
                t.automation.cliente_auten = ClienteAuten.objects.get(id=client_id)
            else:
                t.automation.cliente_auten = None
            t.automation.save()
            
            t.description = description
            t.version_current = version
            t.status = status
            t.updated_by = request.user.id
            t.updated_at = datetime.datetime.now()
            t.save()
            
            doLog('TELA alterada', f'TELA #{t.id} .O Usuário <b>@{request.user.first_name}</b> editou o cadastro!', 2) # Info

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('TelaIndexView', automation_type)

    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('AutomationIndexView')
      
@login_required
def deleteAction(request, tela_id):

    try:
        t = Tela.objects.get(id=int(tela_id))
        doLog('TELA Excluída', f'TELA #{t.id} .O Usuário <b>@{request.user.first_name}</b> excluiu essa automação.', 0) # Error
        t.delete()

        context = {
            'status': 200,
            'descricao': 'Excluído com sucesso'
        }
    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
   
