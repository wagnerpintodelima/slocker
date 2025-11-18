import datetime
import json
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from backend.models import Automation, Client, HU, AutomationType, UserApp, Slot
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers

@login_required
def indexView(request):
    
    excluir = ['VicSensor V1', 'Slock', 'AlarmBar']        
    data = AutomationType.objects.filter(status=True).order_by('description')
    data_filtrada = data.exclude(description__in=excluir)  # Se for um QuerySet

    context = {
        'data': data_filtrada
    }

    return render(request, 'Automation/index.html', context)

@login_required
def newView(request):

    clients = Client.objects.filter(status=True)
    automationTypes = AutomationType.objects.filter(status=True)

    context = {
        'companies': clients,
        'automationTypes': automationTypes
    }
    return render(request, 'Automation/new.html', context)

@login_required
def SaveAction(request):

    if request.method == 'POST':
        client_id = request.POST.get('client_id', None)
        automation_type_id = request.POST.get('automation_type_id', None)
        name = request.POST.get('name', None)
        short_name = request.POST.get('short_name', None)
        ip = request.POST.get('ip', None)
        subnet = request.POST.get('subnet', None)
        gateway = request.POST.get('gateway', None)
        mac = request.POST.get('mac', None)
        type_location = request.POST.get('type_location', 0)
        description = request.POST.get('description', None)
        status = request.POST.get('status', 0)

        if not client_id:
            messages.add_message(request, messages.ERROR, 'Empresa é obrigatório!')
            return redirect('AutomationNewAction')

        if not automation_type_id:
            messages.add_message(request, messages.ERROR, 'Tipo de Automação é obrigatório!')
            return redirect('AutomationNewAction')

        client = Client.objects.get(id=client_id)
        automationType = AutomationType.objects.get(id=automation_type_id)

        item = Automation()
        item.client = client
        item.automation_type = automationType
        item.name = name
        item.ip = ip
        item.subnet = subnet
        item.gateway = gateway
        item.mac = mac
        item.short_name = short_name
        item.description = description
        item.type_location = type_location
        item.status = status
        item.created_by = request.user.id
        item.created_at = datetime.datetime.now()
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro salvo com sucesso!')

    return redirect('AutomationIndexView')

@login_required
def editView(request, automation_id):

    item = Automation.objects.get(id=automation_id)
    companies = Client.objects.filter(status=True)
    automationTypes = AutomationType.objects.filter(status=True)

    context = {
        'item': item,
        'companies': companies,
        'automationTypes': automationTypes
    }

    return render(request, 'Automation/edit.html', context)

@login_required
def editAction(request):

    if request.method == 'POST':
        automation_id = request.POST.get('automacao_id', None)
        client_id = request.POST.get('client_id', None)
        automation_type_id = request.POST.get('automation_type_id', None)
        name = request.POST.get('name', None)
        short_name = request.POST.get('short_name', None)
        ip = request.POST.get('ip', None)
        subnet = request.POST.get('subnet', None)
        gateway = request.POST.get('gateway', None)
        mac = request.POST.get('mac', None)
        type_location = request.POST.get('type_location', None)
        description = request.POST.get('description', None)
        status = request.POST.get('status', 0)

        if not automation_id:
            messages.add_message(request, messages.ERROR, 'Automação é obrigatório!')
            return redirect('AutomationEditAction')

        item = Automation.objects.get(id=automation_id)

        if not client_id:
            messages.add_message(request, messages.ERROR, 'Empresa é obrigatório!')
            return redirect('AutomationNewAction')

        if not automation_type_id:
            messages.add_message(request, messages.ERROR, 'Tipo de Automação é obrigatório!')
            return redirect('AutomationNewAction')

        client = Client.objects.get(id=client_id)
        automationType = AutomationType.objects.get(id=automation_type_id)

        item.client = client
        item.automation_type = automationType
        item.name = name
        item.ip = ip
        item.subnet = subnet
        item.gateway = gateway
        item.mac = mac
        item.short_name = short_name
        item.description = description
        item.type_location = type_location
        item.status = status
        item.updated_by = request.user.id
        item.updated_at = datetime.datetime.now()
        item.save()

        messages.add_message(request, messages.SUCCESS, 'Registro atulizado com sucesso!')

    return redirect('AutomationIndexView')

