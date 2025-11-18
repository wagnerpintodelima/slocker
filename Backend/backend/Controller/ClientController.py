import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile
from backend.models import Client
from slock.settings import DOMAIN_ASSETS, BASE_DIR
from backend.Controller.BaseController import doLog


_PATH_FILE_CLIENT = 'backend/upload/client/'

@login_required
def newView(request):
    context = {}
    return render(request, 'Client/new.html', context)

@login_required
def editView(request, client_id):
     item = Client.objects.get(id=client_id)
     return render(request, 'Client/edit.html', {
         'item': item
     })

@login_required
def editAction(request, client_id):
    item = Client.objects.get(id=client_id)

    if request.method == 'POST' and item:
        razaoSocial = request.POST.get('razaoSocial', None)
        nomeFantasia = request.POST.get('nomeFantasia', None)
        email = request.POST.get('email', None)
        cnpj = request.POST.get('cnpj', None)
        telefone = request.POST.get('telefone', None)
        cep = request.POST.get('cep', None)
        uf = request.POST.get('uf', 0)
        bairro = request.POST.get('bairro', None)
        rua = request.POST.get('rua', None)
        numero = request.POST.get('numero', None)
        cidade = request.POST.get('cidade', None)
        observacao = request.POST.get('observacao', None)
        status = request.POST.get('status', 0)

        item.razao_social = razaoSocial
        item.nome_fantasia = nomeFantasia
        item.email = email
        item.cpf_cnpj = cnpj
        item.phone_number = telefone
        item.cep = cep
        item.uf = uf
        item.neighborhood = bairro
        item.street = rua
        item.house_number = numero
        item.city = cidade
        item.observation = observacao
        item.status = status
        item.save()
        messages.add_message(request, messages.SUCCESS, 'Registro modificado com sucesso!')                

    return redirect('ClientIndexView')

@login_required
def saveAction(request):

    if request.method == 'POST':
        razaoSocial = request.POST.get('razaoSocial', None)
        nomeFantasia = request.POST.get('nomeFantasia', None)
        email = request.POST.get('email', None)
        cnpj = request.POST.get('cnpj', None)
        telefone = request.POST.get('telefone', None)
        cep = request.POST.get('cep', None)
        uf = request.POST.get('uf', 0)
        bairro = request.POST.get('bairro', None)
        rua = request.POST.get('rua', None)
        numero = request.POST.get('numero', None)
        cidade = request.POST.get('cidade', None)
        observacao = request.POST.get('observacao', None)
        logo = request.FILES['logo']
        banner = request.FILES['banner']
        status = request.POST.get('status', 0)

        item = Client()
        item.razao_social = razaoSocial
        item.nome_fantasia = nomeFantasia
        item.email = email
        item.cpf_cnpj = cnpj
        item.phone_number = telefone
        item.cep = cep
        item.uf = uf
        item.neighborhood = bairro
        item.street = rua
        item.house_number = numero
        item.city = cidade
        item.observation = observacao
        if logo:
            item.logo = saveFile(_PATH_FILE_CLIENT, 'png', logo)
        if banner:
            item.picture = saveFile(_PATH_FILE_CLIENT, 'png', banner)
        item.status = status
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    return redirect('ClientIndexView')

def indexView(request):
    data = Client.objects.all()

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS
    }

    return render(request, 'Client/index.html', context)

@login_required
def deleteAction(request, client_id):

    item = Client.objects.get(id=client_id)

    try:                
        path = os.path.join(BASE_DIR, 'media', _PATH_FILE_CLIENT, item.foto + '.png')
        if os.path.exists(path):
            os.remove(path)
        else:
            messages.add_message(request, messages.ERROR, f"Arquivo não encontrado: {path}") 
        
    except Exception as er:
        messages.add_message(request, messages.ERROR, "Ocorreu esse erro ao tentar deletar a logo: {}".format(er))

    try:
        os.remove(_PATH_FILE_CLIENT + item.picture)
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