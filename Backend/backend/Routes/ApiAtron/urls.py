from django.urls import path
from backend.Controller import ApiAtronController as api

urlpatterns = [
    path('new', api.new, name="ApiAtronNew"), # Usado para receber novos hash's gps via QRcode    
    path('handshake', api.handshake, name="ApiAtronHandshake"), # Toda vez que o GPS liga e tem wifi, não requer dados de localização    
    path('show', api.showHash, name="ApiAtronShowHash"), # Recebe os logs
]
