import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from backend.models import Automation, Client, HU, AutomationType
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos, generate_password
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone

@csrf_exempt
@require_http_methods(["POST"])
def setupAction(request):

    try:
        dados = json.loads(request.body.decode('utf-8'))

        mac = dados.get('mac', None)
        triggerLDR = dados.get('triggerLDR', None)
        timeOnLight = dados.get('timeOnLight', None)
        resetUC = dados.get('resetUC', None)

        topic = "wagner/api/setup"

        # Sincronizar os codes das checkouts
        packageMqtt = {
            'mac': mac,
            'trigger': triggerLDR,
            'tempo_ligado': timeOnLight,
            'reset': resetUC
        }

        mqttSendDataToDevice(json.dumps(packageMqtt), topic)

        # Fazer algo com o valor
        return JsonResponse({
            'status': 200,
            'description': 'Dados recebidos com sucesso',
            'operations': packageMqtt
        })

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")


@csrf_exempt
@require_http_methods(["POST"])
def sendCommandAction(request):    
             
    try:
        dados = json.loads(request.body.decode('utf-8'))

        mac = dados.get('mac', None)
        function = dados.get('function', None)
        turnOn = dados.get('turnOn', None)
        

        topic = "wagner/api/receiver"
        
        packageMqtt = {}   
        
        if function == 'light':
            packageMqtt = {
                'mac': mac,                        
                "relay": turnOn,
                "force_relay": turnOn,
                "alarme": True,
                "buzzer": True,
                "laser": True
            }   
        


        mqttSendDataToDevice(json.dumps(packageMqtt), topic)

        # Fazer algo com o valor
        return JsonResponse({
            'status': 200,
            'description': 'Dados recebidos com sucesso',
            'operations': packageMqtt
        })

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")