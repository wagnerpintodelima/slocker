import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile, DateSTR2Datetime
from backend.models import Carro, Client
from slock.settings import DOMAIN_ASSETS, BASE_DIR

_PATH_FILE_CLIENT = 'backend/upload/carro/'

@login_required
def newView(request):
    
    empresas = Client.objects.filter(status=True)
    
    context = {
        'empresas': empresas
    }
    return render(request, 'Carro/new.html', context)

@login_required
def editView(request, carro_id):
     item = Carro.objects.get(id=carro_id)
     empresas = Client.objects.filter(status=True)
     
     return render(request, 'Carro/edit.html', {
         'carro': item,
         'empresas': empresas
     })

@login_required
def editAction(request, carro_id):
    
    item = Carro.objects.get(id=carro_id)

    if request.method == 'POST' and item:
        empresa = request.POST.get('empresa', None)        
        marca = request.POST.get('marca', None)
        modelo = request.POST.get('modelo', None)
        placa = request.POST.get('placa', None)
        km_proxima_troca_pneu = request.POST.get('km_proxima_troca_pneu', None)        
        km_proxima_troca_oleo = request.POST.get('km_proxima_troca_oleo', None)
        cor = request.POST.get('cor', None)
        ano = request.POST.get('ano', None)
        km_rodados = request.POST.get('km_rodados', None)
        observacao = request.POST.get('observacao', None)        
        foto = None
        if 'foto' in request.FILES:
            foto = request.FILES['foto']

        status = request.POST.get('status', 0)
        
        item.empresa = Client.objects.get(id=empresa)                
        item.marca = marca
        item.modelo = modelo
        item.placa = placa
        item.km_proxima_troca_oleo = km_proxima_troca_oleo
        item.km_proxima_troca_pneu = km_proxima_troca_pneu
        item.cor = cor
        item.ano = ano
        item.km_rodados = km_rodados
        item.observacao = observacao
        if foto:            
            try:
                path = os.path.join(BASE_DIR, 'media', _PATH_FILE_CLIENT, item.foto + '.png')
                if os.path.exists(path):
                    os.remove(path)
                else:
                    messages.add_message(request, messages.ERROR, f"Arquivo não encontrado: {path}") 
            except Exception as er:
                messages.add_message(request, messages.ERROR, "Ocorreu esse erro ao tentar deletar a foto: {}".format(er))
            
            item.foto = saveFile(_PATH_FILE_CLIENT, 'png', foto)
        item.status = status
        item.save()
        messages.add_message(request, messages.SUCCESS, 'Registro modificado com sucesso!')

    return redirect('CarroIndexView')

@login_required
def saveAction(request):

    if request.method == 'POST':
        
        empresa = request.POST.get('empresa', None)        
        marca = request.POST.get('marca', None)
        modelo = request.POST.get('modelo', None)
        placa = request.POST.get('placa', None)
        km_proxima_troca_pneu = request.POST.get('km_proxima_troca_pneu', None)        
        km_proxima_troca_oleo = request.POST.get('km_proxima_troca_oleo', None)
        cor = request.POST.get('cor', None)
        ano = request.POST.get('ano', None)
        km_rodados = request.POST.get('km_rodados', None)        
        observacao = request.POST.get('observacao', None)  
        foto = request.FILES['foto']      
        status = request.POST.get('status', 0)

        item = Carro()
        item.empresa = Client.objects.get(id=empresa)                
        item.marca = marca
        item.modelo = modelo
        item.placa = placa
        item.km_proxima_troca_oleo = km_proxima_troca_oleo
        item.km_proxima_troca_pneu = km_proxima_troca_pneu
        item.cor = cor
        item.ano = ano
        item.km_rodados = km_rodados
        item.observacao = observacao
        if foto:
            item.foto = saveFile(_PATH_FILE_CLIENT, 'png', foto)
        item.status = status
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    return redirect('CarroIndexView')

@login_required
def indexView(request):
    data = Carro.objects.all()    

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS        
    }

    return render(request, 'Carro/index.html', context)

@login_required
def deleteAction(request, carro_id):

    item = Carro.objects.get(id=carro_id)
    
    try:
        path = os.path.join(BASE_DIR, 'media', _PATH_FILE_CLIENT, item.foto + '.png')
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