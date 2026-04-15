from django.urls import path
from backend.Controller import ApiAtronController as api

urlpatterns = [
    path('new', api.new, name="ApiAtronNew"), # Usado para receber novos hash's gps via QRcode
    path('handshake', api.handshake, name="ApiAtronHandshake"), # Toda vez que o GPS liga e tem wifi, nao requer dados de localizacao
    path('show', api.showHash, name="ApiAtronShowHash"), # Recebe os logs
    path('token', api.token, name="ApiAgrolineToken"), # Pega o token para o download
    path('download', api.download, name="ApiAgrolineDownload"), # Pega o token para o download
]
