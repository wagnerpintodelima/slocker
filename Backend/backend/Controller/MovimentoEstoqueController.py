import datetime
import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile, DateSTR2Datetime
from backend.models import MovimentoEstoque, TIPO_MOV_ESTOQUE_CHOICES, Produto, Client
from backend.models_views import SaldoEstoque
from django.views.decorators.http import require_http_methods
from backend.Controller.BaseController import doLog
from slock.settings import DOMAIN_ASSETS, BASE_DIR

_PATH_FILE_MAQUINA = 'backend/upload/maquina/'

@login_required
def indexView(request):
    data = MovimentoEstoque.objects.filter(status=True)    

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS        
    }

    return render(request, 'MovimentoEstoque/index.html', context)

@login_required
def newView(request):        
    
    context = {
        'produtos': Produto.objects.filter(status=True),
        'TIPO_MOV_ESTOQUE_CHOICES': TIPO_MOV_ESTOQUE_CHOICES
    }
    return render(request, 'MovimentoEstoque/new.html', context)

@require_http_methods(["POST"])
@login_required
def saveAction(request):            
    
    produto_id = int(request.POST.get('produto_id', None))
    tipo = request.POST.get('tipo', None)
    quantidade = int(request.POST.get('quantidade', None))
    descricao = request.POST.get('descricao', None)
    
    if produto_id == 0 or tipo == 0 or quantidade < 1 or not descricao:
        messages.add_message(request, messages.SUCCESS, 'Dados Inválidos!')            
        return redirect('MovimentoEstoqueIndexView')
    
    if tipo == 'ajuste_estoque' and not request.user.is_superuser :
        messages.add_message(request, messages.WARNING, 'Você não tem permissão para essa operação!')    
        doLog('+Movimento de Estoque', f'<b>@{request.user.first_name}</b> Tentou fazer um Ajuste de Estoque!', 0) # error
        return redirect('MovimentoEstoqueIndexView')
    
    produto = Produto.objects.get(id=produto_id)

    if tipo == 'ajuste_estoque':
        saldo_atual = SaldoEstoque.objects.get(produto_id=produto.id).saldo_atual

        diferenca = quantidade - saldo_atual
        quantidade = diferenca

        if diferenca == 0:
            messages.add_message(request, messages.SUCCESS, 'Não foi necessário Ajustes!')            
            return  # Não precisa ajustar
    
    item = MovimentoEstoque()    
    item.empresa = Client.objects.get(id=9) # Auten PRO    
    item.produto = produto
    item.tipo = tipo
    item.quantidade = quantidade
    item.descricao = descricao
    item.created_at = datetime.datetime.now()
    item.created_by = request.user.id
    item.status = True
    item.save()
    
    # Atualiza o produto
    produto.quantidade_em_estoque = SaldoEstoque.objects.get(produto_id=produto.id).saldo_atual
    produto.save()

    messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
    
    doLog('+Movimento de Estoque', f'<b>@{request.user.first_name}</b> fez uma {item.tipo} no produto {item.produto.descricao} na quantidade de {item.quantidade}.', 2) # info

    return redirect('MovimentoEstoqueIndexView')

@login_required
def deleteView(request, movimento_estoque_id):        
    
    item = MovimentoEstoque.objects.get(id=movimento_estoque_id)
    
    context = {
        'item': item
    }
    return render(request, 'MovimentoEstoque/delete.html', context)

@require_http_methods(["POST"])
@login_required
def deleteAction(request):

    movimento_estoque_id = int(request.POST.get('movimento_estoque_id', None))    
    item = MovimentoEstoque.objects.get(id=movimento_estoque_id)    
    descricao = request.POST.get('descricao', None)
    
    if not descricao:
        messages.add_message(request, messages.SUCCESS, "Você precisa informar o motivo!")
        return redirect('MovimentoEstoqueIndexView')
    
    try:        
        data_formatada = datetime.datetime.now().strftime('%d/%m/%Y %Hh:%Mm')
        item.descricao += f"\n\nMotivo da exclusão: {descricao}\nData da Exclusão: {data_formatada}. \nUsuário: {request.user.username}"
        item.status = False
        item.save()
        doLog('+Movimento de Estoque', f'<b>@{request.user.first_name}</b> excluiu o {item.produto.descricao}(ID:{item.id}).', 2) # info
        messages.add_message(request, messages.SUCCESS, "Excluído com sucesso!")
    except Exception as e:
        messages.add_message(request, messages.ERROR, "Ocorreu esse erro: {}".format(e))

    return redirect('MovimentoEstoqueIndexView')



