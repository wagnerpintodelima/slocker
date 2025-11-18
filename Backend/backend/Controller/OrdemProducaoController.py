import datetime
import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile, DateSTR2Datetime
from backend.models import Produto, CHOICE_STATUS_OP, Client, ProdutoComposto, ProdutoCompostoChild, OrdemProducao, OrdemProducaoChild, MovimentoEstoque
from django.views.decorators.http import require_http_methods
from backend.Controller.BaseController import doLog, str_to_datetime, formatar_data_hora
from slock.settings import DOMAIN_ASSETS, BASE_DIR
from django.db import transaction
from django.http import JsonResponse

_PATH_FILE_ANEXO = 'backend/upload/ordem/producao/'

@login_required
def indexView(request):

    data = OrdemProducao.objects.exclude(status='done')

    context = {
        'data': data,
        'DOMAIN_ASSETS': DOMAIN_ASSETS
    }

    return render(request, 'OrdemProducao/index.html', context)

@login_required
def newView(request):        

    context = {

    }

    return render(request, 'OrdemProducao/new.html', context)

@require_http_methods(["POST"])
@login_required
def saveAction(request):            

    empresa = Client.objects.get(id=9) # Auten PRO
    job = request.POST.get('job', None)
    data_inicio = request.POST.get('data_inicio', None)
    data_entrega = request.POST.get('data_entrega', None)
    anexo = request.FILES['anexo']

    item = OrdemProducao()
    item.empresa = empresa
    if anexo:
        item.anexo = saveFile(_PATH_FILE_ANEXO, 'png', anexo)   
    item.job = job
    item.data_inicio = str_to_datetime(data_inicio)
    item.data_entrega = str_to_datetime(data_entrega)
    item.created_by = request.user.id
    item.created_at = datetime.datetime.now()   
    item.save()

    messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    doLog('+OP', f'<b>@{request.user.first_name}</b> add uma Ordem de Serviço: {job}. Inicia em: {data_inicio} e Termina em {data_entrega}', 2) # info

    return redirect('OrdemProducaoIndexView')

@login_required
def editView(request, ordem_producao_id):
    
     item = OrdemProducao.objects.get(id=ordem_producao_id)     
     
     return render(request, 'OrdemProducao/edit.html', {
         'item': item,
         'DOMAIN_ASSETS': DOMAIN_ASSETS
     })

@login_required
@require_http_methods(["POST"])
def editAction(request, ordem_producao_id):

    item = OrdemProducao.objects.get(id=ordem_producao_id)    
        
    job = request.POST.get('job', None)
    data_inicio = request.POST.get('data_inicio', None)
    data_entrega = request.POST.get('data_entrega', None)  
    anexo = None
    if 'anexo' in request.FILES:
        anexo = request.FILES['anexo']
    
    item.job = job
    item.data_inicio = str_to_datetime(data_inicio)
    item.data_entrega = str_to_datetime(data_entrega)
    if anexo:
        item.anexo = saveFile(_PATH_FILE_ANEXO, 'png', anexo)    
    item.updated_by = request.user.id
    item.updated_at = datetime.datetime.now()
    item.save()
    
    
    messages.add_message(request, messages.SUCCESS, 'Registro modificado com sucesso!')
    doLog('+OP', f'<b>@{request.user.first_name}</b> Alterado uma Ordem de Serviço: {job}. Inicia em: {data_inicio} e Termina em {data_entrega}', 2) # info

    return redirect('OrdemProducaoIndexView')

@require_http_methods(["GET"])
@login_required
def deleteAction(request, ordem_producao_id):

    try:
        with transaction.atomic():                                    
            
            ordem_producao = OrdemProducao.objects.get(id=ordem_producao_id)
            ordem_producao.delete()
                        
            doLog('-Ordem Produção', f'<b>@{request.user.first_name}</b> <b>Excluiu a OP</b> #{ordem_producao.id}.', 0) # ERRO            
            
            messages.add_message(request, messages.SUCCESS, fr'Item removido com sucesso!')            
            return JsonResponse({
                'status': 200,
                'description': 'Item Excluído com sucesso'
            })
    except Exception as e:
        messages.add_message(request, messages.ERROR, fr'Ops! Você precisa excluir os itens dela antes!!!')
        return JsonResponse({
            'status': 500,
            'description': fr'Ops! Você precisa excluir os itens dela antes!!!'
        })
        return redirect('OrdemProducaoIndexView')

@login_required
def componentesView(request, ordem_producao_id):
    
     ordem_producao = OrdemProducao.objects.get(id=ordem_producao_id)
     produtos = Produto.objects.filter(status=True)      
     ordem_producao_child = OrdemProducaoChild.objects.filter(ordem_producao=ordem_producao).order_by('-produto__endereco')         
     
     return render(request, 'OrdemProducao/componentes.html', {
         'ordem_producao': ordem_producao,   
         'ordem_producao_composto_child': ordem_producao_child,
         'produtos': produtos,
         'DOMAIN_ASSETS': DOMAIN_ASSETS
     })

