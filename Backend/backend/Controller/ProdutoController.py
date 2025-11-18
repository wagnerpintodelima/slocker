import datetime
import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile, DateSTR2Datetime
from backend.models import Produto, TIPO_MOV_ESTOQUE_CHOICES, Client, ProdutoComposto, ProdutoCompostoChild
from django.views.decorators.http import require_http_methods
from backend.Controller.BaseController import doLog
from slock.settings import DOMAIN_ASSETS, BASE_DIR
from django.db import transaction

_PATH_FILE_PRODUTO = 'backend/upload/produto/'

@login_required
def indexView(request):
    data = Produto.objects.filter(status=True)

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS        
    }

    return render(request, 'Produto/index.html', context)

@login_required
def newView(request):        
    
    context = {
        
    }
    return render(request, 'Produto/new.html', context)

@require_http_methods(["POST"])
@login_required
def saveAction(request):            
    
    empresa = Client.objects.get(id=9) # Auten PRO
    codigo = request.POST.get('codigo', None)
    descricao = request.POST.get('descricao', None)
    quantidade_minima = request.POST.get('quantidade_minima', None)
    endereco = request.POST.get('endereco', None)
    link = request.POST.get('link', None)
    foto = request.FILES['foto']    
    is_final = request.POST.get('is_final', False)          

    item = Produto()    
    item.codigo = codigo
    item.empresa = empresa
    item.descricao = descricao        
    if foto:
        item.foto = saveFile(_PATH_FILE_PRODUTO, 'png', foto)    
    item.quantidade_minima = quantidade_minima
    item.endereco = endereco
    item.is_final = is_final
    item.link = link
    item.created_at = datetime.datetime.now()
    item.created_by = request.user.id
    item.save()
    
    if item.is_final:
        ProdutoComposto.objects.create(
            empresa = empresa,
            produto_pai = item,
            quantidade_elementos = 0,
            created_at = datetime.datetime.now(),
            created_by = item.created_by
        )

    messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
    
    doLog('+Produto', f'<b>@{request.user.first_name}</b> add um Produto: {item.descricao}.', 2) # info

    return redirect('ProdutoIndexView')

@login_required
def editView(request, produto_id):
     item = Produto.objects.get(id=produto_id)     
     
     return render(request, 'Produto/edit.html', {
         'item': item,
         'DOMAIN_ASSETS': DOMAIN_ASSETS
     })

@login_required
@require_http_methods(["POST"])
def editAction(request, produto_id):

    item = Produto.objects.get(id=produto_id)    

    codigo = request.POST.get('codigo', None)
    descricao = request.POST.get('descricao', None)
    quantidade_minima = request.POST.get('quantidade_minima', None)
    endereco = request.POST.get('endereco', None)
    link = request.POST.get('link', None)     
    # is_final = request.POST.get('is_final', False)                  
    foto = None
    if 'foto' in request.FILES:
        foto = request.FILES['foto']

    # Salvando        
    item.descricao = descricao
    item.codigo = codigo
    if foto:
        item.foto = saveFile(_PATH_FILE_PRODUTO, 'png', foto)    
    item.quantidade_minima = quantidade_minima
    item.endereco = endereco
    # item.is_final = is_final
    item.link = link
    item.updated_at = datetime.datetime.now()
    item.updated_by = request.user.id
    item.save()
    messages.add_message(request, messages.SUCCESS, 'Registro modificado com sucesso!')
    doLog('+Produto', f'<b>@{request.user.first_name}</b> editou um Produto: {item.descricao}.', 2) # info

    return redirect('ProdutoIndexView')

@login_required
def componentesView(request, produto_id):
     item = Produto.objects.get(id=produto_id)
     produto_composto = ProdutoComposto.objects.get(produto_pai=item)
     produto_composto_child = ProdutoCompostoChild.objects.filter(produto_composto=produto_composto)
     
     produtos = Produto.objects.filter(status=True, is_final=False)
     
     return render(request, 'Produto/componentes.html', {
         'pai': item,
         'produtoComposto': produto_composto,
         'produtos': produtos,
         'produto_composto_child': produto_composto_child,
         'DOMAIN_ASSETS': DOMAIN_ASSETS
     })

@require_http_methods(["POST"])
@login_required
def saveComponenteChildAction(request, produto_composto_id):            
    
    try:
        with transaction.atomic():
            produtoComposto = ProdutoComposto.objects.get(id=produto_composto_id)
            produto = Produto.objects.get(id=request.POST.get('produto', None))
            quantidade = float(request.POST.get('quantidade', None))
            observacao = request.POST.get('observacao', False)
            
            if quantidade <= 0:
                messages.add_message(request, messages.SUCCESS, 'Quantidade deve ser maior que zero!')
                return redirect('ProdutoComponentsView', produtoComposto.produto_pai.id)
            
            ProdutoCompostoChild.objects.create(
                produto_composto = produtoComposto,
                produto = produto,
                quantidade = quantidade,
                observacao = observacao,
                created_at = datetime.datetime.now(),
                created_by = request.user.id
            )

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            
            doLog('+Produto Composto', f'<b>@{request.user.first_name}</b> <b>add</b> um {produto.descricao} dentro do {produtoComposto.produto_pai.descricao}.', 2) # info

            return redirect('ProdutoComponentsView', produtoComposto.produto_pai.id)
    except Exception as e:        
        messages.add_message(request, messages.ERROR, fr'Você preencheu todos os dados?? \n\nDescrição do erro:\n\n{str(e)}')
        return redirect('ProdutoComponentsView', produtoComposto.produto_pai.id)

@require_http_methods(["GET"])
@login_required
def deleteProdutoComponenteChild(request, produto_composto_child_id):

    try:
        produto_composto_child = ProdutoCompostoChild.objects.get(id=produto_composto_child_id)
        produto = produto_composto_child.produto
        produto_pai = produto_composto_child.produto_composto.produto_pai
        produto_composto_child.delete()
        doLog('+Produto Composto', f'<b>@{request.user.first_name}</b> <b>removeu</b> o {produto.descricao} de dentro do {produto_pai.descricao}.', 2) # info
        messages.add_message(request, messages.SUCCESS, fr'Item removido com sucesso!')
        return redirect('ProdutoComponentsView', produto_pai.id)
    except Exception as e:
        messages.add_message(request, messages.ERROR, fr'Ops! erro:{str(e)}')
        return redirect('ProdutoComponentsView', produto_pai.id)

    
    
    
    
