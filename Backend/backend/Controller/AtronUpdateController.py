from django.utils import timezone
from datetime import timedelta
from django.utils.html import strip_tags
from backend.Controller.BaseController import doLog
import datetime
import json
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from backend.models import AtronUpdate
from backend.Controller.BaseController import saveFile, deleteFile, downloadFile
from django.core import serializers

_PATH_FILE_APK = 'backend/upload/atron/update/apk/'
_FORMAT_FILE = 'zip'

@login_required
def indexView(request):
    data = AtronUpdate.objects.order_by('-id')        

    context = {
        'data': data
    }

    return render(request, 'AtronUpdate/index.html', context)

@login_required
def newView(request):

    itens = AtronUpdate.objects.filter(status=True).order_by('id')

    lastVersion = 'v1.0.0'
    if len(itens) > 0:
        lastVersion = itens[0].version_current
    
    
    context = {
        'itens': itens,
        'lastVersion': lastVersion
    }
    return render(request, 'AtronUpdate/new.html', context)

@login_required
def SaveAction(request):

    if request.method == 'POST':
        version_current = request.POST.get('version_current', None)
        description = request.POST.get('description', None)
        level = request.POST.get('level', None)                        
        apk = request.FILES['apk']           
        status = request.POST.get('status', 0)

        if not apk:
            messages.add_message(request, messages.ERROR, 'APK é obrigatório!')
            return redirect('atronUpdateView')                                            

        item = AtronUpdate()
        item.version_current = version_current
        item.description = description
        item.level = level
        item.apk = saveFile(_PATH_FILE_APK, _FORMAT_FILE, apk)                
        item.status = status
        item.created_by = request.user.id
        item.created_at = datetime.datetime.now()
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    return redirect('atronUpdateView')

@login_required
def editView(request, atron_id):

    item = AtronUpdate.objects.get(id=atron_id)    

    context = {
        'item': item
    }

    return render(request, 'AtronUpdate/edit.html', context)

@login_required
def editAction(request):

    if request.method == 'POST':
        atron_id = request.POST.get('atron_id', None)
        version_current = request.POST.get('version_current', None)
        description = request.POST.get('description', None)
        level = request.POST.get('level', None)                        
        # Verifica se o arquivo 'apk' foi enviado
        apk = request.FILES.get('apk', None)
        if apk:            
            apk = request.FILES['apk']
        status = request.POST.get('status', 0)        

        item = AtronUpdate.objects.get(id=atron_id)
        item.version_current = version_current
        item.description = description
        item.level = level
        deletedOldFile = False
        if apk:
            deletedOldFile = deleteFile(_PATH_FILE_APK, item.apk, _FORMAT_FILE)
            item.apk = saveFile(_PATH_FILE_APK, 'zip', apk)
        item.status = status
        item.updated_by = request.user.id
        item.updated_at = datetime.datetime.now()
        item.save()
        
        if deletedOldFile:
            messages.add_message(request, messages.SUCCESS, "Registro atualizado com sucesso com troca de APK's!")
        else:
            messages.add_message(request, messages.SUCCESS, 'Registro atualizado com sucesso!')

    return redirect('atronUpdateView')

@login_required
def deleteAction(request, atron_id):

    try:
        item = AtronUpdate.objects.get(id=int(atron_id))
        
        deletedOldFile = deleteFile(_PATH_FILE_APK, item.apk, _FORMAT_FILE)
        
        item.delete()

        context = {
            'status': 200,
            'descricao': 'Excluído com sucesso' if not deletedOldFile else 'Excluído registro e arquivo com sucesso!'
        }
    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

def downloadAPKAction(request, atron_id):
    
    # Verificar se está liberada
    atron = AtronUpdate.objects.all().order_by('-id').first()
    if timezone.now() - atron.updated_at > timedelta(minutes=10):
        doLog('Atron Update', fr'Houve uma tentativa de download da APK do Atron sem liberar no sistema', 0) # error
        return redirect('https://autenpro.com.br/')

    try:  
        item = AtronUpdate.objects.get(id=atron_id)
        response = downloadFile(_PATH_FILE_APK, item.apk, _FORMAT_FILE)
        return response
    
    except Exception as e:
        messages.add_message(request, messages.ERROR, 'Não há essa APK no servidor, verificar se não foi "upada" no localhost!')
        return redirect('atronUpdateView')

@login_required    
def habilitarDownloadSecurity(request):
    
    atron = AtronUpdate.objects.all().order_by('-id').first()
    atron.updated_at = datetime.datetime.now()
    atron.save()
    
    msg = f'<b>@{request.user.first_name}</b> Liberou o update do Atron por 10 minutos.'
    doLog('Atron Update', msg, 2) # info
    messages.add_message(request, messages.SUCCESS, strip_tags(msg))
    
    return redirect('indexView')
    