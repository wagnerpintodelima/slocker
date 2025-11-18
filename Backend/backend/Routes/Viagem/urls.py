from django.urls import path
from backend.Controller import ViagemController as v

urlpatterns = [
    path('', v.indexView, name="ViagemIndexView"),
    path('new', v.newView, name="ViagemNewView"),
    path('save', v.saveAction, name="ViagemSaveAction"),
    path('edit/<int:viagem_id>', v.editView, name="ViagemEditView"),
    path('edit/save/<int:viagem_id>', v.editSaveAction, name="ViagemEditAction"),
    path('delete/<int:viagem_id>', v.deleteAction, name="ViagemDeleteAction"),
    
    # Início de viagem
    path('new/saida/<int:viagem_id>', v.saidaView, name="ViagemSaidaView"),
    path('save/saida/<int:viagem_id>', v.saveInicioAction, name="ViagemSaveSaidaAction"),
    
    # Acerto de Viagem
    path('new/chegada/<int:viagem_id>', v.chegadaView, name="ViagemChegadaView"),
    path('save/chegada/<int:viagem_id>', v.saveChegadaAction, name="ViagemSaveChegadaAction"),
    
    path('extrato/<int:viagem_id>', v.extratoView, name="ViagemExtratoView"),
    
    path('filter/', v.filterView, name="ViagemFilterView"),
    path('filter/search', v.filterAction, name="ViagemFilterAction"),
]
