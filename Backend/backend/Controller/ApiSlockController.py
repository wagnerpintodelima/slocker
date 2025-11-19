import logging
import os
import locale
import json
import threading
import time
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
import pytz
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.models import HU, UserApp, Keyword, Locacao, Slot, Client, Automation, LogGate
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos, generate_password
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from backend.Controller.BaseController import getHash
from slock.settings import DOMAIN_ASSETS, BASE_DIR
from backend.Controller.UserAppController import _PATH_FILE_USER_APP
from backend.Controller.BaseController import saveFileBase64

@csrf_exempt
@require_http_methods(["POST"])
def login(request):

    """
    Essa fn é executada em todos os apps, ela faz o login deles.
    É SUPER IMPORTANTE!!!
    """
    
    try:        
        
        cpf = request.POST.get('cpf', None)
        password = request.POST.get('password', None)
        so = request.POST.get('so', None)
        
        userApp = UserApp.objects.filter(cpf=cpf, password=password).first()
        
        if userApp:
            
            # Definindo o locale para português do Brasil
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            
            # Inicializar variáveis
            keys = [None, None, None]
            keys_created_at = [None, None, None]

            # Obter as palavras-chave ativas relacionadas ao usuário
            keywords = Keyword.objects.filter(hu=userApp.hu, status=True)[:3]  # Limitar a 3 resultados

            # Atribuir valores às variáveis
            for i, k in enumerate(keywords):
                keys[i] = k.word
                keys_created_at[i] = k.created_at.strftime('%d de %B de %Y, %Hh:%Mm')

            # Acessar valores
            key1, key2, key3 = keys
            key1_created_at, key2_created_at, key3_created_at = keys_created_at
            
            print(f'Key1: {key1_created_at} \n Key2: {key2_created_at} \n Key3: {key3_created_at}')            
            
            # Tem locação ativa?
            hasLocacoes = Locacao.objects.filter(hu=userApp.hu,client=userApp.client).exists()
            dataLocacoes = []
            
            if hasLocacoes:
                locacoes = Locacao.objects.filter(hu=userApp.hu,client=userApp.client)
                
                for l in locacoes:
                    item = {
                        'id_locacao_operations': l.id, # ID da locação no operation
                        'id_locacao': l.locacao_id, # ID da locação na raspberry                        
                        'slot': l.slot, # ID do slot na raspberry                        
                        'hu': l.hu, # ID da HU na raspberry
                        'password': l.password,
                        'keyword': l.keyword if l.keyword else '###',
                        'delivered_at': l.delivered_at.strftime('%d de %B de %Y, %Hh:%Mm') if l.delivered_at else None,
                        'created_at': l.created_at.strftime('%d de %B de %Y, %Hh:%Mm'),
                        'status': l.status
                    }
                    dataLocacoes.append(item)
            
            if so and so != userApp.so and so != '':
                userApp.so = so
            
            
            # Registra o last access do usuario
            userApp.updated_at = timezone.now()
            userApp.save()
            
            return JsonResponse({
                'status': 200,
                'description': 'Acesso autorizado!',
                'id': userApp.id,
                'is_doorman': userApp.is_doorman,
                'name': userApp.name,
                'picture': f'{DOMAIN_ASSETS}/user_app/{userApp.picture}.png',
                'statusCadastro': userApp.status,
                'phone': userApp.phone_number,
                'signature': userApp.signature,
                'so': userApp.so,
                'email': userApp.email,
                'hu': userApp.hu,                
                'key1': key1,
                'key2': key2,
                'key3': key3,
                'key1_created_at': key1_created_at,
                'key2_created_at': key2_created_at,
                'key3_created_at': key3_created_at,
                'locacoes': dataLocacoes
            })     
        else:
            return JsonResponse({
              'status': 500,
                'description': 'O CPF ou a senha está errado! Fale com seu síndico e verifique os dados de acesso'
            })

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def addKeyword(request):

    try:        

        id = request.POST.get('id', None)        
        word = request.POST.get('word', None)        

        if not word or not id: 
            return JsonResponse({
                'status': 500,
                'description': 'Formulário inválido'
            })

        userApp = get_object_or_404(UserApp, id=id)        
        
        keyInBdExists = Keyword.objects.filter(word=word, client=userApp.client, status=True).exists()
        
        if keyInBdExists:
            return JsonResponse({
                'status': 500,
                'description': 'Palavra já existe no banco de dados!'
            })

        if Keyword.objects.filter(client=userApp.client, status=True).count() > 2:
            return JsonResponse({
                'status': 500,
                'description': 'Você já tem três palavras chaves!'
            })
        
        keyword = Keyword()
        keyword.client = userApp.client
        keyword.hu = userApp.hu
        keyword.word = word
        keyword.status = True
        keyword.created_at = datetime.now()
        keyword.created_by = userApp.id
        keyword.save()
        
        return JsonResponse({
            'status': 200,
            'description': 'Palavra adicionado com sucesso!'
        })
       

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def removeKeyword(request):

    try:        
        
        id = request.POST.get('id', None)        
        word = request.POST.get('word', None)
        
        if not word or not id: 
            return JsonResponse({
                'status': 500,
                'description': 'Formulário inválido'
            })

        userApp = get_object_or_404(UserApp, id=id)        
        
        keyInBdExists = Keyword.objects.filter(word=word, client=userApp.client, status=True).exists()
        
        if not keyInBdExists:
            return JsonResponse({
                'status': 500,
                'description': 'Palavra não existe no banco de dados!'
            })

        
        keywordInBD = Keyword.objects.get(word=word, client=userApp.client, status=True)
        try: # Se não tiver preso em nenhuma locação excluí!
            keywordInBD.delete()        
            excluiu = True
        except Exception as e: # tá preso em uma locação, apenas desativamos
            excluiu = False            
        finally:        
            
            if not excluiu:                
                keywordInBD.status = False
                keywordInBD.updated_at = timezone.now()
                keywordInBD.save()
            
            key1 = None
            key2 = None
            key3 = None
            
            keywords = Keyword.objects.filter(hu=userApp.hu, status=True)
            
            for i,k in enumerate(keywords):
                if i == 0:
                    key1 = k.word
                elif i == 1:                    
                    key2 = k.word
                elif i == 2:
                    key3 = k.word
                else:
                    break
            
            return JsonResponse({
            'status': 200,
            'description': 'Palavra removida com sucesso!',
            'key1': key1,
            'key2': key2,
            'key3': key3
        })
       

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def syncLocacao(request):

    try:        
        
        js = json.loads(request.body)
        
        client_id = js['client_id']
        locacao_id = js['locacao_id']
        slot = js['slot']
        hu = js['hu']
        keyword = js['keyword']
        password = js['password']
        delivered_at = js['delivered_at']
        status = js['status']
        
        if not hu or not slot or not password or not client_id: 
            return JsonResponse({
                'status': 500,
                'description': 'Formulário inválido'
            })
        
        print('Dados OK')
        
        condominio = Client.objects.get(id=client_id)
        
        LocacaoInBdExists = Locacao.objects.filter(locacao_id=locacao_id, client=condominio).exists()
        
        if LocacaoInBdExists: # Edita a locacao
            
            print('Editando uma locacao')
            
            locacao = Locacao.objects.get(locacao_id=locacao_id, client=condominio)
            locacao.locacao_id = locacao_id
            locacao.slot = slot
            locacao.hu = hu
            locacao.keyword = keyword
            locacao.password = password
            locacao.delivered_at = delivered_at
            locacao.status = status            
            locacao.save()
            
            return JsonResponse({
                'status': 200,
                'description': 'Editada nova locação com sucesso!'
            })
                                   
        else: # cria uma nova locacao
            
            print('Criando uma nova locacao')                        
            
            locacao = Locacao()
            locacao.client = condominio
            locacao.locacao_id = locacao_id
            locacao.slot = slot
            locacao.hu = hu
            locacao.keyword = keyword
            locacao.password = password
            locacao.delivered_at = delivered_at
            locacao.status = status
            locacao.created_at = timezone.now()                            
            locacao.save()

            
            print('Retorno 200')
            return JsonResponse({
                'status': 200,
                'description': 'Criada nova locação com sucesso!'
            })
    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }
        print('Retorno 500')


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["GET"])
def syncKeyword(request):

    try:        
        
        js = json.loads(request.body)
        
        client_id = js['client_id']
        
        client = Client.objects.get(id=client_id)
        auto = Automation.objects.get(client=client)
        hus = HU.objects.filter(automation=auto)
        
        data = []
        
        for hu in hus:
            
            # Data de um mês atrás
            um_mes_atras = datetime.now() - timedelta(days=30)
            
            keysExists = Keyword.objects.filter(hu=hu, created_at__gte=um_mes_atras).exists()            
            
            if keysExists:
                
                keys = Keyword.objects.filter(hu=hu, created_at__gte=um_mes_atras)
                
                for key in keys:
                
                    item = {                        
                        'hu_id': hu.hu_id,
                        'word': key.word,
                        'keyword_id': key.id,
                        'status': key.status
                    }
                    
                    data.append(item)
            
        print(data)    
        return JsonResponse({
            'status': 200,
            'data': data
        })
        
        
    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def pulsoPortoes(request):
    
    try: 

        # logging.basicConfig(
        #     filename="/home/slock/public_html/pulse_gate.log",  # Nome do arquivo de log
        #     level=logging.INFO,
        #     format="%(asctime)s - %(levelname)s - %(message)s"
        # )

        dados = json.loads(request.body.decode('utf-8'))
        authorization_header = request.headers.get('Authorization', None)
        
        if authorization_header != getHash():
            # Fazer algo com o valor
            return JsonResponse({
                'status': 403,
                'description': r"Forbidden! Be careful, we know where you are!"
            })

        # Acessando um valor específico | {"cpf":073.969.489-83,"fn":"people|enter|leave"}
        
        userApp = UserApp.objects.get(cpf=dados.get('cpf', None))
        fn = dados.get('fn', None)              
        
        # Enviar comando para mqtt
        logging.info(f'\nEnviando comando MQTT\n')
        if fn == 'people':
            mqtt_topic = 'cbs/interfone/uc/receiver'        
            mqtt_msg = '{"mac": "CA:FE:C0:FF:EE:EA",  "function": "relay","pulse": true,"pulse_delay": 1000,"state": false,"relay_state_default": false}'
            mqttSendDataToDevice(mqtt_msg, mqtt_topic)
        elif fn == 'enter_car':
            mqtt_topic = 'bitz/energy_power/api/send'
            mqtt_msg = '{"mac":"CA:FE:C0:FF:EE:E4","read":false,"relay1":false,"relay2":false,"relay3":true,"red":0,"green":0,"blue":0}'
            mqttSendDataToDevice(mqtt_msg, mqtt_topic)
        elif fn == 'leave_car':
            logging.info(f'\n\tEntrou no Leave Car\n')
            mqtt_topic = 'bitz/energy_power/api/send'
            mqtt_msg = '{"mac":"CA:FE:C0:FF:EE:E4","read":false,"relay1":false,"relay2":true,"relay3":false,"red":0,"green":0,"blue":0}'
            mqttSendDataToDevice(mqtt_msg, mqtt_topic)
        
        # Salvar log no banco
        log = LogGate()
        log.client = userApp.client
        log.condomino = userApp.name
        log.hu = userApp.hu
        log.comando = fn
        log.created_at = timezone.now()
        log.save()
        
        return JsonResponse({
            'status': True,
            'description': 'Comando enviado com sucesso'
        })        
                
    except Exception as e:        
        return JsonResponse({
            'status': 0,
            'description': str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def userApp(request):
    
    print('\nSync User Apps\n')
    # logging.basicConfig(
    #     filename="/home/slock/public_html/condomino.log",  # Nome do arquivo de log
    #     level=logging.INFO,
    #     format="%(asctime)s - %(levelname)s - %(message)s"
    # )
    
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    
    try:        
    
        body = json.loads(request.body)        
        
        registro_bola_da_vez = None
        new = 0
        edit = 0
        
        for idx, js in enumerate(body):
            
            registro_bola_da_vez = js
            
            client_id = js['client_id']        
            nome = js['nome']
            hu = js['hu']
            cpf = js['cpf']
            telefone = js['telefone']
            is_doorman = js['is_doorman']
            created_at = js['created_at']
            status = js['status']
            
            if not client_id: 
                return JsonResponse({
                    'status': 500,
                    'description': 'Formulário inválido'
                })                        
            
            condominio = Client.objects.get(id=client_id)
            
            userAppExists = UserApp.objects.filter(client=condominio, cpf=cpf).exists()
            
            if userAppExists: # edit
                print(f'+1 \t Edit')
                logging.info(f'+1 \t Edit \t {nome}')
                edit += 1
                item = UserApp.objects.filter(client=condominio, cpf=cpf).first()            
                item.name = nome
                item.hu = hu
                item.cpf = cpf
                item.phone_number = telefone     
                item.is_doorman = is_doorman       
                item.status = status
                item.save()
                
            else: # Novo user app
                new += 1
                print(f'+1 \t New')
                logging.info(f'+1 \t New \t {nome}')
                item = UserApp()
                item.client = condominio
                item.name = nome
                item.password = '12345678'
                item.hu = hu
                item.cpf = cpf
                item.phone_number = telefone
                item.is_doorman = is_doorman
                item.created_at = datetime.strptime(created_at, '%Y-%d-%m %H:%M:%S')
                item.status = status
                item.save()
            
        print('\nEnd Sync User Apps\n')
        logging.info('\nEnd Sync User Apps\n')
        
        return JsonResponse({
            'status': 200,
            'processados': idx,
            'new': new,
            'edit': edit
        })
        
    except Exception as e:
        print('Retorno 500')
        print(registro_bola_da_vez)            
        
        logging.info(f'\nErro: {str(e)}\n')
        
        return JsonResponse({
            'status': 500,
            'description': str(e),
            'registro': registro_bola_da_vez
        })
               
@csrf_exempt
@require_http_methods(["POST"])
def changePerfilApp(request):

    try:        
        
        cpf = request.POST.get('cpf', None)
        password = request.POST.get('password', None)
        picture = request.POST.get('picture', None)
        
        userApp = UserApp.objects.filter(cpf=cpf).first()
        
        passwordChanged = False
        
        if userApp:

            # Definindo o locale para português do Brasil
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')                                    

            passwordChanged = userApp.password != password
            userApp.password = password
            
            if picture != 'null':
                
                try:
                    path = os.path.join(BASE_DIR, 'media/' + _PATH_FILE_USER_APP, userApp.picture + '.png')
                    os.remove(path)
                except Exception as er:
                    pass
                
                userApp.picture = saveFileBase64('media/' + _PATH_FILE_USER_APP, '.png', picture)                                 
                
            
            userApp.updated_at = datetime.now()
            userApp.save()
            
            return JsonResponse({
                'status': 200,
                'passwordChanged': passwordChanged,
                'description': 'Perfil alterado com sucesso!'
            })     
        else:
            return JsonResponse({
              'status': 500,
              'description': 'O CPF ou a senha está errado! Fale com seu síndico e verifique os dados de acesso'
            })

    except Exception as e:
        return JsonResponse({
            'status': 500,
            'description': str(e)
        })        
    
                
@csrf_exempt
@require_http_methods(["POST"])
def ping(request):

    try:      
        
        # logging.basicConfig(
        #     filename="/home/slock/public_html/ping.log",  # Nome do arquivo de log
        #     level=logging.INFO,
        #     format="%(asctime)s - %(levelname)s - %(message)s"
        # )          
        
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
        
        body = json.loads(request.body)       
        automation_id = body['automation_id']
        logging.info(f'\nid recebido: {automation_id}\n')                  
        
        if not automation_id:
            return JsonResponse({
              'status': 500,
              'description': 'Formulário inválido!'
            })
            
        automation = Automation.objects.get(id=automation_id)
        logging.info(f'\nid base de dados: {automation.id}\n')                  
        
        automation.updated_at = timezone.now()
        automation.save()      
        
        logging.info(f'\nhora da servidor: {timezone.now()}\n')                  
        logging.info(f'\nhora da automacao: {automation.updated_at}\n')                  
        
        return JsonResponse({
            'status': 200,
            'description': 'Registro atualizado com sucesso!'
        })

    except Exception as e:
        return JsonResponse({
            'status': 500,
            'description': str(e)
        })        
    
    






