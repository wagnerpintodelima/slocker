import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from backend.models import Automation, HU, AutomationType
from backend.Controller.MQTTController import mqttSendDataToDevice, remover_acentos, generate_password
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone


@csrf_exempt
@require_http_methods(["POST"])
def receiverCheckout(request):    
    
    context = {
        'status': 500,
        'description': str('ops')
    }


    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
