from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.models import Reserva, Espaco, EspacoItem
from datetime import datetime
from django.utils import timezone
from django.http import HttpResponse
import json

@login_required
def indexView(request):
    
    agora = timezone.now()
    reservas_qs = Reserva.objects.filter(data_fim__gte=agora).order_by('data_inicio')

    reservas = []
    for reserva in reservas_qs:
        espaco = getattr(reserva, 'espaco', None)                
        
        itens_do_espaco = EspacoItem.objects.filter(espaco=espaco)
        itens = []
        
        for item in itens_do_espaco:
            itens.append({
                'id': item.id,
                'descricao': item.descricao,
                'quantidade': item.quantidade
            })
        
        item = {
            'id': reserva.id,
            'espaco': {
                'id': espaco.id if espaco else None,
                'nome': espaco.nome if espaco else None,
                'valor_reserva': espaco.valor_reserva if espaco else None,
                'regras': espaco.regras if espaco else None,
                'itens': itens if itens else []
            },
            'data_inicio': reserva.data_inicio.strftime('%d/%m/%Y %Hh:%Mm') if reserva.data_inicio else None,
            'data_fim': reserva.data_fim.strftime('%d/%m/%Y %Hh:%Mm') if reserva.data_fim else None,
            'status': reserva.status,
            'created_at': reserva.created_at.strftime('%d/%m/%Y %Hh:%Mm') if reserva.created_at else None
        }
        reservas.append(item)
    
    
    context = {
        'reservas': reservas_qs
    }
    
    return render(request, 'Reserva/index.html', context)


@login_required
def aprovarView(request, reserva_id):    
    reserva = Reserva.objects.get(id=reserva_id)
    reserva.status = 1  # Aprovar
    reserva.save()
    
    messages.add_message(request, messages.SUCCESS, 'Reserva APROVADA com sucesso!')
    
    return redirect('ReservaIndexView')

@login_required
def negarView(request, reserva_id):
    reserva = Reserva.objects.get(id=reserva_id)
    reserva.status = 2  # Negar
    reserva.save()
    
    messages.add_message(request, messages.SUCCESS, 'Reserva NEGADA com sucesso!')
    
    return redirect('ReservaIndexView')

@login_required
def deleteAction(request, reserva_id):
    
    Reserva.objects.get(id=reserva_id).delete()    
    
    messages.add_message(request, messages.SUCCESS, 'Reserva EXCLUÍDA com sucesso!')
    
    context = {
        'status': 200,
        'descricao': 'Excluído com sucesso'
    }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
