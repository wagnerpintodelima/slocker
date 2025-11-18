from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.models import V2, Sensor, Tela, ViagemInstalacaoKitChild, AtronDevice, Log, Call, Tecnico, AuthUser, PosVenda
from datetime import datetime

@login_required
def indexView(request):
    
    v2_in_store = V2.objects.filter(automation__cliente_auten__isnull=True).count()
    tela_in_store = Tela.objects.filter(automation__cliente_auten__isnull=True).count()
    sensor_in_store = Sensor.objects.filter(automation__cliente_auten__isnull=True).count()
    gps_in_store = AtronDevice.objects.filter(automation__cliente_auten__isnull=True, status=True).count()
    
    v2_reserva_tecnico = ViagemInstalacaoKitChild.objects.filter(v2__isnull=False, status=0).count()
    tela_reserva_tecnico = ViagemInstalacaoKitChild.objects.filter(tela__isnull=False, status=0).count()
    sensores_reserva_tecnico = ViagemInstalacaoKitChild.objects.filter(sensor__isnull=False, status=0).count()
    
    logs = Log.objects.all().order_by('-id')[:30]  # Pega os 10 primeiros, ordenados pelo ID descrescente
    
    posvendas_atrasadas = PosVenda.objects.filter(data_programada_ligacao__lt=datetime.now(), status=0)            
    
    if request.user.is_superuser:
        calls = Call.objects.exclude(status=1)
    else:
        auth_user = AuthUser.objects.get(id=request.user.id)
        tecnicoLogado = Tecnico.objects.get(user_auth=auth_user)
        calls = Call.objects.exclude(status=1).filter(tecnico=tecnicoLogado)
    
    context = {
        'v2_in_store': v2_in_store,
        'tela_in_store': tela_in_store,
        'sensor_in_store': sensor_in_store,
        'gps_in_store': gps_in_store,
        'v2_reserva_tecnico': v2_reserva_tecnico,
        'tela_reserva_tecnico': tela_reserva_tecnico,
        'sensores_reserva_tecnico': sensores_reserva_tecnico,
        'logs': logs,
        'calls': calls,
        'posvendas_atrasadas': posvendas_atrasadas
    }
    
    return render(request, 'Dashboard/index.html', context)
