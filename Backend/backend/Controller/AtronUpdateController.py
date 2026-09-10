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
from django.core import signing
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import get_valid_filename
from backend.models import AtronUpdate
from backend.Controller.BaseController import saveFile, deleteFile, downloadFile
from backend.Controller.ApiAtronController import existsToken
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
        apk = request.FILES.get('apk', None)
        status = request.POST.get('status', 0)

        if not apk:
            messages.add_message(request, messages.ERROR, 'APK é obrigatório!')
            return redirect('atronUpdateView')                                            
        
        file_name = get_valid_filename(apk.name).rsplit('.', 1)[0]

        item = AtronUpdate()
        item.version_current = version_current
        item.description = description
        item.level = level
        item.apk = saveFile(_PATH_FILE_APK, _FORMAT_FILE, apk, file_name)                
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
        status = request.POST.get('status', 0)        

        item = AtronUpdate.objects.get(id=atron_id)
        item.version_current = version_current
        item.description = description
        item.level = level
        deletedOldFile = False
        if apk:
            file_name = get_valid_filename(apk.name).rsplit('.', 1)[0]
            deletedOldFile = deleteFile(_PATH_FILE_APK, item.apk, _FORMAT_FILE)
            item.apk = saveFile(_PATH_FILE_APK, _FORMAT_FILE, apk, file_name)
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

@login_required
@require_http_methods(["GET"])
def downloadAPKAction(request, atron_id):
    item = get_object_or_404(AtronUpdate, id=atron_id)
    return downloadFile(_PATH_FILE_APK, item.apk, _FORMAT_FILE)

@login_required    
def habilitarDownloadSecurity(request):
    
    atron = AtronUpdate.objects.all().order_by('-id').first()
    atron.updated_at = datetime.datetime.now()
    atron.save()
    
    msg = f'<b>@{request.user.first_name}</b> Liberou o update do Atron por 10 minutos.'
    doLog('Atron Update', msg, 2) # info
    messages.add_message(request, messages.SUCCESS, strip_tags(msg))
    
    return redirect('indexView')
    
