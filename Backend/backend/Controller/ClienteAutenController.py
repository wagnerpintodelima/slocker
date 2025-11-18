import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile
from backend.models import ClienteAuten
from slock.settings import DOMAIN_ASSETS, BASE_DIR
from backend.Controller.BaseController import doLog
import datetime

_PATH_FILE_CLIENT = 'backend/upload/client/auten/'

@login_required
def newView(request):
    context = {}
    return render(request, 'ClienteAuten/new.html', context)

@login_required
def editView(request, client_auten_id):
     item = ClienteAuten.objects.get(id=client_auten_id)
     return render(request, 'ClienteAuten/edit.html', {
         'item': item
     })

@login_required
def editAction(request, client_auten_id):
    
    item = ClienteAuten.objects.get(id=client_auten_id)

    if request.method == 'POST' and item:
        nome = request.POST.get('nome', None)        
        cpf_cnpj = request.POST.get('cpf_cnpj', None)
        telefone = request.POST.get('telefone', None)
        cep = request.POST.get('cep', None)
        uf = request.POST.get('uf', 0)        
        cidade = request.POST.get('cidade', None)
        endereco = request.POST.get('endereco', None)
        numero = request.POST.get('numero', None)
        observacao_endereco = request.POST.get('observacao_endereco', None)        
        link_gps = request.POST.get('link_gps', None)        
        status = request.POST.get('status', 0)
        
        item.nome = nome                
        item.cpf_cnpj = cpf_cnpj
        item.telefone = telefone
        item.cep = cep
        item.uf = uf        
        item.numero = numero
        item.cidade = cidade
        item.endereco = endereco
        item.link_gps = link_gps
        item.observacao_endereco = observacao_endereco        
        item.status = status
        item.updated_by = request.user.id
        item.updated_at = datetime.datetime.now()
        item.save()
        messages.add_message(request, messages.SUCCESS, 'Registro modificado com sucesso!')
        
        doLog('edit Cliente', f'<b>@{request.user.first_name}</b> Editou o cliente {item.nome}', 2) # info

    return redirect('ClienteAutenIndexView')

@login_required
def saveAction(request):

    if request.method == 'POST':
        
        nome = request.POST.get('nome', None)        
        cpf_cnpj = request.POST.get('cpf_cnpj', None)
        telefone = request.POST.get('telefone', None)
        cep = request.POST.get('cep', None)
        uf = request.POST.get('uf', 0)        
        cidade = request.POST.get('cidade', None)
        endereco = request.POST.get('endereco', None)
        numero = request.POST.get('numero', None)
        observacao_endereco = request.POST.get('observacao_endereco', None)        
        link_gps = request.POST.get('link_gps', None)        
        status = request.POST.get('status', 0)

        item = ClienteAuten()
        item.nome = nome                
        item.cpf_cnpj = cpf_cnpj
        item.telefone = telefone
        item.cep = cep
        item.uf = uf        
        item.numero = numero
        item.cidade = cidade
        item.endereco = endereco
        item.link_gps = link_gps
        item.observacao_endereco = observacao_endereco        
        item.status = status
        item.created_at = datetime.datetime.now()
        item.created_by = request.user.id
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
        
        doLog('Save Cliente', f'<b>@{request.user.first_name}</b> CRIOU o cliente {item.nome}', 1) # success

    return redirect('ClienteAutenIndexView')

@login_required
def indexView(request):
    data = ClienteAuten.objects.all()

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS
    }

    return render(request, 'ClienteAuten/index.html', context)

@login_required
def deleteAction(request, client_auten_id):

    item = ClienteAuten.objects.get(id=client_auten_id)   
    
    try:            
        path = os.path.join(BASE_DIR, 'media', _PATH_FILE_CLIENT, item.foto + '.png')
        if os.path.exists(path):
            os.remove(path)
        else:
            messages.add_message(request, messages.ERROR, f"Arquivo não encontrado: {path}")         
    except Exception as er:
        messages.add_message(request, messages.ERROR, "Ocorreu esse erro ao tentar deletar a logo: {}".format(er))            

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