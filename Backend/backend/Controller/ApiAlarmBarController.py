import logging
import os
import locale
import json
import threading
import time
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
import pytz
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.models import HU, UserApp, AlarmBar, AlarmBarDisparo, Automation, AlarmBarGroup, AlarmBarGroupItem
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos, generate_password
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from backend.Controller.BaseController import print_dict, formatar_data_hora
from slock.settings import DOMAIN_ASSETS, BASE_DIR
from backend.Controller.UserAppController import _PATH_FILE_USER_APP


@csrf_exempt
@require_http_methods(["POST"])
def login(request):

    """
    Essa fn é executada em todos os apps, ela faz o login deles.
    É SUPER IMPORTANTE!!!
    """
    
    try:

        cpf = request.POST.get('cpf', None)
        password = request.POST.get('password', None)        

        userApp = UserApp.objects.filter(cpf=cpf, password=password).first()

        if userApp:

            # Definindo o locale para português do Brasil
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')                                                

            automation_ = Automation.objects.filter(client=userApp.client).first() # Uma automation tem vários alarm bar's

            alarm_bars = AlarmBar.objects.filter(automation=automation_)
            automacoes = []
            
            if alarm_bars.exists():
                
                groups_dict = {}

                groups_ = AlarmBarGroup.objects.filter(automation=automation_)

                for gp in groups_:
                    
                    itens_ = AlarmBarGroupItem.objects.filter(alarm_bar_group=gp)
                    
                    if gp.id not in groups_dict:
                        groups_dict[gp.id] = {
                            'id': gp.id,
                            'description': gp.descricao,
                            'items': []
                        }
                    
                    for it in itens_:
                        groups_dict[gp.id]['items'].append({
                            'id': it.id,
                            'description': it.descricao
                        })

                # converte para lista para usar no JSON
                groups = list(groups_dict.values())
                
                for alarmbar in alarm_bars:
                    automacoes.append({
                        'id': alarmbar.id,
                        'ui_mqtt': f'#id-mqtt-{alarmbar.id}',
                        'local': automation_.type_location,
                        'wifi_ssid': alarmbar.wifi_ssid,
                        'wifi_pswd': alarmbar.wifi_pswd,
                        'wifi_ssid_local': alarmbar.wifi_ssid_local,
                        'wifi_pswd_local': alarmbar.wifi_pswd_local,
                        'imu_task_ms': alarmbar.imu_task_ms,
                        'min_pitch': alarmbar.min_pitch,
                        'max_pitch': alarmbar.max_pitch,
                        'min_roll': alarmbar.min_roll,
                        'max_pitch': alarmbar.max_pitch,
                        'min_yaw': alarmbar.min_yaw,
                        'max_yaw': alarmbar.max_yaw,
                        'tempo_de_disparo_seg': alarmbar.tempo_disparo_seg,
                        'imu_active': alarmbar.imu_active,   
                        'mqtt_topic_uc_to_broker': alarmbar.mqtt_topic_uc_to_broker,
                        'mqtt_topic_broker_to_uc': alarmbar.mqtt_topic_broker_to_uc,   
                        'group_id': alarmbar.alarm_bar_group_item.alarm_bar_group.id,
                        'group_descricao': alarmbar.alarm_bar_group_item.alarm_bar_group.descricao,
                        'group_item_id': alarmbar.alarm_bar_group_item.id,
                        'group_item_descricao': alarmbar.alarm_bar_group_item.descricao,
                        'status': alarmbar.status
                    })
                
                return JsonResponse({
                    'status': 200,
                    'description': 'Acesso autorizado!',
                    'id': userApp.id,
                    'name': userApp.name,
                    'picture': f'{DOMAIN_ASSETS}/user_app/{userApp.picture}.png',
                    'statusCadastro': userApp.status,
                    'phone': userApp.phone_number,                                
                    'email': userApp.email,
                    'cpf': userApp.cpf,
                    'automations': automacoes,
                    'groups': groups
                })
            else: # Não tem nenhum alarm bar cadastrado
                return JsonResponse({
                    'status': 500,
                    'description': 'Seu login é válido, porém você precisa ter cadastrado ao menos um ALARM BAR no sistema de gestão!'
                })                        
            
        else:
            return JsonResponse({
              'status': 500,
                'description': 'O CPF ou a senha está errado! Fale com seu representante comercial e verifique os dados de acesso'
            })

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def sync(request):    
    
    try:
        
        package = json.loads(request.POST.get('package', None))        
        print_dict(package)
        
        alarmBAR = AlarmBar.objects.get(id=int(package['alarm_bar_id']))
        
        alarmBAR.min_pitch = int(package['min_pitch'])
        alarmBAR.max_pitch = int(package['max_pitch'])
        alarmBAR.min_roll = int(package['min_roll'])
        alarmBAR.max_roll = int(package['max_roll'])
        alarmBAR.min_yaw = int(package['min_yaw'])
        alarmBAR.max_yaw = int(package['max_yaw'])   
        
        alarmBAR.tempo_disparo_seg = int(package['tempo_de_disparo'])   
        
        alarmBAR.wifi_ssid = package['wifi_ssid']  
        alarmBAR.wifi_pswd = package['ssid_pswd']
        
        alarmBAR.wifi_ssid_local = package['wifi_ssid_local']  
        alarmBAR.wifi_pswd_local = package['wifi_pswd_local']   
        
        alarmBAR.mqtt_topic_uc_to_broker = package['uc_to_broker']  
        alarmBAR.mqtt_topic_broker_to_uc = package['broker_to_uc']     
        
        alarmBAR.updated_at = datetime.now()   
        
        alarmBAR.save()
        
        
        return JsonResponse({
            'status': 200,
            'description': 'Registro atualizado com sucesso!'            
        })

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def setStatus(request):    
    
    try:
        
        package = json.loads(request.POST.get('package', None))        
        print_dict(package)
        
        alarmBAR = AlarmBar.objects.get(id=int(package['alarm_bar_id']))        
        
        alarmBAR.imu_active = bool(package['imu_active'])
        
        alarmBAR.updated_at = datetime.now()   
        
        alarmBAR.save()
        
        
        return JsonResponse({
            'status': 200,
            'description': 'Registro atualizado com sucesso!'            
        })

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def history(request):    
    
    try:
        
        alarm_bar_id = request.POST.get('alarm_bar_id', None)        
        
        alarmBar = AlarmBar.objects.get(id=alarm_bar_id)

        if alarmBar:

            # Definindo o locale para português do Brasil
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')                                                

            disparos = AlarmBarDisparo.objects.filter(alarm_bar=alarmBar).order_by('-created_at')

            dados = []

            for disparo in disparos:                                                                
                
                dados.append({
                    'id': disparo.id,
                    'pitch': disparo.pitch,
                    'roll': disparo.roll,
                    'yaw': disparo.yaw,
                    'created_at': formatar_data_hora(disparo.created_at)
                })
                
            
            return JsonResponse({
                'status': 200,
                'description': 'Histórico concedido com sucesso!',                
                'history': dados
            })
            
        else:
            return JsonResponse({
              'status': 500,
                'description': 'Fale com seu gestor e verifique os dados de acesso'
            })

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

