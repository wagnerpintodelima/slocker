import os
import datetime
from django.utils import timezone
import json
from slock.settings import DOMAIN_ASSETS
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from backend.models import Viagem, ClienteAuten, TIPO_INSTALACAO_CHOICES, MAQUINA_MODELO_CHOICES, Sensor, Tela, V2, Tecnico, ViagemInstalacao, PosVenda, ViagemInstalacaoKit, ViagemInstalacaoKitChild, Maquina
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers
from django.db import transaction
from backend.Controller.BaseController import str_to_datetime, saveFile

_PATH_FILE_VIAGEM = 'backend/upload/viagem/instalacao/'

@login_required
def indexView(request, viagem_id):

    item = Viagem.objects.get(id=viagem_id)        
    itens = ViagemInstalacao.objects.filter(viagem=item)

    context = {
        'viagem': item,
        'instalacoes': itens,
        'DOMAIN_ASSETS': DOMAIN_ASSETS
    }

    return render(request, 'ViagemInstalacao/index.html', context)

@login_required
def newView(request, viagem_id):    

    clients = ClienteAuten.objects.filter(status=True).order_by('nome')
    item = Viagem.objects.get(id=viagem_id)
    viagemInstalacaoAnteriores = ViagemInstalacao.objects.filter(status=True)
    maquinas = Maquina.objects.filter(status=True)
    
    context = {        
        'viagem': item,
        'maquinas': maquinas,
        'empresas': clients,
        'TIPO_INSTALACAO_CHOICES': TIPO_INSTALACAO_CHOICES,        
        'viagemInstalacaoAnteriores': viagemInstalacaoAnteriores
    }

    return render(request, 'ViagemInstalacao/new.html', context)

@login_required
@require_http_methods(["POST"])
def saveAction(request, viagem_id):
    
    try:
        with transaction.atomic():
                        
            cliente_auten = ClienteAuten.objects.get(id=request.POST.get('client_id', None))
            tipo_instalacao = request.POST.get('tipo_instalacao', None)
            maquina_modelo = request.POST.get('maquina_modelo', None)
            job = request.POST.get('job', None)
            viagem_instalacao_pai = int(request.POST.get('viagem_instalacao_pai', None))
            
            
            #------------------ Criar Viagem Instalação
            v = ViagemInstalacao()
            if viagem_instalacao_pai > 0:
                v.viagem_instalacao_pai = ViagemInstalacao.objects.get(id=viagem_instalacao_pai)
            v.viagem = Viagem.objects.get(id=viagem_id)       
            v.cliente_auten = cliente_auten
            v.tipo_instalacao = tipo_instalacao
            if maquina_modelo != '0':                            
                v.maquina = Maquina.objects.get(id=maquina_modelo)
            v.job = job          
            v.status = False
            v.created_by = request.user.id
            v.created_at = datetime.datetime.now()
            v.save()

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('ViagemInstalacaoIndexView', viagem_id)
    
    except Exception as e:
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('ViagemInstalacaoIndexView', viagem_id)
        
@login_required
@require_http_methods(["GET"])
def editView(request, viagem_instalacao_id):
    
    viagemInstalacao = ViagemInstalacao.objects.get(id=viagem_instalacao_id)    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')   
    viagemInstalacaoAnteriores = ViagemInstalacao.objects.filter(status=True) 
    maquinas = Maquina.objects.filter(status=True)
    
    context = {
        'viagemInstalacao': viagemInstalacao,        
        'empresas': clients,
        'maquinas': maquinas,
        'TIPO_INSTALACAO_CHOICES': TIPO_INSTALACAO_CHOICES,        
        'viagemInstalacaoAnteriores': viagemInstalacaoAnteriores
    }
    
    return render(request, 'ViagemInstalacao/edit.html', context)

@login_required
@require_http_methods(["POST"])
def editSaveAction(request, viagem_instalacao_id):

    try:
        
        v = ViagemInstalacao.objects.get(id=viagem_instalacao_id)
        
        with transaction.atomic():                        
            
            cliente_auten = ClienteAuten.objects.get(id=request.POST.get('client_id', None))
            tipo_instalacao = request.POST.get('tipo_instalacao', None)
            maquina_modelo = request.POST.get('maquina_modelo', None)
            job = request.POST.get('job', None)
            viagem_instalacao_pai = int(request.POST.get('viagem_instalacao_pai', None))
            
            #------------------ Editar Viagem Instalação                        
            if viagem_instalacao_pai > 0:
                v.viagem_instalacao_pai = ViagemInstalacao.objects.get(id=viagem_instalacao_pai)
            v.cliente_auten = cliente_auten
            v.tipo_instalacao = tipo_instalacao
            if maquina_modelo != '0':                            
                v.maquina = Maquina.objects.get(id=maquina_modelo)
            v.job = job
            v.status = False
            v.updated_by = request.user.id
            v.updated_at = datetime.datetime.now()
            v.save()

            messages.add_message(request, messages.SUCCESS, 'Registro editado com sucesso!')
            return redirect('ViagemInstalacaoIndexView', v.viagem.id)

    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('ViagemInstalacaoIndexView', v.viagem.id)
      
