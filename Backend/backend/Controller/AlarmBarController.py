import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile, DateSTR2Datetime
from backend.models import AlarmBar, Client, Automation, AutomationType, AlarmBarGroup, AlarmBarGroupItem
from slock.settings import DOMAIN_ASSETS, BASE_DIR
from django.db import transaction
from django.views.decorators.http import require_http_methods
import datetime


_PATH_FILE_CLIENT = 'backend/upload/alarmbar/'

@login_required
def newView(request):
    
    empresas = Client.objects.filter(status=True)
    
    context = {
        'empresas': empresas
    }
    return render(request, 'Alarmbar/new.html', context)

@login_required
def editView(request, alarmbar_id):
     item = AlarmBar.objects.get(id=alarmbar_id)
     empresas = Client.objects.filter(status=True)
     
     return render(request, 'Alarmbar/edit.html', {
         'item': item,
         'empresas': empresas
     })


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def editSaveAction(request, alarmbar_id):
    
    alarm = AlarmBar.objects.get(id=alarmbar_id)
    
    description = request.POST.get('description', None)
    
    wifi_ssid = request.POST.get('wifi_ssid', None)
    wifi_pswd = request.POST.get('wifi_pswd', None)

    wifi_ssid_automation = request.POST.get('wifi_ssid_automation', None)
    wifi_pswd_automation = request.POST.get('wifi_pswd_automation', None)

    tempo_disparo_seg = request.POST.get('tempo_disparo_seg', None)
    imu_task_ms = request.POST.get('imu_task_ms', None)
    group_str = request.POST.get('group', None)
    subgroup = request.POST.get('subgroup', None)

    min_pitch = request.POST.get('min_pitch', None)    
    max_pitch = request.POST.get('max_pitch', None)    
    min_roll = request.POST.get('min_roll', None)    
    max_roll = request.POST.get('max_roll', None)    
    min_yaw = request.POST.get('min_yaw', None)    
    max_yaw = request.POST.get('max_yaw', None)                    

    uctobroker = request.POST.get('uctobroker', None)                    
    brokertouc = request.POST.get('brokertouc', None)                

    imu_ativo = request.POST.get('imu_ativo', 0)                

    # Salvando os dados
    automation = alarm.automation
    automation.name = description
    automation.description = description    
    automation.save()

    group = alarm.alarm_bar_group_item.alarm_bar_group
    group.automation = automation
    group.descricao = group_str
    group.save()

    item = alarm.alarm_bar_group_item
    item.alarm_bar_group = group
    item.descricao = subgroup
    item.save()        
    
    alarm.wifi_ssid = wifi_ssid
    alarm.wifi_pswd = wifi_pswd
    alarm.wifi_ssid_local = wifi_ssid_automation
    alarm.wifi_pswd_local = wifi_pswd_automation
    alarm.mqtt_topic_broker_to_uc = brokertouc
    alarm.mqtt_topic_uc_to_broker = uctobroker
    alarm.imu_task_ms = imu_task_ms
    alarm.min_pitch = min_pitch
    alarm.max_pitch = max_pitch
    alarm.min_roll = min_roll
    alarm.max_roll = max_roll
    alarm.min_yaw = min_yaw
    alarm.max_yaw = max_yaw
    alarm.tempo_disparo_seg = tempo_disparo_seg
    alarm.imu_active = imu_ativo    
    alarm.updated_at = datetime.datetime.now()
    alarm.updated_by = request.user.id
    alarm.save()

    messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    return redirect('AlarmbarIndexView')

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def saveAction(request):                              

    client_id = request.POST.get('empresa', None)
    description = request.POST.get('description', None)
    wifi_ssid = request.POST.get('wifi_ssid', None)
    wifi_pswd = request.POST.get('wifi_pswd', None)

    wifi_ssid_automation = request.POST.get('wifi_ssid_automation', None)
    wifi_pswd_automation = request.POST.get('wifi_pswd_automation', None)

    tempo_disparo_seg = request.POST.get('tempo_disparo_seg', None)
    imu_task_ms = request.POST.get('imu_task_ms', None)
    group_str = request.POST.get('group', None)
    subgroup = request.POST.get('subgroup', None)

    min_pitch = request.POST.get('min_pitch', None)    
    max_pitch = request.POST.get('max_pitch', None)    
    min_roll = request.POST.get('min_roll', None)    
    max_roll = request.POST.get('max_roll', None)    
    min_yaw = request.POST.get('min_yaw', None)    
    max_yaw = request.POST.get('max_yaw', None)                    

    uctobroker = request.POST.get('uctobroker', None)                    
    brokertouc = request.POST.get('brokertouc', None)                

    imu_ativo = request.POST.get('imu_ativo', 0)                

    # Salvando os dados
    automation = Automation()
    automation.client = Client.objects.get(id=client_id)
    automation.automation_type = AutomationType.objects.get(id=11)
    automation.name = description
    automation.description = description
    automation.status = True
    automation.created_at = datetime.datetime.now()
    automation.created_by = request.user.id
    automation.save()

    group = AlarmBarGroup()
    group.automation = automation
    group.descricao = group_str
    group.save()

    item = AlarmBarGroupItem()
    item.alarm_bar_group = group
    item.descricao = subgroup
    item.save()

    alarm = AlarmBar()
    alarm.automation = automation
    alarm.alarm_bar_group_item = item
    alarm.wifi_ssid = wifi_ssid
    alarm.wifi_pswd = wifi_pswd
    alarm.wifi_ssid_local = wifi_ssid_automation
    alarm.wifi_pswd_local = wifi_pswd_automation
    alarm.mqtt_topic_broker_to_uc = brokertouc
    alarm.mqtt_topic_uc_to_broker = uctobroker
    alarm.imu_task_ms = imu_task_ms
    alarm.min_pitch = min_pitch
    alarm.max_pitch = max_pitch
    alarm.min_roll = min_roll
    alarm.max_roll = max_roll
    alarm.min_yaw = min_yaw
    alarm.max_yaw = max_yaw
    alarm.tempo_disparo_seg = tempo_disparo_seg
    alarm.imu_active = imu_ativo
    alarm.status = True
    alarm.created_at = datetime.datetime.now()
    alarm.created_by = request.user.id
    alarm.save()

    messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    return redirect('AlarmbarIndexView')

@login_required
def indexView(request):
    data = AlarmBar.objects.filter(status=True).order_by('-id')

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS        
    }

    return render(request, 'Alarmbar/index.html', context)

@login_required
def deleteAction(request, alarmbar_id):

    item = AlarmBar.objects.get(id=alarmbar_id)        

    try:
        item.delete()
        item.alarm_bar_group_item.delete()
        item.alarm_bar_group_item.alarm_bar_group.delete()
        messages.add_message(request, messages.SUCCESS, "Excluído com sucesso!")
    except Exception as e:
        messages.add_message(request, messages.ERROR, "Ocorreu esse erro: {}".format(e))


    context = {
        'status': 200,
        'descricao': 'Excluído com sucesso'
    }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")