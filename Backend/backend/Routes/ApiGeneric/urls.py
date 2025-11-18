from django.urls import path
from backend.Controller import ApiGenericController as api

urlpatterns = [
    path('wagner/setup', api.setupAction, name="ApiWagnerSetupAction"),
    path('wagner/send/comando', api.sendCommandAction, name="ApiWagnerSendCommandAction")
]
