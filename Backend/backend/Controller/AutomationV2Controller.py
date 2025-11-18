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
from backend.models import V2, ClienteAuten, Automation, AutomationType, MODO_OPERACAO_CHOICES, V2Configuracao
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers
from django.db import transaction
from backend.Controller.BaseController import doLog

@login_required
def indexView(request, automation_type):
    data = V2.objects.filter(status=True).order_by('-id')

    context = {
        'data': data,
        'automation_type': automation_type
    }

    return render(request, 'Automation/V2/index.html', context)

@login_required
def newView(request, automation_type):    
    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')
    
    context = {        
        'clients': clients,
        'automation_type': automation_type
    }

    return render(request, 'Automation/V2/new.html', context)

@login_required
@require_http_methods(["POST"])
def saveAction(request, automation_type):
    
    try:
        with transaction.atomic():
            automationType = AutomationType.objects.get(id=automation_type)            
            client_id = request.POST.get('client_id', None)
            version = request.POST.get('version_current', None)
            description = request.POST.get('description', None)        
            status = request.POST.get('status', 0)            
            
            # Criar automation
            automation = Automation()
            if client_id != '0':                
                automation.cliente_auten = ClienteAuten.objects.get(id=client_id)
            automation.description = 'VicSensor - V2'
            automation.status = status
            automation.automation_type = automationType
            automation.type_location = 'Lavoura'
            automation.created_by = request.user.id
            automation.created_at = datetime.datetime.now()
            automation.save()
            
            # Criar V2
            v2 = V2()
            v2.automation = automation            
            v2.version_current = version
            v2.description = description
            v2.status = status
            v2.created_by = request.user.id
            v2.created_at = datetime.datetime.now()
            v2.save()
            
            doLog('+V2', f'V2 - <b>@{request.user.first_name}</b>. #{v2.id} .Nova automação criada!', 1) # Success

            messages.add_message(request, messages.SUCCESS, f'Registro salvo com sucesso! ID #{v2.id}')
            return redirect('V2IndexView', automation_type)
    
    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('AutomationIndexView')
        
@login_required
@require_http_methods(["GET"])
def editView(request, automation_type, v2_id):
    
    v2 = V2.objects.get(id=v2_id)    
    clients = ClienteAuten.objects.filter(status=True).order_by('nome')    
    
    context = {
        'v2': v2,
        'automation_type': automation_type,
        'clients': clients        
    }
    
    return render(request, 'Automation/V2/edit.html', context)

@login_required
@require_http_methods(["POST"])
def editSaveAction(request, automation_type, v2_id):

    try:
        with transaction.atomic():
            automationType = AutomationType.objects.get(id=automation_type)
            client_id = int(request.POST.get('client_id', None))
            version = request.POST.get('version_current', None)
            description = request.POST.get('description', None)
            status = request.POST.get('status', 0)                                                                            
                
            v2 = V2.objects.get(id=v2_id)
            if client_id != 0:
                v2.automation.cliente_auten = ClienteAuten.objects.get(id=client_id)
            else:
                v2.automation.cliente_auten = None
            v2.automation.save()
            
            v2.description = description
            v2.version_current = version
            v2.status = status
            v2.updated_by = request.user.id
            v2.updated_at = datetime.datetime.now()
            v2.save()
            
            doLog('V2 alterada', f'V2 #{v2.id} .O Usuário <b>@{request.user.first_name}</b> editou o cadastro!', 2) # Info

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            return redirect('V2IndexView', automation_type)

    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('AutomationIndexView')
      
@login_required
def deleteAction(request, v2_id):

    try:
        v2 = V2.objects.get(id=int(v2_id))        
        doLog('V2 Excluída', f'V2 #{v2.id} .O Usuário <b>@{request.user.first_name}</b> excluiu essa automação.', 0) # Error
        v2.delete()

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
def calibrationView(request, automation_type, v2_id):    

    clients = ClienteAuten.objects.filter(status=True).order_by('nome')    
    v2 = V2.objects.get(id=v2_id)
    v2Configuracao = V2Configuracao.objects.filter(v2=v2).first()

    context = {
        'v2': v2,
        'v2Configuracao': v2Configuracao,
        'clients': clients,
        'automation_type': automation_type,
        'MODO_OPERACAO_CHOICES': MODO_OPERACAO_CHOICES
    }

    return render(request, 'Automation/V2/calibrate.html', context)

