import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile
from backend.models import Tecnico, Client
from slock.settings import DOMAIN_ASSETS, BASE_DIR
import datetime

_PATH_FILE_TECNICO = 'backend/upload/tecnico/auten/'

@login_required
def newView(request):
    context = {}
    return render(request, 'Tecnico/new.html', context)

@login_required
def editView(request, tecnico_id):
     item = Tecnico.objects.get(id=tecnico_id)
     return render(request, 'Tecnico/edit.html', {
         'item': item
     })

@login_required
def editAction(request, tecnico_id):
    
    item = Tecnico.objects.get(id=tecnico_id)

    if request.method == 'POST' and item:
        
        nome = request.POST.get('nome', None)
        telefone = request.POST.get('telefone', None)
        observacao = request.POST.get('observacao', None)
        status = request.POST.get('status', 0)
        foto = None
        if 'foto' in request.FILES:
            foto = request.FILES['foto']
        
        item.nome = nome         
        item.telefone = telefone       
        if foto:
            try:
                path = os.path.join(BASE_DIR, 'media', _PATH_FILE_TECNICO, item.foto + '.png')
                if os.path.exists(path):
                    os.remove(path)
                else:
                    messages.add_message(request, messages.ERROR, f"Arquivo não encontrado: {path}")
                
            except Exception as er:
                messages.add_message(request, messages.ERROR, "Ocorreu esse erro ao tentar deletar a foto: {}".format(er))
            
            item.foto = saveFile(_PATH_FILE_TECNICO, 'png', foto)
        item.observacao = observacao   
        item.updated_by = request.user.id
        item.updated_at = datetime.datetime.now()     
        item.status = status
        item.save()
        messages.add_message(request, messages.SUCCESS, 'Registro modificado com sucesso!')

    return redirect('TecnicoIndexView')

@login_required
def saveAction(request):

    if request.method == 'POST':
        
        nome = request.POST.get('nome', None)        
        telefone = request.POST.get('telefone', None)        
        observacao = request.POST.get('observacao', None)        
        status = request.POST.get('status', 0)
        foto = None
        if 'foto' in request.FILES:
            foto = request.FILES['foto']
        

        item = Tecnico()
        item.empresa = Client.objects.get(id=9) # Auten PRO
        item.nome = nome 
        item.telefone = telefone               
        if foto:            
            try:
                item.foto = saveFile(_PATH_FILE_TECNICO, 'png', foto)
            except Exception as er:
                messages.add_message(request, messages.ERROR, "Ocorreu esse erro ao tentar deletar a foto: {}".format(er))                        
        item.observacao = observacao        
        item.status = status
        item.created_by = request.user.id
        item.created_at = datetime.datetime.now()
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    return redirect('TecnicoIndexView')

@login_required
def indexView(request):
    data = Tecnico.objects.all()    

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS
    }

    return render(request, 'Tecnico/index.html', context)

@login_required
def deleteAction(request, tecnico_id):

    item = Tecnico.objects.get(id=tecnico_id)    
    
    try:                
        path = os.path.join(BASE_DIR, 'media', _PATH_FILE_TECNICO, item.foto + '.png')
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