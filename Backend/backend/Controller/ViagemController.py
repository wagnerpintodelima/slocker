from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
import datetime
from django.utils import timezone
import json
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from backend.models import Viagem, ClienteAuten, Automation, AutomationType, Client, Carro, Tecnico, PosVenda, ViagemInstalacao, ViagemInstalacaoKit, ViagemInstalacaoKitChild, STATUS_CHOICES
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers
from django.db import transaction
from backend.Controller.BaseController import str_to_datetime
from backend.Controller.BaseController import doLog

@login_required
def indexView(request):

    # Inicia o QuerySet com todos os registros
    viagens = Viagem.objects.all()

    # Obtém os filtros via GET
    tecnico = request.GET.get('tecnico')
    cliente = request.GET.get('cliente')
    status = request.GET.get('status')
    data = request.GET.get('data')

    # Aplica os filtros se os parâmetros estiverem presentes
    if tecnico:
        viagens = viagens.filter(tecnico=Tecnico.objects.get(id=tecnico))
    if cliente:
        viagens = viagens.filter(cliente_auten=ClienteAuten.objects.get(id=cliente))    
    if status:
        if status == '-2': # Agendado + Em viagem (0 + 2)
            viagens = viagens.filter(Q(status=0) | Q(status=2))
        else:
            viagens = viagens.filter(status=status)            
    if data:
        today = timezone.now()

        if data == '1':
            date_limit = today - timedelta(days=90)
        elif data == '2':
            date_limit = today - timedelta(days=60)
        elif data == '3':
            date_limit = today - timedelta(days=30)
        
        viagens = viagens.filter(data_saida_prevista__gte=date_limit)

    # Ordena os registros conforme a data do chamado
    viagens = viagens.order_by('created_at')    

    context = {
        'data': viagens
    }

    return render(request, 'Viagem/index.html', context)

@login_required
def newView(request):    

    clients = ClienteAuten.objects.filter(status=True).order_by('nome')
    carros = Carro.objects.filter(status=True).order_by('modelo')
    tecnicos = Tecnico.objects.filter(status=True).order_by('nome')

    context = {        
        'empresas': clients,
        'carros': carros,
        'tecnicos': tecnicos
    }

    return render(request, 'Viagem/new.html', context)

@login_required
@require_http_methods(["POST"])
def saveAction(request):
    
    try:
        with transaction.atomic():
            
            empresa = Client.objects.get(id=9)
            cliente_auten = ClienteAuten.objects.get(id=request.POST.get('client_id', None))
            tecnico = Tecnico.objects.get(id=request.POST.get('tecnico', None))
            carro = Carro.objects.get(id=request.POST.get('carro', None))
            km_previsto = request.POST.get('km_previsto', None)
            data_chegada_prevista = request.POST.get('data_chegada_prevista', None)            
            link_gps = request.POST.get('link_gps', None)
            data_saida_prevista = request.POST.get('data_saida_prevista', None)            
            observacao = request.POST.get('observacao', None)
            status = 0
            
            #------------------ Criar Viagem
            v = Viagem()
            v.empresa = empresa
            v.cliente_auten = cliente_auten
            v.tecnico = tecnico
            v.carro = carro
            v.data_chegada_prevista = str_to_datetime(data_chegada_prevista)
            v.link_gps = link_gps
            v.data_saida_prevista = str_to_datetime(data_saida_prevista)
            v.observacao = observacao
            v.km_previsto = km_previsto
            v.status = int(status)
            v.created_by = request.user.id
            v.created_at = datetime.datetime.now()
            v.save()
            
            doLog('Viagem +1', f'VIAGEM #{v.id} .Agendado viagens de {v.km_previsto}km para <b>@{v.tecnico.nome}</b> com saída no dia {v.data_saida_prevista}!', 1) # Success

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('ViagemIndexView')
    
    except Exception as e:
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('ViagemNewView')
        