@login_required
def deleteAction(request, hu_id):

    try:
        HU.objects.get(id=int(hu_id)).delete()

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
def huView(request, automation_id):

    automation = Automation.objects.get(id=automation_id)

    hus = HU.objects.filter(automation=automation).order_by('descricao')

    users_app = UserApp.objects.filter(status=True).order_by('name')
    users_app_serializado = serializers.serialize('json', users_app)

    array = []
    for hu in hus:
        array.append({
            'id': hu.id,
            'description': hu.descricao,
            'keys': hu.keys,
            'name': hu.user_app.name,
            'cpf': hu.user_app.cpf,
            'telefone': hu.user_app.phone_number,
            'signature': hu.user_app.signature,
            'created_at': hu.created_at.strftime('%d/%m/%Y %H:%M:%S')
        })

    context = {
        'automation': automation,
        'users_app': users_app_serializado,
        'hus': json.dumps(array),
        'endereco': "{},{},{}".format(automation.client.street, automation.client.house_number,automation.client.neighborhood),
        'cidade': "{}-{}".format(automation.client.city, automation.client.uf_description)
    }
    return render(request, 'Automation/hu_list.html', context)

@login_required
def huSaveAction(request):

    try:
        if request.method == 'GET':
            automation_id = request.GET.get('automation_id', None)
            description = request.GET.get('description', None)
            keys = request.GET.get('keys', None)
            user_app_id = request.GET.get('user_app', None)

            if not automation_id:
                context = {
                    'status': 401,
                    'description': 'É necessário informar a automação!'
                }
                return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

            if not user_app_id:
                context = {
                    'status': 401,
                    'description': 'É necessário informar o usuário responsável pelo apartamento!'
                }
                return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

            automation = Automation.objects.get(id=automation_id)
            userApp = UserApp.objects.get(id=user_app_id)

            # Validações
            # verificar se já existe
            inBD = False
            try:
                inBD = HU.objects.get(automation=automation,descricao=description)
            except ObjectDoesNotExist:
                pass

            if inBD:
                context = {
                    'status': 401,
                    'description': f"HU {description} já existe!"
                }
                return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

            #máximo 105 hus
            registers = HU.objects.filter(automation=automation).count()
            if registers > 105:
                context = {
                    'status': 401,
                    'description': 'Atingiu o máximo de registros. 105.'
                }
                return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

            # descrição 5 caracteres
            if len(description) > 5:
                context = {
                    'status': 401,
                    'description': 'A descrição pode ter no máximo 5 caracteres.'
                }
                return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

            # keys 63 caracteres
            if len(description) > 31:
                context = {
                    'status': 401,
                    'description': 'As keys podem ter no máximo 31 caracteres.'
                }
                return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

            hu = HU()
            hu.automation = automation
            hu.descricao = description
            hu.keys = keys
            hu.user_app = userApp
            hu.created_by = request.user.id
            hu.created_at = datetime.datetime.now()
            hu.save()

            context = {
                'status': 200,
                'description': 'Salvo com sucesso',
                'id': hu.id,
                'created_at': hu.created_at.strftime('%d/%m/%Y %H:%M:%S')
            }
        else:
            context = {
                'status': 401,
                'description': 'Método de envio inválido!'
            }
    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@csrf_exempt
