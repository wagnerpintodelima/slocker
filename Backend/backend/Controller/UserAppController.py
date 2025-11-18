import datetime
import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from unicodedata import name

from django.core.paginator import Paginator  # 👈 PAGINAÇÃO

from backend.Controller.BaseController import saveFile
from backend.models import UserApp, UserAppAddress, Client
from slock.settings import DOMAIN_ASSETS

_PATH_FILE_USER_APP = 'backend/upload/user_app/'

@login_required
def indexView(request):
    # Query base
    qs = UserApp.objects.all().order_by('id')

    # Parâmetros de paginação pela URL (?page=2&per_page=25)
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except Exception:
        per_page = 10

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        'per_page': per_page,
        'DOMAIN_ASSETS': DOMAIN_ASSETS
    }
    return render(request, 'UserApp/index.html', context)

@login_required
def newView(request):
    condominios = Client.objects.filter(status=True)
    context = {
        'condominios': condominios,
    }
    return render(request, 'UserApp/new.html', context)

@login_required
def editView(request, user_app_id):
     item = UserApp.objects.get(id=user_app_id)
     condominios = Client.objects.filter(status=True)
     
     return render(request, 'UserApp/edit.html', {
         'item': item,
         'condominios': condominios,
         'DOMAIN_ASSETS': DOMAIN_ASSETS
     })

@login_required
def editAction(request, user_app_id):
    item = UserApp.objects.get(id=user_app_id)
    
    if item.user_app_address:
        address = UserAppAddress.objects.get(id=item.user_app_address.id)

    if request.method == 'POST' and item:
        nome = request.POST.get('name', None)
        signature = request.POST.get('signature', None)
        password = request.POST.get('password', None)
        hu = request.POST.get('hu', None)
        email = request.POST.get('email', None)
        cpf = request.POST.get('cpf', None)
        telefone = request.POST.get('telefone', None)
        cep = request.POST.get('cep', None)
        uf = request.POST.get('uf', None)
        cidade = request.POST.get('cidade', None)
        bairro = request.POST.get('bairro', None)
        rua = request.POST.get('rua', None)
        numero = request.POST.get('numero', None)
        observacao = request.POST.get('observacao', None)
        foto = None
        if 'foto' in request.FILES:
            foto = request.FILES['foto']
        status = request.POST.get('status', 0)

        if item.user_app_address:
            address.cep = cep
            address.uf_description = uf
            address.city = cidade
            address.neighborhood = bairro
            address.street = rua
            address.house_number = numero
            address.observation = observacao
            address.status = status
            address.updated_by = request.user.id
            address.updated_at = datetime.datetime.now()
            address.save()

        item.name = nome
        item.hu = hu
        item.password = password
        item.signature = signature
        item.email = email
        item.cpf = cpf
        item.phone_number = telefone
        item.updated_at = datetime.datetime.now()
        item.updated_by = request.user.id
        if foto:
            try:
                os.remove('media/' + _PATH_FILE_USER_APP + item.picture + '.png')
            except Exception as er:
                pass

            item.picture = saveFile(_PATH_FILE_USER_APP, 'png', foto)

        item.status = status
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro modificado com sucesso!')

    return redirect('UserAppIndexView')

@login_required
def saveAction(request):

    if request.method == 'POST':
        nome = request.POST.get('name', None)
        client_id = request.POST.get('client_id', None)
        client = Client.objects.get(id=client_id)
        hu = request.POST.get('hu', None)
        password = request.POST.get('password', None)
        signature = request.POST.get('signature', None)
        email = request.POST.get('email', None)
        cpf = request.POST.get('cpf', None)
        telefone = request.POST.get('telefone', None)
        cep = request.POST.get('cep', None)
        uf = request.POST.get('uf', None)
        bairro = request.POST.get('bairro', None)
        rua = request.POST.get('rua', None)
        numero = request.POST.get('numero', None)
        cidade = request.POST.get('cidade', None)
        observacao = request.POST.get('observacao', None)
        foto = request.FILES['foto']
        status = request.POST.get('status', 0)

        address = UserAppAddress()        
        address.title = 'UsuárioApp'
        address.cep = cep
        address.uf_description = uf
        address.city = cidade
        address.neighborhood = bairro
        address.street = rua
        address.house_number = numero
        address.observation = observacao
        address.status = status
        address.created_by = request.user.id
        address.created_at = datetime.datetime.now()
        address.save()

        item = UserApp()
        item.client = client
        item.hu = hu
        item.user_app_address = address
        item.name = nome
        item.password = password
        item.signature = signature
        item.email = email
        item.cpf = cpf
        item.phone_number = telefone
        item.created_at = datetime.datetime.now()
        item.created_by = request.user.id
        if foto:
            item.picture = saveFile(_PATH_FILE_USER_APP, 'png', foto)
        item.status = status
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    return redirect('UserAppIndexView')

@login_required
def deleteAction(request, user_app_id):

    item = UserApp.objects.get(id=user_app_id)

    try:
        os.remove('media/' + _PATH_FILE_USER_APP + item.picture + '.png')
    except Exception as er:
        messages.add_message(request, messages.ERROR, "Ocorreu esse erro ao tentar deletar a foto: {}".format(er))

    try:
        address = UserAppAddress.objects.get(id=item.user_app_address.id)
        item.delete()
        address.delete()
        messages.add_message(request, messages.SUCCESS, "Excluído com sucesso!")
    except Exception as e:
        messages.add_message(request, messages.ERROR, "Ocorreu esse erro: {}".format(e))

    context = {
        'status': 200,
        'descricao': 'Excluído com sucesso'
    }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