@require_http_methods(["POST"])
@login_required
def saveComponenteChildAction(request, ordem_producao_id):            
    
    try:
        with transaction.atomic():                                    
            
            produto = Produto.objects.get(id=request.POST.get('produto', None))
            quantidade = int(request.POST.get('quantidade', None))
            observacao = request.POST.get('observacao', False)
            
            if quantidade <= 0:
                messages.add_message(request, messages.SUCCESS, 'Quantidade deve ser maior que zero!')
                return redirect('OrdemProducaoComponentsView', ordem_producao_id)
            
            
            if produto.is_final: # Produto composto, Itera por cada produto filho, baixa estoque e gera ordem de produção item-a-item
                
                produto_composto = ProdutoComposto.objects.filter(produto_pai=produto).first()
                
                if produto_composto:
                    
                    produto_composto_child = ProdutoCompostoChild.objects.filter(produto_composto=produto_composto)
                    
                    for child in produto_composto_child:
                        createOP(request, ordem_producao_id, child.produto, int(child.quantidade * quantidade), child.observacao, fr'ORDEM DE PRODUÇÃO #{ordem_producao_id} - Composição {produto_composto.produto_pai.descricao}')
                    
                else:
                    messages.add_message(request, messages.ERROR, fr'Verifique o cadastro do produto composto código #{produto_composto.id}!')
                    return redirect('OrdemProducaoComponentsView', ordem_producao_id)
                
            else: # Produto Simples, gera baixa estoque ordem de producao 
                createOP(request, ordem_producao_id, produto, quantidade, observacao, fr'ORDEM DE PRODUÇÃO #{ordem_producao_id}')            
            

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            
            doLog('+Ordem Produção', f'<b>@{request.user.first_name}</b> <b>add</b> itens dentro <b>OP</b> #{ordem_producao_id}.', 2) # info

            return redirect('OrdemProducaoComponentsView', ordem_producao_id)
        
    except Exception as e:        
        messages.add_message(request, messages.ERROR, fr'Você preencheu todos os dados?? \n\nDescrição do erro:\n\n{str(e)}')
        return redirect('OrdemProducaoComponentsView', ordem_producao_id)

# Isso é usado para o próprio consumo dessa controller
def createOP(request, ordem_producao_id, produto, quantidade, observacao, descricao):        
    
    try:
        with transaction.atomic():        
            movimento_estoque = MovimentoEstoque.objects.create(                    
                produto = produto,
                empresa = Client.objects.get(id=9), # Auten PRO
                tipo = 'saida',
                quantidade = quantidade,
                descricao = descricao,
                status = True,
                created_at = datetime.datetime.now(),
                created_by = request.user.id
            )

            OrdemProducaoChild.objects.create( 
                ordem_producao = OrdemProducao.objects.get(id=ordem_producao_id),
                movimento_estoque = movimento_estoque,                                                                     
                produto = produto,
                quantidade = quantidade,
                observacao = observacao,
                created_at = datetime.datetime.now(),
                created_by = request.user.id
            )
            
            return True
    except Exception as e:        
        return False

@require_http_methods(["GET"])
@login_required
def deleteProdutoComponenteChild(request, ordem_producao_child_id):

    try:
        with transaction.atomic():                                    
            
            ordem_producao_child = OrdemProducaoChild.objects.get(id=ordem_producao_child_id)
            ordem_producao = ordem_producao_child.ordem_producao
            produto = ordem_producao_child.produto
            movimento_estoque = ordem_producao_child.movimento_estoque
            movimento_estoque.status = False
            movimento_estoque.save()
            
            ordem_producao_child.delete()
            
            doLog('-Ordem Produção', f'<b>@{request.user.first_name}</b> <b>removeu</b> o {produto.descricao} de dentro da <b>OP #{ordem_producao.id}.</b>', 0) # ERRO
            messages.add_message(request, messages.SUCCESS, fr'Item removido com sucesso!')            
            return redirect('OrdemProducaoComponentsView', ordem_producao.id)
    except Exception as e:
        messages.add_message(request, messages.ERROR, fr'Ops! erro:{str(e)}')
        return redirect('OrdemProducaoComponentsView', ordem_producao.id)

@require_http_methods(["GET"])
@login_required
def setStatusAction(request, ordem_producao_id, status):

    try:
        with transaction.atomic():                                    
            
            ordem_producao = OrdemProducao.objects.get(id=ordem_producao_id)
            status_current = ordem_producao.get_status_display()
            
            if status == 'separacao':
                status = 'producao_pendente'
            
            ordem_producao.status = status
            ordem_producao.save()
            status_new = ordem_producao.get_status_display()
            ordem_producao.job += f'\n\n<b>{formatar_data_hora()}</b> alterado o status de <b>{status_current}</b> para <b>{status_new}</b>.'
            ordem_producao.save()
            
            doLog('*Ordem Produção', f'<b>@{request.user.first_name}</b> <b>Setou</b> o status {status_new} da <b>OP #{ordem_producao.id}.</b>', 1) # Success
            messages.add_message(request, messages.SUCCESS, fr'Status alterado com sucesso! Parabéns campeão!!')            
            return redirect('OrdemProducaoIndexView')
    except Exception as e:
        messages.add_message(request, messages.ERROR, fr'Ops! erro:{str(e)}')
        return redirect('OrdemProducaoIndexView')




