from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from backend.models import V2, Sensor, Tela, ViagemInstalacaoKitChild, AtronDevice, AtronDeviceRegister, Log, Call, Tecnico, AuthUser, PosVenda
from datetime import datetime, timedelta
import re

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


@login_required
def mapaAgroLineView(request):
    return render(request, 'Dashboard/mapaAgroLine.html')


@login_required
def mapaAgroLineDevicesAction(request):
    updated_since = datetime.now() - timedelta(hours=24)
    registers = (
        AtronDeviceRegister.objects
        .filter(status=0, updated_at__gte=updated_since)
        .exclude(lat__isnull=True)
        .exclude(lon__isnull=True)
        .exclude(lat='')
        .exclude(lon='')
        .order_by('-updated_at')
    )

    def parse_coordinate(value):
        if value is None:
            return None

        match = re.search(r'-?\d+(?:[,.]\d+)?', str(value))
        if not match:
            return None

        try:
            return float(match.group(0).replace(',', '.'))
        except ValueError:
            return None

    devices = []
    skipped = []
    for register in registers:
        latitude = parse_coordinate(register.lat)
        longitude = parse_coordinate(register.lon)

        if latitude is None or longitude is None:
            skipped.append({
                'id': register.id,
                'device_number': register.device_number,
                'lat': register.lat,
                'lon': register.lon,
            })
            continue

        devices.append({
            'id': register.id,
            'device_number': register.device_number,
            'version_current': register.version_current,
            'latitude': latitude,
            'longitude': longitude,
            'satellites': register.satellites,
            'updated_at': register.updated_at.strftime('%d/%m/%Y %H:%M:%S') if register.updated_at else '',
        })

    return JsonResponse({
        'status': 200,
        'updated_at': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'total_found': registers.count(),
        'total_skipped': len(skipped),
        'skipped': skipped,
        'devices': devices,
    })