@login_required
@require_http_methods(["GET"])
def editView(request, viagem_id):
    
    viagens = Viagem.objects.get(id=viagem_id)    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')
    carros = Carro.objects.filter(status=True).order_by('modelo')
    tecnicos = Tecnico.objects.filter(status=True).order_by('nome')
    
    context = {
        'item': viagens,        
        'empresas': clients,
        'carros': carros,
        'tecnicos': tecnicos
    }
    
    return render(request, 'Viagem/edit.html', context)

@login_required
@require_http_methods(["POST"])
def editSaveAction(request, viagem_id):

    try:
        
        v = Viagem.objects.get(id=viagem_id)
        
        with transaction.atomic():                        
            
            cliente_auten = ClienteAuten.objects.get(id=request.POST.get('client_id', None))
            tecnico = Tecnico.objects.get(id=request.POST.get('tecnico', None))
            carro = Carro.objects.get(id=request.POST.get('carro', None))
            km_previsto = request.POST.get('km_previsto', None)
            data_chegada_prevista = request.POST.get('data_chegada_prevista', None)            
            link_gps = request.POST.get('link_gps', None)
            data_saida_prevista = request.POST.get('data_saida_prevista', None)            
            observacao = request.POST.get('observacao', None)            
            
            #------------------ Criar Viagem
            v = Viagem.objects.get(id=viagem_id)            
            v.cliente_auten = cliente_auten
            v.tecnico = tecnico
            v.carro = carro
            v.data_chegada_prevista = str_to_datetime(data_chegada_prevista)
            v.link_gps = link_gps
            v.data_saida_prevista = str_to_datetime(data_saida_prevista)
            v.observacao = observacao
            v.km_previsto = km_previsto            
            v.updated_by = request.user.id
            v.updated_at = datetime.datetime.now()
            v.save()

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('ViagemIndexView')

    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('ViagemIndexView')
      
@login_required
def deleteAction(request, viagem_id):

    try:
        
        viagens = Viagem.objects.get(id=int(viagem_id))
        viagens.delete()

        context = {
            'status': 200,
            'descricao': 'Excluído com sucesso'
        }
        
    except Exception as e:
        
        context = {
            'status': 500,
            'description': str(e)
        }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
   
@login_required
def saidaView(request, viagem_id):

    item = Viagem.objects.get(id=viagem_id)

    context = {
        'item': item
    }

    return render(request, 'Viagem/Iniciar.html', context)

@login_required
@require_http_methods(["POST"])
def saveInicioAction(request, viagem_id):
    
    try:
        with transaction.atomic():                                                
            
            data_saida = request.POST.get('data_saida', None)
            km_saida = request.POST.get('km_saida', None)
            status = 2 # Em viagens
            
            #------------------ Criar Viagem
            v = Viagem.objects.get(id=viagem_id)
            v.data_saida = str_to_datetime(data_saida)
            v.km_saida = km_saida
            v.status = int(status)
            v.updated_by = request.user.id
            v.updated_at = datetime.datetime.now()
            v.save()
            
            doLog('Viagem Saída', f'VIAGEM #{v.id} .<b>@{v.tecnico.nome}</b> saiu de viagens. Usando o veículo {v.carro.modelo}. Data prevista de retorno no dia {v.data_chegada_prevista}!', 2) # Info

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('ViagemIndexView')
    
    except Exception as e:
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('ViagemNewView')
       
@login_required
def chegadaView(request, viagem_id):

    item = Viagem.objects.get(id=viagem_id)

    context = {
        'item': item
    }

    return render(request, 'Viagem/Finalizar.html', context)

