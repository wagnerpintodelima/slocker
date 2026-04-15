import json
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
import pytz
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core import signing
from backend.models import Automation, HU, AtronDeviceRegister, Slot, AtronUpdate, AtronDevice, AtronDownload
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos, generate_password
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from backend.Controller.BaseController import getHash
from backend.Controller.BaseController import downloadFile

_PATH_FILE_APK = 'backend/upload/atron/update/apk/'
_FORMAT_FILE = 'zip'
_CHECKSUM_ALGORITHM = 'sha256'

def get_last_update_checksum():
    item = AtronUpdate.objects.order_by('-id').first()

    if not item:
        return None, None

    file_path = os.path.join(settings.MEDIA_ROOT, _PATH_FILE_APK, f'{item.apk}.{_FORMAT_FILE}')

    if not os.path.exists(file_path):
        return item, None

    hash_value = hashlib.sha256()
    with open(file_path, 'rb') as apk_file:
        for chunk in iter(lambda: apk_file.read(1024 * 1024), b''):
            hash_value.update(chunk)

    return item, hash_value.hexdigest()

@csrf_exempt
@require_http_methods(["POST"])
def new(request):

    try:
        dados = json.loads(request.body.decode('utf-8'))
        authorization_header = request.headers.get('Authorization', None)
        
        if authorization_header != getHash():
            # Fazer algo com o valor
            return JsonResponse({
                'status': 403,
                'description': r"Forbidden! Be careful, we know where you are!"
            })


        # Acessando um valor específico | {"deviceNumber":"cf916da6509da698be4854f789b26c01","version": "v4.3.2"}
        deviceNumber = dados.get('deviceNumber', None)
        version = dados.get('version', None)        
        
        if len(deviceNumber) != 32:
            return JsonResponse({
                'status': 500,
                'description': r"Device number not has length correctly of digits."
            })
        
        if not deviceNumber or not version:
            return JsonResponse({
                'status': 400,
                'description': r"Mandatory parameters are missing"
            })
            
        existThisDeviceInBd = AtronDeviceRegister.objects.filter(device_number=deviceNumber).count()
        if existThisDeviceInBd:
            return JsonResponse({
                'status': 400,
                'description': r"Repeated device"
            })
            
        item = AtronDeviceRegister()
        item.device_number = deviceNumber
        item.version_current = version     
        item.status = 1 # Disponível   
        item.created_by = 0
        item.created_at = datetime.now()
        item.save()

        # Fazer algo com o valor
        return JsonResponse({
            'status': 200,
            'description': 'Dados recebidos com sucesso'
        })

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def handshake(request):

    try:
        dados = json.loads(request.body.decode('utf-8'))
        authorization_header = request.headers.get('Authorization', None)
        
        if authorization_header != getHash():
            # Fazer algo com o valor
            return JsonResponse({
                'status': 403,
                'description': r"Forbidden! Be careful, we know where you are!"
            })


        # Acessando um valor específico | {"deviceNumber":"cf916da6509da698be4854f789b26c01","version":"v4.3.2"}
        deviceNumber = dados.get('deviceNumber', None)
        version = dados.get('version', None)
        lat = dados.get('lat', None)
        lon = dados.get('lon', None)

        if not deviceNumber or not version or not lat or not lon:
            return JsonResponse({
                'status': 400,
                'description': r"Mandatory parameters are missing"
            })
        
        try:
            
            atronDevice = AtronDevice.objects.get(atron_device_register__device_number=deviceNumber)  
            atronDevice.version_current = version
            atronDevice.save()       
            
            atronDevice.atron_device_register.lat = lat
            atronDevice.atron_device_register.lon = lon
            atronDevice.atron_device_register.save()   
            
            if atronDevice.status == 0:
                return JsonResponse({
                    'status': 2,
                    'description': f"Deactived"
                })
            
            atronUpdateLastVersion = AtronUpdate.objects.filter(status=1).order_by('-id').first()

            
            version_in_gps = version_to_number(version)
            version_in_server = version_to_number(atronUpdateLastVersion.version_current)
            
            if version_in_server > version_in_gps:
                
                if atronUpdateLastVersion.level == 0:
                    status = 3 # Deprecated
                elif atronUpdateLastVersion.level == 1:
                    status = 4 # DeprecatedUrgent
                else:                    
                    status = 5 # ForceUpdate
                    
                return JsonResponse({
                    'status': status,
                    'description': fr'Há atualização disponível para seu Agroline. Atualmente você está na versão: {version} e o sistema já evoluiu para a versão: {atronUpdateLastVersion.version_current}'
                })
            
            return JsonResponse({
                'status': 1,
                'description': f"Actived"
            })
            
            
            
            
        except AtronDevice.DoesNotExist:
            return JsonResponse({
                'status': 404,
                'description': r"Not Found!"
            })                                                    

    except Exception as e:
        context = {
            'status': 0,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
def showHash(request):
    
    context = {
        'hash': getHash()
    }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

def existsToken(deviceNumber, token):
    
    valid_since = timezone.now() - timedelta(minutes=10)
    
    if not token:
        return AtronDownload.objects.filter(
            device_number=deviceNumber,
            created_at__gte=valid_since
        ).order_by('-created_at').first() or False
    
    else:
        return AtronDownload.objects.filter(
            device_number=deviceNumber,
            token=token,
            created_at__gte=valid_since
        ).order_by('-created_at').first() or False

@csrf_exempt
def token(request):
    
    try:
        dados = json.loads(request.body.decode('utf-8'))
        authorization_header = request.headers.get('Authorization', None)
        
        if authorization_header != getHash():
            # Fazer algo com o valor
            return JsonResponse({
                'status': 403,
                'description': r"Forbidden! Be careful, we know where you are!"
            })

        # Acessando um valor específico | {"deviceNumber":"cf916da6509da698be4854f789b26c01","version":"v4.3.2"}
        deviceNumber = dados.get('deviceNumber', None)        
        lat = dados.get('lat', None)
        lon = dados.get('lon', None)

        if not deviceNumber or not lat or not lon:
            return JsonResponse({
                'status': 400,
                'description': r"Mandatory parameters are missing"
            })
        
        try:
            
            atronDevice = AtronDevice.objects.get(atron_device_register__device_number=deviceNumber)                          
            # Atualiza a latitude e longitude do dispositivo
            atronDevice.atron_device_register.lat = lat
            atronDevice.atron_device_register.lon = lon
            atronDevice.atron_device_register.save()   
            
            if atronDevice.status == 0:
                return JsonResponse({
                    'status': 2,
                    'description': f"Deactived"
                })                        
            
            # Verificar se já existe um token válido para esse dispositivo
            lastUpdate, apkChecksum = get_last_update_checksum()
            if not lastUpdate:
                return JsonResponse({
                    'status': 404,
                    'description': r"Update file not found."
                })

            if not apkChecksum:
                return JsonResponse({
                    'status': 404,
                    'description': r"Update file does not exist."
                })

            existingToken = existsToken(deviceNumber, token=None)
            if existingToken:
                return JsonResponse({
                    'status': 3,
                    'token': existingToken.token,
                    'checksum': apkChecksum,
                    'checksum_algorithm': _CHECKSUM_ALGORITHM,
                    'description': f"Download token already exists. Please use the existing token to download the APK."
                })
            
            AgrolineDownload = AtronDownload()
            AgrolineDownload.device_number = deviceNumber
            AgrolineDownload.token = secrets.token_urlsafe(32)
            AgrolineDownload.created_at = datetime.now()
            AgrolineDownload.save()

            return JsonResponse({
                'status': 1,
                'token': AgrolineDownload.token,
                'checksum': apkChecksum,
                'checksum_algorithm': _CHECKSUM_ALGORITHM,
                'description': f"Download token generated successfully. Use this token to download the APK."
            })
            
        except AtronDevice.DoesNotExist:
            return JsonResponse({
                'status': 404,
                'description': r"Not Found!"
            })                                                    

    except Exception as e:
        context = {
            'status': 0,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
def download(request):
    
    try:
        dados = json.loads(request.body.decode('utf-8'))
        authorization_header = request.headers.get('Authorization', None)
        token = request.headers.get('Token', None)
        
        if authorization_header != getHash():
            # Fazer algo com o valor
            return JsonResponse({
                'status': 403,
                'description': r"Forbidden! Be careful, we know where you are!"
            })
            
        if not token:
            return JsonResponse({
                'status': 400,
                'description': r"Mandatory parameters are missing"
            })                    

        # Acessando um valor específico | {"deviceNumber":"cf916da6509da698be4854f789b26c01","version":"v4.3.2"}
        deviceNumber = dados.get('deviceNumber', None)        
        lat = dados.get('lat', None)
        lon = dados.get('lon', None)

        if not deviceNumber or not lat or not lon:
            return JsonResponse({
                'status': 400,
                'description': r"Mandatory parameters are missing"
            })
        
        try:
            
            if not existsToken(deviceNumber=deviceNumber, token=token):
                return JsonResponse({
                    'status': 403,
                    'description': r"Forbidden! Invalid token."
                })
            else:
                item = AtronUpdate.objects.order_by('-id').first()
                response = downloadFile(_PATH_FILE_APK, item.apk, _FORMAT_FILE)
                return response
            
        except AtronDevice.DoesNotExist:
            return JsonResponse({
                'status': 404,
                'description': r"Not Found!"
            })                                                    

    except Exception as e:
        context = {
            'status': 0,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

def version_to_number(version_str):
    # Remove o 'v' da string de versão e separa os números por '.'
    version_parts = version_str.lstrip('v').split('.')
    
    # Junta os números e converte para inteiro
    version_number = int(''.join(version_parts))
    
    return version_number