def sendToMqttAction(request):
    try:
        if request.method == 'POST':
            str_data = list(request.POST.keys())[0]
            data = json.loads(str_data)

            if not data['automation']:
                context = {
                    'status': 401,
                    'description': 'É necessário informar a automação!'
                }
                return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

            automation = Automation.objects.get(id=data['automation'])

            next_codigo = 1
            ultimo_registro = Delivery.objects.order_by('-id').first()

            if ultimo_registro:
                next_codigo = int(ultimo_registro.codigo) + 1

            hus = []
            for i, hu in enumerate(data['hus']):
                hus.append({
                    'index': f"{i:03}",
                    'descricao': remover_acentos(hu['description']),
                    'nome': remover_acentos(hu['name']),
                    'cpf': hu['cpf'],
                    'telefone': hu['telefone'],
                    'signature': str(hu['signature']).zfill(5),
                    'keys': hu['keys']
                })

            packageMqtt = {
                'mac': automation.mac,
                'function': 'sync_hu',
                'hu': hus,
                'codigo': f"{next_codigo:05}",
                'address': remover_acentos(data['address']),
                'city': remover_acentos(data['city'])
            }

            mqttSendDataToDevice(json.dumps(packageMqtt))

            context = {
                'status': 200,
                'description': 'Pacote enviado em bom sucesso! Aguarde 1 minuto para processar os dados na automação!'
            }
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

        else:
            context = {
                'status': 401,
                'description': 'Método de envio inválido'
            }
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@login_required
def editSlotAction(request, automation_id):

    item = Automation.objects.get(id=automation_id)

    try:
        slots = Slot.objects.filter(automation=item).order_by('id_in_array_slots')
        hus = HU.objects.filter(automation=item)

        context = {
            'automation': item,
            'slots': serialize('json', slots),  # Serialize queryset to JSON
            'hus': serialize('json', hus)  # Serialize queryset to JSON
        }

    except Slot.DoesNotExist:
        context = {
            'automation': item,
            'slots': json.dumps([]),
            'hus': json.dumps([]),
        }


    return render(request, 'Automation/slot.html', context)

