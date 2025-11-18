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
from backend.models import AtronDevice, AtronDeviceRegister, ClienteAuten, Automation, AutomationType
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers
from django.db import transaction
from backend.Controller.BaseController import doLog

@login_required
def indexView(request, automation_type):
    data = AtronDevice.objects.filter(status=True).order_by('-id')

    context = {
        'data': data,
        'automation_type': automation_type
    }

    return render(request, 'Automation/Atron/index.html', context)

@login_required
def newView(request, automation_type):
    atronDevicesRegisters = AtronDeviceRegister.objects.filter(status=True).order_by('-id')
    
    if not atronDevicesRegisters:
        messages.add_message(request, messages.WARNING, "Não há registro de novos GPS's produzidos!")
        return redirect('AtronIndexView', automation_type)
    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')
    
    context = {
        'atronDevicesRegisters': atronDevicesRegisters,
        'clients': clients,
        'automation_type': automation_type
    }

    return render(request, 'Automation/Atron/new.html', context)

@login_required
@require_http_methods(["POST"])
def saveAction(request, automation_type):
    
    try:
        with transaction.atomic():
            automationType = AutomationType.objects.get(id=automation_type)
            atron_device_register_id = request.POST.get('atron_device_register_id', None)
            client_id = request.POST.get('client_id', None)
            description = request.POST.get('description', None)        
            status = request.POST.get('status', 0)

            if not atron_device_register_id:
                messages.add_message(request, messages.ERROR, 'Device Register is required!')
                return redirect('AtronIndexView')
            
            atronDeviceRegister = AtronDeviceRegister.objects.get(id=atron_device_register_id)
            
            # Criar automation
            automation = Automation()
            if client_id != '0':                
                automation.cliente_auten = ClienteAuten.objects.get(id=client_id)
            automation.description = 'Atron GPS'
            automation.status = status
            automation.automation_type = automationType
            automation.type_location = 'Atron GPS'
            automation.created_by = request.user.id
            automation.created_at = datetime.datetime.now()
            automation.save()
            
            # Criar Atron Device
            atron = AtronDevice()
            atron.automation = automation
            atron.atron_device_register = atronDeviceRegister
            atron.description = description
            atron.status = status
            atron.created_by = request.user.id
            atron.created_at = datetime.datetime.now()
            atron.save()
            
            # Alterar o register para usado
            atronDeviceRegister.status = 0
            atronDeviceRegister.save()    

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('AtronIndexView', automation_type)
    
    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('AutomationIndexView')
        
@login_required
@require_http_methods(["GET"])
def editView(request, automation_type, atron_device):
    
    atronDevice = AtronDevice.objects.get(id=atron_device)    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')    
    
    context = {
        'atronDevice': atronDevice,
        'automation_type': automation_type,
        'clients': clients        
    }
    
    return render(request, 'Automation/Atron/edit.html', context)

@login_required
@require_http_methods(["POST"])
def editSaveAction(request, automation_type, atron_device):
    
    try:
        with transaction.atomic():
            automationType = AutomationType.objects.get(id=automation_type)       
            client_id = request.POST.get('client_id', None)                                                     
            description = request.POST.get('description', None)
            status = request.POST.get('status', 0)                                    
            
            atron = AtronDevice.objects.get(id=atron_device)
            
            if client_id != '0':
                atron.automation.cliente_auten = ClienteAuten.objects.get(id=client_id)
            else:
                atron.automation.cliente_auten = None
            
            atron.description = description
            atron.status = status
            atron.updated_by = request.user.id
            atron.updated_at = datetime.datetime.now()
            atron.save()
            atron.automation.save()
            
            doLog('*Atron GPS', f'<b>@{request.user.first_name}</b> <b>Editou</b> o registro #{atron.id} do <b>GPS.</b>', 2) # Warning

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('AtronIndexView', automation_type)
    
    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('AutomationIndexView')
      
@login_required
def deleteAction(request, atron_id):

    try:
        atron = AtronDevice.objects.get(id=int(atron_id))
        atronRegister = atron.atron_device_register
        atronRegister.status = True
        atronRegister.updated_by = request.user.id
        atronRegister.updated_at = timezone.now()
        atronRegister.save()

        atron.delete()

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
   
@login_required
def garantia(request, atron_id):

    try:
        atron = AtronDevice.objects.get(id=int(atron_id))
        
        context = {
            'atron': atron
        }
        
        return render(request, 'Automation/Atron/garantia.html', context)
    
    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }

        return render(request, 'Automation/Atron/garantia.html', context)
   