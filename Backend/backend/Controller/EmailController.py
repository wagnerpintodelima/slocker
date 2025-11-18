from django.utils import timezone
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
from backend.models import Automation, Client, HU, AutomationType, UserApp, Slot, AuthUser, Call, Tecnico
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos
from django.core import serializers
from django.template.loader import render_to_string
import smtplib
from email.message import EmailMessage
from django.http import JsonResponse
from backend.Controller.BaseController import doLog

def atendimentoAction(request):
    
    authUsers = AuthUser.objects.filter(is_active=True)
    
    dados = []
    
    for authUser in authUsers:
        tecnico = Tecnico.objects.get(user_auth=authUser)                
        
        today = datetime.datetime.now()
        today = today.replace(hour=23, minute=0, second=0, microsecond=0)
        
        calls = Call.objects.exclude(status=1).filter(
            tecnico=tecnico,
            call_at__lte=today
        )
        
        dados.append({
            'tecnico': tecnico,
            'calls': calls,
            'chamados': len(calls)
        })
        
        # Colocando esses registros para atrasados
        for call in calls:
            print(f'ID:{call.id} \t CallAt: {call.call_at.strftime("%d/%m/%Y %H:%M")} \t Atual:{today.strftime("%d/%m/%Y %H:%M")}')
            call.status = 2 # Atraso
            call.save()
    
    # Renderizar o template com variáveis
    contexto = {        
        'dados': dados,        
        'today': datetime.datetime.now()
    }        
    
    mensagem_html = render_to_string("Email/atendimento.html", contexto)
    mensagem_texto = "Seu email não suporta esse relatório."

    # Configurações do e-mail
    EMAIL_REMETENTE = "wagnerdelima2@gmail.com"
    EMAIL_SENHA = "ohni rwrg lksg qvdz"    
    
    # 'jordaofelps@gmail.com',
    # 'marcelo_mrl.2010@hotmail.com',
    # 'douglassci20@gmail.com',
    # 'auten.automacaoetecnologia@gmail.com',
    # 'douglas@autenpro.com.br',
    # 'wagner@autenpro.com.br'
        
    gerentes = [        
        'wagner@autenpro.com.br',        
        'jordaofelps@gmail.com',
        'marcelo_mrl.2010@hotmail.com',
        'douglassci20@gmail.com',
        'auten.automacaoetecnologia@gmail.com',
        'douglas@autenpro.com.br'
    ]
    
    for email in gerentes:
    
        # Criando a mensagem
        msg = EmailMessage()
        msg["Subject"] = "Relatório diário de Atendimentos"
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = email

        # Define o conteúdo como texto simples e adiciona o HTML como alternativa
        msg.set_content(mensagem_texto)
        msg.add_alternative(mensagem_html, subtype="html")

        # Conectar ao servidor SMTP e enviar
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_REMETENTE, EMAIL_SENHA)
                server.send_message(msg)
            print("E-mail enviado com sucesso!")
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
    
    
    doLog('+ATENDIMENTOS', f'<b>AUTO MESSAGE</b> - Relatório diário de atendimentos pendentes enviado para a gerência!', 2) # info
    
    return JsonResponse({
        'status': 200,
        'description': 'Email Enviado com sucesso'
    })

def test(request):        
    """
    Essa tassk é só para testar o modelo que vai por email
    """
    authUsers = AuthUser.objects.filter(is_active=True)
    
    dados = []
    
    for authUser in authUsers:
        tecnico = Tecnico.objects.get(user_auth=authUser)
        calls = Call.objects.exclude(status=1).filter(tecnico=tecnico)
        
        dados.append({
            'tecnico': tecnico,
            'calls': calls,
            'chamados': len(calls)
        })
    
    # Renderizar o template com variáveis
    contexto = {        
        'dados': dados,        
        'today': datetime.datetime.now()
    }    
    
    return render(request, 'Email/atendimento.html', contexto)