@login_required
@require_http_methods(["POST"])
def calibrationSaveAction(request, automation_type, v2_id):

    try:
        with transaction.atomic():
            
            automationType = None
            if int(automation_type) != 0:
                automationType = AutomationType.objects.get(id=automation_type)      
            v2 = V2.objects.get(id=v2_id)      
            
            v2_configuracao_id = request.POST.get('v2_configuracao_id', None)
            
            
            # Geral
            modo_padrao = request.POST.get('modo_padrao', None)
            modo_operacao = request.POST.get('modo_operacao', None)
            modo_operacao_zc = request.POST.get('modo_operacao_zc', None)        
            altura_barra = request.POST.get('altura_barra', None)            
            altura_quadro = request.POST.get('altura_quadro', None)            
            compensar_altura_porcentagem = request.POST.get('compensar_altura_porcentagem', None)            
            subir_direto_interno = request.POST.get('subir_direto_interno', None)            
            subir_direto_externo = request.POST.get('subir_direto_externo', None)            
            tempo_espera_zc = request.POST.get('tempo_espera_zc', None)            
            planar = request.POST.get('planar', None)            
            planar = True if planar == '1' else False
            
            sensor_interno_habilitado = request.POST.get('sensor_interno_habilitado', None)            
            sensor_interno_habilitado = True if sensor_interno_habilitado == '1' else False
            
            pitch_min = request.POST.get('pitch_min', None)            
            pitch_max = request.POST.get('pitch_max', None)            
            roll_min = request.POST.get('roll_min', None)            
            roll_max = request.POST.get('roll_max', None)            
            yaw = request.POST.get('yaw', None)            
            amostras_interno = request.POST.get('amostras_interno', None)            
            amostras_externo = request.POST.get('amostras_externo', None)      
            
            # Direita 
            ## Pulsos
            t_subida_direita = request.POST.get('t_subida_direita', None)      
            t_descida_direita = request.POST.get('t_descida_direita', None)      
            compensar_negativo_habilitado_direita = request.POST.get('compensar_negativo_habilitado_direita', None)      
            compensar_negativo_habilitado_direita = True if compensar_negativo_habilitado_direita == '1' else False            
            compensar_negativo_direita = request.POST.get('compensar_negativo_direita', None)      
            duty_subida_min_direita = request.POST.get('duty_subida_min_direita', None)      
            duty_descida_min_direita = request.POST.get('duty_descida_min_direita', None)      
            duty_subida_max_direita = request.POST.get('duty_subida_max_direita', None)      
            duty_descida_max_direita = request.POST.get('duty_descida_max_direita', None)      
            compensar_positivo_habilitado_direita = request.POST.get('compensar_positivo_habilitado_direita', None)      
            compensar_positivo_habilitado_direita = True if compensar_positivo_habilitado_direita == '1' else False            
            compensar_positivo_direita = request.POST.get('compensar_positivo_direita', None)      
            
            # Margens
            margem_superior_ext_one_direita = request.POST.get('margem_superior_ext_one_direita', None)      
            margem_superior_ext_two_direita = request.POST.get('margem_superior_ext_two_direita', None)      
            margem_superior_ext_three_direita = request.POST.get('margem_superior_ext_three_direita', None)      
            margem_inferior_ext_one_direita = request.POST.get('margem_inferior_ext_one_direita', None)      
            margem_inferior_ext_two_direita = request.POST.get('margem_inferior_ext_two_direita', None)      
            margem_inferior_ext_three_direita = request.POST.get('margem_inferior_ext_three_direita', None)      
            margem_inferior_int_one_direita = request.POST.get('margem_inferior_int_one_direita', None)      
            margem_inferior_int_two_direita = request.POST.get('margem_inferior_int_two_direita', None)      
            margem_inferior_int_three_direita = request.POST.get('margem_inferior_int_three_direita', None)      
            tempo_espera_one_direita = request.POST.get('tempo_espera_one_direita', None)      
            tempo_espera_two_direita = request.POST.get('tempo_espera_two_direita', None)      
            tempo_espera_three_direita = request.POST.get('tempo_espera_three_direita', None)      
            
            # Esquerda
            ## Pulsos
            t_subida_esquerda = request.POST.get('t_subida_esquerda', None)      
            t_descida_esquerda = request.POST.get('t_descida_esquerda', None)      
            compensar_negativo_habilitado_esquerda = request.POST.get('compensar_negativo_habilitado_esquerda', None)      
            compensar_negativo_habilitado_esquerda = True if compensar_negativo_habilitado_esquerda == '1' else False
            compensar_negativo_esquerda = request.POST.get('compensar_negativo_esquerda', None)      
            duty_subida_min_esquerda = request.POST.get('duty_subida_min_esquerda', None)      
            duty_descida_min_esquerda = request.POST.get('duty_descida_min_esquerda', None)      
            duty_subida_max_esquerda = request.POST.get('duty_subida_max_esquerda', None)      
            duty_descida_max_esquerda = request.POST.get('duty_descida_max_esquerda', None)      
            compensar_positivo_habilitado_esquerda = request.POST.get('compensar_positivo_habilitado_esquerda', None)      
            compensar_positivo_habilitado_esquerda = True if compensar_positivo_habilitado_esquerda == '1' else False
            compensar_positivo_esquerda = request.POST.get('compensar_positivo_esquerda', None)      
            
            # Margens
            margem_superior_ext_one_esquerda = request.POST.get('margem_superior_ext_one_esquerda', None)      
            margem_superior_ext_two_esquerda = request.POST.get('margem_superior_ext_two_esquerda', None)      
            margem_superior_ext_three_esquerda = request.POST.get('margem_superior_ext_three_esquerda', None)      
            margem_inferior_ext_one_esquerda = request.POST.get('margem_inferior_ext_one_esquerda', None)      
            margem_inferior_ext_two_esquerda = request.POST.get('margem_inferior_ext_two_esquerda', None)      
            margem_inferior_ext_three_esquerda = request.POST.get('margem_inferior_ext_three_esquerda', None)      
            margem_inferior_int_one_esquerda = request.POST.get('margem_inferior_int_one_esquerda', None)      
            margem_inferior_int_two_esquerda = request.POST.get('margem_inferior_int_two_esquerda', None)      
            margem_inferior_int_three_esquerda = request.POST.get('margem_inferior_int_three_esquerda', None)      
            tempo_espera_one_esquerda = request.POST.get('tempo_espera_one_esquerda', None)      
            tempo_espera_two_esquerda = request.POST.get('tempo_espera_two_esquerda', None)      
            tempo_espera_three_esquerda = request.POST.get('tempo_espera_three_esquerda', None)     
            
            # Quadro
            ## Pulsos
            t_subida_quadro = request.POST.get('t_subida_quadro', None)      
            t_descida_quadro = request.POST.get('t_descida_quadro', None)      
            compensar_negativo_habilitado_quadro = request.POST.get('compensar_negativo_habilitado_quadro', None)      
            compensar_negativo_habilitado_quadro = True if compensar_negativo_habilitado_quadro == '1' else False
            compensar_negativo_quadro = request.POST.get('compensar_negativo_quadro', None)      
            duty_subida_min_quadro = request.POST.get('duty_subida_min_quadro', None)      
            duty_descida_min_quadro = request.POST.get('duty_descida_min_quadro', None)      
            duty_subida_max_quadro = request.POST.get('duty_subida_max_quadro', None)      
            duty_descida_max_quadro = request.POST.get('duty_descida_max_quadro', None)      
            compensar_positivo_habilitado_quadro = request.POST.get('compensar_positivo_habilitado_quadro', None)      
            compensar_positivo_habilitado_quadro = True if compensar_positivo_habilitado_quadro == '1' else False
            compensar_positivo_quadro = request.POST.get('compensar_positivo_quadro', None)      
            
            # Margens
            margem_superior_ext_one_quadro = request.POST.get('margem_superior_ext_one_quadro', None)      
            margem_superior_ext_two_quadro = request.POST.get('margem_superior_ext_two_quadro', None)      
            margem_superior_ext_three_quadro = request.POST.get('margem_superior_ext_three_quadro', None)      
            margem_inferior_ext_one_quadro = request.POST.get('margem_inferior_ext_one_quadro', None)      
            margem_inferior_ext_two_quadro = request.POST.get('margem_inferior_ext_two_quadro', None)      
            margem_inferior_ext_three_quadro = request.POST.get('margem_inferior_ext_three_quadro', None)      
            margem_inferior_int_one_quadro = request.POST.get('margem_inferior_int_one_quadro', None)      
            margem_inferior_int_two_quadro = request.POST.get('margem_inferior_int_two_quadro', None)      
            margem_inferior_int_three_quadro = request.POST.get('margem_inferior_int_three_quadro', None)      
            tempo_espera_one_quadro = request.POST.get('tempo_espera_one_quadro', None)      
            tempo_espera_two_quadro = request.POST.get('tempo_espera_two_quadro', None)      
            tempo_espera_three_quadro = request.POST.get('tempo_espera_three_quadro', None)                        

            # Criar/Editar V2 Configuração
            if v2_configuracao_id:
                vconf = V2Configuracao.objects.get(id=v2_configuracao_id)
            else:
                vconf = V2Configuracao()

            vconf.v2 = v2

            # Geral
            vconf.modo_padrao = modo_padrao
            vconf.altura_barra = altura_barra
            vconf.altura_quadro = altura_quadro
            vconf.modo_operacao = modo_operacao
            vconf.modo_operacao_zc = modo_operacao_zc
            vconf.subir_direto_interno = subir_direto_interno
            vconf.subir_direto_externo = subir_direto_externo
            vconf.tempo_espera_zc = tempo_espera_zc
            vconf.planar = planar
            vconf.compensar_altura_porcentagem = compensar_altura_porcentagem
            vconf.pitch_min = pitch_min
            vconf.pitch_max = pitch_max
            vconf.roll_min = roll_min
            vconf.roll_max = roll_max
            vconf.yaw = yaw
            vconf.amostras_interno = amostras_interno
            vconf.amostras_externo = amostras_externo
            vconf.sensor_interno_habilitado = sensor_interno_habilitado
            
            # Configurações da Barra Direita
            vconf.t_subida_direita = t_subida_direita
            vconf.t_descida_direita = t_descida_direita
            vconf.duty_subida_min_direita = duty_subida_min_direita
            vconf.duty_subida_max_direita = duty_subida_max_direita
            vconf.duty_descida_min_direita = duty_descida_min_direita
            vconf.duty_descida_max_direita = duty_descida_max_direita
            vconf.compensar_negativo_habilitado_direita = compensar_negativo_habilitado_direita
            vconf.compensar_positivo_habilitado_direita = compensar_positivo_habilitado_direita
            vconf.compensar_negativo_direita = compensar_negativo_direita
            vconf.compensar_positivo_direita = compensar_positivo_direita
            vconf.margem_superior_ext_one_direita = margem_superior_ext_one_direita
            vconf.margem_inferior_ext_one_direita = margem_inferior_ext_one_direita
            vconf.margem_inferior_int_one_direita = margem_inferior_int_one_direita
            vconf.tempo_espera_one_direita = tempo_espera_one_direita
            vconf.margem_superior_ext_two_direita = margem_superior_ext_two_direita
            vconf.margem_inferior_ext_two_direita = margem_inferior_ext_two_direita
            vconf.margem_inferior_int_two_direita = margem_inferior_int_two_direita
            vconf.tempo_espera_two_direita = tempo_espera_two_direita
            vconf.margem_superior_ext_three_direita = margem_superior_ext_three_direita
            vconf.margem_inferior_ext_three_direita = margem_inferior_ext_three_direita
            vconf.margem_inferior_int_three_direita = margem_inferior_int_three_direita
            vconf.tempo_espera_three_direita = tempo_espera_three_direita
            
            # Configurações da Barra Esquerda
            vconf.t_subida_esquerda = t_subida_esquerda
            vconf.t_descida_esquerda = t_descida_esquerda
            vconf.duty_subida_min_esquerda = duty_subida_min_esquerda
            vconf.duty_subida_max_esquerda = duty_subida_max_esquerda
            vconf.duty_descida_min_esquerda = duty_descida_min_esquerda
            vconf.duty_descida_max_esquerda = duty_descida_max_esquerda
            vconf.compensar_negativo_habilitado_esquerda = compensar_negativo_habilitado_esquerda
            vconf.compensar_positivo_habilitado_esquerda = compensar_positivo_habilitado_esquerda
            vconf.compensar_negativo_esquerda = compensar_negativo_esquerda
            vconf.compensar_positivo_esquerda = compensar_positivo_esquerda
            vconf.margem_superior_ext_one_esquerda = margem_superior_ext_one_esquerda
            vconf.margem_inferior_ext_one_esquerda = margem_inferior_ext_one_esquerda
            vconf.margem_inferior_int_one_esquerda = margem_inferior_int_one_esquerda
            vconf.tempo_espera_one_esquerda = tempo_espera_one_esquerda
            vconf.margem_superior_ext_two_esquerda = margem_superior_ext_two_esquerda
            vconf.margem_inferior_ext_two_esquerda = margem_inferior_ext_two_esquerda
            vconf.margem_inferior_int_two_esquerda = margem_inferior_int_two_esquerda
            vconf.tempo_espera_two_esquerda = tempo_espera_two_esquerda
            vconf.margem_superior_ext_three_esquerda = margem_superior_ext_three_esquerda
            vconf.margem_inferior_ext_three_esquerda = margem_inferior_ext_three_esquerda
            vconf.margem_inferior_int_three_esquerda = margem_inferior_int_three_esquerda
            vconf.tempo_espera_three_esquerda = tempo_espera_three_esquerda
            
            # Configurações do Quadro
            vconf.t_subida_quadro = t_subida_quadro
            vconf.t_descida_quadro = t_descida_quadro
            vconf.duty_subida_min_quadro = duty_subida_min_quadro
            vconf.duty_subida_max_quadro = duty_subida_max_quadro
            vconf.duty_descida_min_quadro = duty_descida_min_quadro
            vconf.duty_descida_max_quadro = duty_descida_max_quadro
            vconf.compensar_negativo_habilitado_quadro = compensar_negativo_habilitado_quadro
            vconf.compensar_positivo_habilitado_quadro = compensar_positivo_habilitado_quadro
            vconf.compensar_negativo_quadro = compensar_negativo_quadro
            vconf.compensar_positivo_quadro = compensar_positivo_quadro
            vconf.margem_superior_ext_one_quadro = margem_superior_ext_one_quadro
            vconf.margem_inferior_ext_one_quadro = margem_inferior_ext_one_quadro
            vconf.margem_inferior_int_one_quadro = margem_inferior_int_one_quadro
            vconf.tempo_espera_one_quadro = tempo_espera_one_quadro
            vconf.margem_superior_ext_two_quadro = margem_superior_ext_two_quadro
            vconf.margem_inferior_ext_two_quadro = margem_inferior_ext_two_quadro
            vconf.margem_inferior_int_two_quadro = margem_inferior_int_two_quadro
            vconf.tempo_espera_two_quadro = tempo_espera_two_quadro
            vconf.margem_superior_ext_three_quadro = margem_superior_ext_three_quadro
            vconf.margem_inferior_ext_three_quadro = margem_inferior_ext_three_quadro
            vconf.margem_inferior_int_three_quadro = margem_inferior_int_three_quadro
            vconf.tempo_espera_three_quadro = tempo_espera_three_quadro
            
            # Default               
            if v2_configuracao_id:         
                vconf.updated_by = request.user.id
                vconf.updated_at = datetime.datetime.now()
            else:
                vconf.created_by = request.user.id
                vconf.created_at = datetime.datetime.now()
            vconf.save()
            
            doLog('V2 Calibrada', f'V2 #{v2.id} .O Usuário <b>@{request.user.first_name}</b> add uma calibração nesta automação.', 1) # Success

            messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')
            
            if not automation_type:
                automation_type = 2
                
            return redirect('V2IndexView', automation_type)
    
    except Exception as e:        
        messages.add_message(request, messages.ERROR, f'Ocorreu um erro na hora de criar um novo registro, o erro foi o seguinte: {e}')
        return redirect('V2IndexView', automation_type)
        