@login_required
def deleteAction(request, viagem_instalacao_id):

    try:
        
        viagemInstalacao = ViagemInstalacao.objects.get(id=int(viagem_instalacao_id))
        
        posVendas = PosVenda.objects.filter(viagem_instalacao=viagemInstalacao).delete()
        
        # Ve se tem ViagemInstalacaoKit
        viagemInstalacaoKit = ViagemInstalacaoKit.objects.filter(viagem_instalacao=viagemInstalacao).first()
        
        if viagemInstalacaoKit:                    
            # Ve se tem ViagemInstalacaoKitChild
            viagemInstalacaoKitChilds = ViagemInstalacaoKitChild.objects.filter(viagem_instalacao_kit=viagemInstalacaoKit)
            viagemInstalacaoKitChilds.delete()        
            viagemInstalacaoKit.delete()                    
        viagemInstalacao.delete()

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
def finalizarView(request, viagem_instalacao_id):    
    
    item = ViagemInstalacao.objects.get(id=viagem_instalacao_id)     
    maquinas = Maquina.objects.filter(status=True)       
    
    context = {        
        'viagemInstalacao': item,        
        'TIPO_INSTALACAO_CHOICES': TIPO_INSTALACAO_CHOICES,
        'maquinas': maquinas
    }

    return render(request, 'ViagemInstalacao/finalizar.html', context)

@login_required
@require_http_methods(["POST"])
def finalizarAction(request, viagem_instalacao_id):

    v = ViagemInstalacao.objects.get(id=viagem_instalacao_id)

    with transaction.atomic():

        descricao_atendimento = request.POST.get('descricao_atendimento', None)        
        maquina_modelo = request.POST.get('maquina_modelo', None)        
        foto = None
        if 'foto' in request.FILES:
            foto = request.FILES['foto']        

        #------------------ Criar Viagem Instalação Fechamento                
        if maquina_modelo != '0':                            
                v.maquina = Maquina.objects.get(id=maquina_modelo)     
        v.descricao_atendimento = descricao_atendimento
        v.status = True
        v.updated_by = request.user.id
        v.updated_at = datetime.datetime.now()
        v.save()

        if foto:            
            try:
                os.remove(_PATH_FILE_VIAGEM + v.foto + '.png')
            except Exception as er:
                messages.add_message(request, messages.ERROR, "Ocorreu esse erro ao tentar deletar a foto: {}".format(er))
            
            v.foto_capa = saveFile(_PATH_FILE_VIAGEM, 'png', foto)        
        
        v.save()
        messages.add_message(request, messages.SUCCESS, 'Instalação finalizada com sucesso!')
        
        # Gerar Pós Vendas
        p = PosVenda()
        p.viagem_instalacao = v
        p.data_programada_ligacao = datetime.datetime.now() + datetime.timedelta(days=15)
        p.status = False
        p.created_by = request.user.id
        p.created_at = datetime.datetime.now()
        p.save()                
        messages.add_message(request, messages.SUCCESS, f'Pós Vendas gerado com sucesso para o dia {p.data_programada_ligacao} !')

    return redirect('ViagemInstalacaoIndexView', v.viagem.id)

@login_required
@require_http_methods(["GET"])
def vView(request, viagem_instalacao_id):
    
    item = ViagemInstalacao.objects.get(id=viagem_instalacao_id)            

    context = {
        'viagemInstalacao': item,        
        'DOMAIN_ASSETS': DOMAIN_ASSETS
    }

    return render(request, 'ViagemInstalacao/view.html', context)

@login_required
@require_http_methods(["GET"])
def montarKitView(request, viagem_instalacao_id):
    
    viagemInstalacao = ViagemInstalacao.objects.get(id=viagem_instalacao_id)   
    viagemInstalacaoKitChilds = ViagemInstalacaoKitChild.objects.filter(viagem_instalacao_kit__viagem_instalacao=viagemInstalacao)            
    
    v2s = V2.objects.filter(automation__cliente_auten__isnull=True)
    sensores = Sensor.objects.filter(automation__cliente_auten__isnull=True)
    telas = Tela.objects.filter(automation__cliente_auten__isnull=True)

    context = {
        'viagemInstalacao': viagemInstalacao,
        'viagem': viagemInstalacao.viagem,
        'DOMAIN_ASSETS': DOMAIN_ASSETS,
        'TIPO_INSTALACAO_CHOICES': TIPO_INSTALACAO_CHOICES,
        'sensores': sensores,
        'telas': telas,
        'v2s': v2s,
        'viagemInstalacaoKitChilds': viagemInstalacaoKitChilds
    }

    return render(request, 'ViagemInstalacao/montar_kit.html', context)

