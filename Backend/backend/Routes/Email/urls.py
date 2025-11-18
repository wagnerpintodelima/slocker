from django.urls import path
from backend.Controller import EmailController as e

urlpatterns = [
    path('atendimento', e.atendimentoAction, name="EmailAtendimentoAction")
]