@login_required
@require_http_methods(["POST"])
def saveChegadaAction(request, viagem_id):
    
    try:
        with transaction.atomic():                                                
            
            data_chegada = request.POST.get('data_chegada', None)
            km_chegada = request.POST.get('km_chegada', None)
            observacao = request.POST.get('observacao', None)            
            status = int(3) # Acerto Finalizado            
            
            #------------------ Criar Viagem
            v = Viagem.objects.get(id=viagem_id)
            v.data_chegada = str_to_datetime(data_chegada)
            v.km_chegada = km_chegada
            v.observacao = observacao
            v.status = status
            v.updated_by = request.user.id
            v.updated_at = datetime.datetime.now()
            v.save()
            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            
            return redirect('ViagemIndexView')
            
    
    except Exception as e:
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('ViagemIndexView')
    
@login_required
def extratoView(request, viagem_id):    

    viagem = Viagem.objects.get(id=viagem_id)
    viagemInstalacoesCount = ViagemInstalacao.objects.filter(viagem=viagem).count()
    viagemInstalacoes = ViagemInstalacao.objects.filter(viagem=viagem)
    
    dadosPorCliente = []
    
    for instalacao in viagemInstalacoes:    
        
        viagemInstalacaoKits = ViagemInstalacaoKit.objects.filter(viagem_instalacao=instalacao)
        itens = []
        
        for viagemInstalacaoKit in viagemInstalacaoKits:        
            childs = ViagemInstalacaoKitChild.objects.filter(viagem_instalacao_kit=viagemInstalacaoKit)
            
            for child in childs:
                itens.append({
                    'v2': f'#{child.v2.id} - Versão: {child.v2.version_current}' if child.v2 else None,
                    'sensor': f'#{child.sensor.id} - Versão: {child.sensor.version_current}' if child.sensor else None,
                    'tela': f'#{child.tela.id} - Versão: {child.tela.version_current}' if child.tela else None,
                    'outro': child.outro,
                    'is_reserva': child.is_reserva
                })
        
        dadosPorCliente.append({
            'viagem_instalacao_id': instalacao.id,
            'nome': instalacao.cliente_auten.nome,
            'cidade': f'{instalacao.cliente_auten.cidade} - {instalacao.cliente_auten.uf}',
            'job': instalacao.job,
            'endereco': f'{instalacao.cliente_auten.endereco} nº {instalacao.cliente_auten.numero}',
            'observacoes': instalacao.cliente_auten.observacao_endereco,
            'telefone': instalacao.cliente_auten.telefone,
            'maquina_modelo': instalacao.get_maquina_modelo_display(),
            'tipo_instalacao': instalacao.get_tipo_instalacao_display(),
            'tipo_instalacao_id': instalacao.tipo_instalacao,
            'itens': itens
        })

    context = {        
        'viagem': viagem,
        'viagemInstalacoesCount': viagemInstalacoesCount,
        'dadosPorCliente': dadosPorCliente
    }

    return render(request, 'Viagem/extrato.html', context)
    
@login_required    
@require_http_methods(["GET"])
def filterView(request):        

    tecnicos = Tecnico.objects.filter(status=True)
    clientes = ClienteAuten.objects.filter(status=True)

    context = {
        'tecnicos': tecnicos,
        'clientes': clientes,
        'STATUS_CHOICES': STATUS_CHOICES
    }

    return render(request, 'Viagem/filter.html', context)

@login_required        
@require_http_methods(["POST"])
def filterAction(request):
    tecnico = request.POST.get('tecnico')
    cliente = request.POST.get('cliente')    
    status = request.POST.get('status')
    data = request.POST.get('data')

    # Cria um dicionário com os filtros se eles estiverem presentes
    params = {}
    if tecnico and tecnico != '-1': # Todos
        params['tecnico'] = tecnico
    if cliente and cliente != '-1': # Todos
        params['cliente'] = cliente    
    if status and status != '-1':   # Todos
        params['status'] = status
    if data and data != '-1':       # Todos
        params['data'] = data

    # Constrói a URL com os parâmetros
    url = f"{reverse('ViagemIndexView')}?{urlencode(params)}"
    return redirect(url)
    
    
    