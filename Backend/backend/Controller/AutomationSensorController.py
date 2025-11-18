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
from backend.models import Sensor, ClienteAuten, Automation, AutomationType
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers
from django.db import transaction
from backend.Controller.BaseController import doLog

@login_required
def indexView(request, automation_type):
    data = Sensor.objects.filter(status=True).order_by('-id')

    context = {
        'data': data,
        'automation_type': automation_type
    }

    return render(request, 'Automation/Sensor/index.html', context)

@login_required
def newView(request, automation_type):    
    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')
    
    context = {        
        'clients': clients,
        'automation_type': automation_type
    }

    return render(request, 'Automation/Sensor/new.html', context)

@login_required
@require_http_methods(["POST"])
def saveAction(request, automation_type):
    
    try:
        with transaction.atomic():
            automationType = AutomationType.objects.get(id=automation_type)            
            client_id = request.POST.get('client_id', None)
            version = request.POST.get('version_current', None)
            modelo = request.POST.get('modelo', None)
            description = request.POST.get('description', None)        
            status = request.POST.get('status', 0)            
            
            # Criar automation
            automation = Automation()
            if client_id != '0':                
                automation.cliente_auten = ClienteAuten.objects.get(id=client_id)
            automation.description = 'VicSensor - Sensor'
            automation.status = status
            automation.automation_type = automationType
            automation.type_location = 'Lavoura'
            automation.created_by = request.user.id
            automation.created_at = datetime.datetime.now()
            automation.save()
            
            # Criar V2
            s = Sensor()
            s.automation = automation      
            s.modelo = modelo      
            s.version_current = version
            s.description = description
            s.status = status
            s.created_by = request.user.id
            s.created_at = datetime.datetime.now()
            s.save()
            
            doLog('SENSOR +1', f'SENSOR #{s.id} .O Usuário <b>@{request.user.first_name}</b> add o cadastro!', 1) # Success

            messages.add_message(request, messages.SUCCESS, f'Registro salvo com sucesso! ID #{s.id}')
            return redirect('SensorIndexView', automation_type)
    
    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('AutomationIndexView')

@login_required
@require_http_methods(["GET"])
def editView(request, automation_type, sensor_id):
    
    sensor = Sensor.objects.get(id=sensor_id)    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')    
    
    context = {
        'sensor': sensor,
        'automation_type': automation_type,
        'clients': clients
    }
    
    return render(request, 'Automation/Sensor/edit.html', context)

@login_required
@require_http_methods(["POST"])
def editSaveAction(request, automation_type, sensor_id):

    try:
        with transaction.atomic():
            automationType = AutomationType.objects.get(id=automation_type)
            client_id = int(request.POST.get('client_id', None))
            version = request.POST.get('version_current', None)
            modelo = request.POST.get('modelo', None)
            description = request.POST.get('description', None)
            status = request.POST.get('status', 0)                                                                            
                
            s = Sensor.objects.get(id=sensor_id)
            if client_id != 0:
                s.automation.cliente_auten = ClienteAuten.objects.get(id=client_id)
            else:
                s.automation.cliente_auten = None
            s.automation.save()
            
            s.modelo = modelo
            s.description = description
            s.version_current = version
            s.status = status
            s.updated_by = request.user.id
            s.updated_at = datetime.datetime.now()
            s.save()

            doLog('SENSOR Edição', f'SENSOR #{s.id} .O Usuário <b>@{request.user.first_name}</b> editou o cadastro!', 2) # Info
            
            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('SensorIndexView', automation_type)

    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('SensorIndexView', automation_type)

@login_required
def deleteAction(request, sensor_id):

    try:
        s = Sensor.objects.get(id=int(sensor_id))
        doLog('SENSOR Excluído', f'SENSOR #{s.id} .O Usuário <b>@{request.user.first_name}</b> excluiu o cadastro!', 0) # Error
        s.delete()

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
   

