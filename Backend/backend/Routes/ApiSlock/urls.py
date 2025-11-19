from django.urls import path
from backend.Controller import ApiSlockController as api

urlpatterns = [
    path('login', api.login, name="ApiSlockLogin"),
    path('add/keyword', api.addKeyword, name="ApiSlockAddKeyword"),
    path('del/keyword', api.removeKeyword, name="ApiSlockDelKeyword"),
    path('sync/keyword', api.syncKeyword, name="ApiSlockSyncKeyword"),
    path('sync/locacao', api.syncLocacao, name="ApiSlockSyncLocacao"),
    path('pulse/gate/', api.pulsoPortoes, name="ApiSlockPulsoPortoes"),
    path('sync/user/app', api.userApp, name="ApiSlockUserApp"),
    path('edit/perfil/app', api.changePerfilApp, name="ApiSlockChangePassword"),
    path('sync/ping', api.ping, name="ApiSlockPing"),
    path('reserva', api.reserva, name="ApiSlockReserva"),
]
