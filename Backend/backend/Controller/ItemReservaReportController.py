import datetime
import os
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.Controller.BaseController import saveFile, DateSTR2Datetime
from backend.models import MovimentoEstoque, TIPO_MOV_ESTOQUE_CHOICES, Produto, Client
from backend.models_views import ItemReserva, SaldoEstoque
from django.views.decorators.http import require_http_methods
from backend.Controller.BaseController import doLog
from slock.settings import DOMAIN_ASSETS, BASE_DIR

@login_required
def indexView(request):
    
    data = ItemReserva.objects.all()

    context = {
        'dados': data,
        'today': datetime.datetime.now()
    }

    return render(request, 'ItemReservaReport/index.html', context)