@login_required
@require_http_methods(["POST"])
def saveKitAction(request, viagem_instalacao_id):
    
    try:
        with transaction.atomic():
            
            viagemInstalacao = ViagemInstalacao.objects.get(id=viagem_instalacao_id)
                        
            v2_id = int(request.POST.get('v2_id', None))
            tela_id = int(request.POST.get('tela_id', None))
            sensor_id = int(request.POST.get('sensor_id', None))
            sensor_id_2 = int(request.POST.get('sensor_id_2', None))
            sensor_id_3 = int(request.POST.get('sensor_id_3', None))
            sensor_id_4 = int(request.POST.get('sensor_id_4', None))
            outro = request.POST.get('outro', None)

            v2_is_reserva = int(request.POST.get('v2_is_reserva', None))
            tela_is_reserva = int(request.POST.get('tela_is_reserva', None))
            sensor_is_reserva = int(request.POST.get('sensor_is_reserva', None))                        
            sensor_2_is_reserva = int(request.POST.get('sensor_2_is_reserva', None))                        
            sensor_3_is_reserva = int(request.POST.get('sensor_3_is_reserva', None))                        
            sensor_4_is_reserva = int(request.POST.get('sensor_4_is_reserva', None))                        
            outro_is_reserva = int(request.POST.get('outro_is_reserva', None))                        
            
            #------------------ Criar Cabeçalho Instalação
            viagemInstalacaoKitInBD = ViagemInstalacaoKit.objects.filter(viagem_instalacao=viagemInstalacao).first()
            
            if not viagemInstalacaoKitInBD: # Cria um novo
                vkit = ViagemInstalacaoKit()
                vkit.viagem_instalacao = viagemInstalacao
                vkit.created_by = request.user.id
                vkit.created_at = datetime.datetime.now()                
            else: # Está editando, porém nao precisa mexer neste registro pai
                vkit = viagemInstalacaoKitInBD
                vkit.updated_by = request.user.id
                vkit.updated_at = datetime.datetime.now()
            vkit.save()

            # Cria o child da V2 se houver
            if v2_id != 0:
                central = V2.objects.get(id=v2_id)
                vchild = ViagemInstalacaoKitChild()
                vchild.viagem_instalacao_kit = vkit
                vchild.v2 = central
                vchild.is_reserva = bool(v2_is_reserva)
                if bool(v2_is_reserva):
                    vchild.status = 0 # Pendente
                else:
                    vchild.status = 2 # Vendido
                vchild.created_by = request.user.id
                vchild.created_at = datetime.datetime.now()
                vchild.save()
                
                # Atualizar Cliente que está dentro de automation
                central.automation.cliente_auten = viagemInstalacao.cliente_auten
                central.automation.save()
                messages.add_message(request, messages.SUCCESS, f'Central #{central.id} add com sucesso!')        

            # Cria o child da Tela se houver
            if tela_id != 0:
                tela = Tela.objects.get(id=tela_id)
                vchild = ViagemInstalacaoKitChild()
                vchild.viagem_instalacao_kit = vkit
                vchild.tela = tela
                vchild.is_reserva = bool(tela_is_reserva)
                if bool(tela_is_reserva):
                    vchild.status = 0 # Pendente
                else:
                    vchild.status = 2 # Vendido
                vchild.created_by = request.user.id
                vchild.created_at = datetime.datetime.now()
                vchild.save()
                                
                # Atualizar Cliente que está dentro de automation
                tela.automation.cliente_auten = viagemInstalacao.cliente_auten
                tela.automation.save()
                messages.add_message(request, messages.SUCCESS, f'Tela #{tela.id} add com sucesso!')                                            

            # Cria o child do Sensor 1 se houver
            if sensor_id != 0:
                sensor = Sensor.objects.get(id=sensor_id)
                vchild = ViagemInstalacaoKitChild()
                vchild.viagem_instalacao_kit = vkit
                vchild.sensor = sensor
                vchild.is_reserva = bool(sensor_is_reserva)
                if bool(sensor_is_reserva):
                    vchild.status = 0 # Pendente
                else:
                    vchild.status = 2 # Vendido
                vchild.created_by = request.user.id
                vchild.created_at = datetime.datetime.now()
                vchild.save()
                
                # Atualizar Cliente que está dentro de automation
                sensor.automation.cliente_auten = viagemInstalacao.cliente_auten
                sensor.automation.save()
                messages.add_message(request, messages.SUCCESS, f'sensor #{sensor.id} add com sucesso!')                                                            

            # Cria o child do Sensor 2 se houver
            if sensor_id_2 != 0:
                sensor = Sensor.objects.get(id=sensor_id_2)
                vchild = ViagemInstalacaoKitChild()
                vchild.viagem_instalacao_kit = vkit
                vchild.sensor = sensor
                vchild.is_reserva = bool(sensor_2_is_reserva)
                if bool(sensor_2_is_reserva):
                    vchild.status = 0 # Pendente
                else:
                    vchild.status = 2 # Vendido
                vchild.created_by = request.user.id
                vchild.created_at = datetime.datetime.now()
                vchild.save()
                
                # Atualizar Cliente que está dentro de automation
                sensor.automation.cliente_auten = viagemInstalacao.cliente_auten
                sensor.automation.save()
                messages.add_message(request, messages.SUCCESS, f'sensor #{sensor.id} add com sucesso!')                                                            

            # Cria o child do Sensor 3 se houver
            if sensor_id_3 != 0:
                sensor = Sensor.objects.get(id=sensor_id_3)
                vchild = ViagemInstalacaoKitChild()
                vchild.viagem_instalacao_kit = vkit
                vchild.sensor = sensor
                vchild.is_reserva = bool(sensor_3_is_reserva)
                if bool(sensor_3_is_reserva):
                    vchild.status = 0 # Pendente
                else:
                    vchild.status = 2 # Vendido
                vchild.created_by = request.user.id
                vchild.created_at = datetime.datetime.now()
                vchild.save()
                
                # Atualizar Cliente que está dentro de automation
                sensor.automation.cliente_auten = viagemInstalacao.cliente_auten
                sensor.automation.save()
                messages.add_message(request, messages.SUCCESS, f'sensor #{sensor.id} add com sucesso!')  

            # Cria o child do Sensor 4 se houver
            if sensor_id_4 != 0:
                sensor = Sensor.objects.get(id=sensor_id_4)
                vchild = ViagemInstalacaoKitChild()
                vchild.viagem_instalacao_kit = vkit
                vchild.sensor = sensor
                vchild.is_reserva = bool(sensor_4_is_reserva)
                if bool(sensor_4_is_reserva):
                    vchild.status = 0 # Pendente
                else:
                    vchild.status = 2 # Vendido
                vchild.created_by = request.user.id
                vchild.created_at = datetime.datetime.now()
                vchild.save()
                
                # Atualizar Cliente que está dentro de automation
                sensor.automation.cliente_auten = viagemInstalacao.cliente_auten
                sensor.automation.save()
                messages.add_message(request, messages.SUCCESS, f'sensor #{sensor.id} add com sucesso!')              

            # Cria o child do Outro se houver
            if outro != '':                
                vchild = ViagemInstalacaoKitChild()
                vchild.viagem_instalacao_kit = vkit
                vchild.outro = outro
                vchild.is_reserva = bool(outro_is_reserva)
                if bool(outro_is_reserva):
                    vchild.status = 0 # Pendente
                else:
                    vchild.status = 2 # Vendido
                vchild.created_by = request.user.id
                vchild.created_at = datetime.datetime.now()
                vchild.save()
                messages.add_message(request, messages.SUCCESS, f'{outro} #{vchild.id} add com sucesso!')            
            
            return redirect('ViagemInstalacaoMontarKitView', viagemInstalacao.id)
    
    except Exception as e:
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('ViagemInstalacaoIndexView', viagemInstalacao.viagem.id)

@login_required
def deleteKitChildAction(request, viagem_instalacao_kit_child_id):

    try:
        
        delViagemInstalacaoChilds(viagem_instalacao_kit_child_id)
        

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

def delViagemInstalacaoChilds(viagem_instalacao_kit_child_id):
    
    try:
        
        child = ViagemInstalacaoKitChild.objects.get(id=int(viagem_instalacao_kit_child_id))
        
        if child.v2:
            child.v2.automation.cliente_auten = None
            child.v2.automation.save()
            
        if child.tela:
            child.tela.automation.cliente_auten = None
            child.tela.automation.save()            
            
        if child.sensor:
            child.sensor.automation.cliente_auten = None
            child.sensor.automation.save()                        
        
        child.delete()

        return True
        
    except Exception as e:
        
        return False