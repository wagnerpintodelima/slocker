import datetime
import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile, DateSTR2Datetime
from backend.models import Maquina, MAQUINA_TIPO_CHOICES, MAQUINA_TIPO_PULSO_CHOICES
from django.views.decorators.http import require_http_methods
from backend.Controller.BaseController import doLog
from slock.settings import DOMAIN_ASSETS, BASE_DIR

_PATH_FILE_MAQUINA = 'backend/upload/maquina/'

@login_required
def indexView(request):
    data = Maquina.objects.all()    

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS        
    }

    return render(request, 'Maquina/index.html', context)

@login_required
def newView(request):        
    
    context = {
        'MAQUINA_TIPO_CHOICES': MAQUINA_TIPO_CHOICES,
        'MAQUINA_TIPO_PULSO_CHOICES': MAQUINA_TIPO_PULSO_CHOICES
    }
    return render(request, 'Maquina/new.html', context)

@require_http_methods(["POST"])
@login_required
def saveAction(request):            
    
    modelo = request.POST.get('modelo', None)
    tipo = request.POST.get('tipo', None)
    tipo_pulso = request.POST.get('tipo_pulso', None)
    usa_rele = request.POST.get('usa_rele', None)
    foto = request.FILES['foto']          
    observacao = request.POST.get('observacao', None)  
    status = request.POST.get('status', 1)

    item = Maquina()    
    item.modelo = modelo        
    if foto:
        item.foto = saveFile(_PATH_FILE_MAQUINA, 'png', foto)
    item.tipo = tipo
    item.tipo_pulso = tipo_pulso
    item.usa_rele = usa_rele
    item.observacao = observacao
    item.status = status
    item.created_at = datetime.datetime.now()
    item.created_by = request.user.id
    item.save()

    messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
    
    doLog('+MÁQUINA', f'<b>@{request.user.first_name}</b> add a máquina: {item.modelo} do tipo {item.get_tipo_display()}', 2) # info

    return redirect('MaquinaIndexView')

def editView(request, maquina_id):
     item = Maquina.objects.get(id=maquina_id)     
     
     return render(request, 'Maquina/edit.html', {
         'maquina': item,
         'MAQUINA_TIPO_CHOICES': MAQUINA_TIPO_CHOICES,
         'MAQUINA_TIPO_PULSO_CHOICES': MAQUINA_TIPO_PULSO_CHOICES
     })

@login_required
@require_http_methods(["POST"])
def editAction(request, maquina_id):
    
    item = Maquina.objects.get(id=maquina_id)
    
    modelo = request.POST.get('modelo', None)    
    tipo = request.POST.get('tipo', None)    
    tipo_pulso = request.POST.get('tipo_pulso', None)
    usa_rele = request.POST.get('usa_rele', None)
    observacao = request.POST.get('observacao', None)  
    status = request.POST.get('status', 1)                   
    foto = None
    if 'foto' in request.FILES:
        foto = request.FILES['foto']

    
    # Salvando    
    item.modelo = modelo        
    if foto:
        item.foto = saveFile(_PATH_FILE_MAQUINA, 'png', foto)
    item.tipo = tipo
    item.tipo_pulso = tipo_pulso
    item.usa_rele = usa_rele
    item.observacao = observacao
    item.status = status
    item.save()
    if foto:                        
        item.foto = saveFile(_PATH_FILE_MAQUINA, 'png', foto)    
        
    item.updated_at = datetime.datetime.now()
    item.updated_by = request.user.id        
    item.save()
    messages.add_message(request, messages.SUCCESS, 'Registro modificado com sucesso!')

    return redirect('MaquinaIndexView')

@login_required
def deleteAction(request, maquina_id):

    item = Maquina.objects.get(id=maquina_id)    
    
    try:
        path = os.path.join(BASE_DIR, 'media', _PATH_FILE_MAQUINA, item.foto + '.png')
        if os.path.exists(path):
            os.remove(path)
        else:
            messages.add_message(request, messages.ERROR, f"Arquivo não encontrado: {path}")
    except Exception as er:
        messages.add_message(request, messages.ERROR, "Ocorreu esse erro ao tentar deletar a foto: {}".format(er))

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