@login_required
@require_http_methods(["GET"])
def editSlotSaveAction(request):

    try:
        str_data = list(request.GET.keys())[0]
        data = json.loads(str_data)

        automation_id = data['automation_id']
        id_in_array_slots = data['id_in_array_slots']
        name = data['name']
        solenoide_address = data['solenoide_address']
        model = data['model']
        password = data['password']
        description = data['description'] # Apartamento
        status = data['status']

        if not automation_id or not id_in_array_slots or not name or not solenoide_address or not model or not status:
            context = {
                'status': 401,
                'description': 'Formulário Inválido!'
            }
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

        if (password and not description) or (not password and description):
            context = {
                'status': 401,
                'description': 'Formulário Inválido!'
            }
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

        if password and len(password) != 5:
            context = {
                'status': 401,
                'description': 'Formulário Inválido!'
            }
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

        automation = Automation.objects.get(id=automation_id)

        # Excluindo Outros que tem os mesmos dados
        try:
            Slot.objects.get(automation=automation, id_in_array_slots=id_in_array_slots).delete()
        except ObjectDoesNotExist:
            pass

        try:
            Slot.objects.get(automation=automation, name=name).delete()
        except ObjectDoesNotExist:
            pass

        try:
            Slot.objects.get(automation=automation, solenoide_address=solenoide_address).delete()
        except ObjectDoesNotExist:
            pass

        slot = Slot()
        slot.automation = automation
        slot.id_in_array_slots = id_in_array_slots
        slot.name = name[0:3]
        slot.solenoide_address = solenoide_address[0:4]
        slot.model = int(model)
        slot.status = int(status)
        slot.created_by = request.user.id
        slot.created_at = datetime.datetime.now()
        if password and description:
            slot.password = f"{password:05}"
            slot.description = description[0:6]
        slot.save()

        context = {
            'status': 200,
            'description': 'Salvo com sucesso',
            'id': slot.id,
            'created_at': slot.created_at.strftime('%d/%m/%Y %H:%M:%S')
        }

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@login_required
def editSlotDeleteAction(request, slot_id):

    try:
        Slot.objects.get(id=int(slot_id)).delete()
        context = {
            'status': 200,
            'description': 'Excluído com sucesso!'
        }
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@login_required
@require_http_methods(["GET"])
def sendToMqttSlotsAction(request):
    try:
        str_data = list(request.GET.keys())[0]
        data = json.loads(str_data)

        if not data['automation']:
            context = {
                'status': 401,
                'description': 'É necessário informar a automação!'
            }
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

        automation = Automation.objects.get(id=data['automation'])

        slots = Slot.objects.filter(automation=automation).order_by('id_in_array_slots')

        slots_arr = []
        for i, slot in enumerate(slots):
            slots_arr.append({
                'id_in_array_slots': slot.id_in_array_slots,
                'name': slot.name[0:3],
                'solenoide_address': slot.solenoide_address[0:4],
                'model': int(slot.model),
                'status': int(slot.status)
            })

        packageMqtt = {
            'mac': automation.mac,
            'function': 'sync_slots',
            'slots': slots_arr
        }

        mqttSendDataToDevice(json.dumps(packageMqtt))

        context = {
            'status': 200,
            'description': 'Pacote enviado em bom sucesso! Aguarde 1 minuto para processar os dados na automação!',
            'json_sended_for_uC': packageMqtt
        }
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@login_required
@require_http_methods(["GET"])
def sendToMqttSlotsEditAction(request):
    try:
        str_data = list(request.GET.keys())[0]
        data = json.loads(str_data)

        if not data['slot_id']:
            context = {
                'status': 401,
                'description': 'É necessário informar um slot!'
            }
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")


        slot = Slot.objects.get(id=data['slot_id'])
        automation = slot.automation

        if not data['empty']:

            # Verificar se já existe no banco com essa senha
            slots = Slot.objects.filter(automation=automation).order_by('id_in_array_slots')
            pswd = data['password'][0:5]
            for _slot in slots:
                if _slot.password == pswd:
                    context = {
                        'status': 401,
                        'description': f'Essa senha({pswd}) está em uso no momento!'
                    }
                    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

            slot.description = data['description'][0:5]
            slot.password = pswd
            slot.status = int(data['status'])
        else:
            slot.description = ""
            slot.password = ""
            slot.status = 0
        slot.save()

        # Verificando se o slot foi salvo corretamente
        slot.refresh_from_db()

        #### Atualizando uC
        slots = Slot.objects.filter(automation=automation).order_by('id_in_array_slots')
        # Acessando um valor específico | {'mac': 'CA:DE:CA:FE:CO:FE'}
        mac = automation.mac

        array = []
        for slot_ in slots:
            if slot_.password:
                array.append({
                    "id_in_array_slots": int(slot_.id_in_array_slots),
                    "descricao": remover_acentos(slot_.description),
                    "password": remover_acentos(slot_.password),
                    "status": int(slot_.status)
                })

        packageMqtt = {
            'mac': mac,
            'function': 'sync_pswd',
            'slots': array
        }

        mqttSendDataToDevice(json.dumps(packageMqtt))

        context = {
            'status': 200,
            'description': 'Pacote enviado em bom sucesso',
            'json_sended_for_uC': packageMqtt
        }

        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        context = {
            'status': 500,
            'description': str(e)
        }
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")

@login_required
def showJsonCheckoutFromFileView(request, automation_id):
    automation = Automation.objects.get(id=automation_id)

    context = {
        'automation': automation
    }

    return render(request, 'Automation/editFileCheckout.html', context)

@login_required
@require_http_methods(["POST"])
def sendHandlerFileCheckout(request):

    automation_id = request.POST.get('automation_id', None)
    json_str = request.POST.get('json_str', None)

    automation = Automation.objects.get(id=automation_id)

    if json_str and automation:
        json_str = json_str.strip()
        try:
            jsonObject = json.loads(json_str)

            packageMqtt = {
                'mac': automation.mac,
                'function': 'fn_set_checkouts',
                'checkouts': jsonObject['checkouts']
            }

            mqttSendDataToDevice(json.dumps(packageMqtt))
            messages.add_message(request, messages.SUCCESS, 'Enviado em Bom Sucesso!')

        except Exception as e:
            messages.add_message(request, messages.ERROR, str(e))
            return redirect('AutomationIndexView')

    else:
        messages.add_message(request, messages.ERROR, 'Dados inválidos!')



    return redirect('AutomationIndexView')