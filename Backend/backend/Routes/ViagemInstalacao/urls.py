from django.urls import path
from backend.Controller import ViagemInstalacaoController as v

urlpatterns = [
    path('<int:viagem_id>', v.indexView, name="ViagemInstalacaoIndexView"),
    path('new/<int:viagem_id>', v.newView, name="ViagemInstalacaoNewView"),
    path('save/<int:viagem_id>', v.saveAction, name="ViagemInstalacaoSaveAction"),
    path('edit/<int:viagem_instalacao_id>', v.editView, name="ViagemInstalacaoEditView"),
    path('edit/save/<int:viagem_instalacao_id>', v.editSaveAction, name="ViagemInstalacaoEditAction"),
    path('delete/<int:viagem_instalacao_id>', v.deleteAction, name="ViagemInstalacaoDeleteAction"),        
    
    # Finalizar Visita ao cliente
    path('finalizar/<int:viagem_instalacao_id>', v.finalizarView, name="ViagemInstalacaoFinalizarView"),        
    path('finalizar/save/<int:viagem_instalacao_id>', v.finalizarAction, name="ViagemInstalacaoFinalizarAction"),        
    
    path('view/<int:viagem_instalacao_id>', v.vView, name="ViagemInstalacaoView"),
    
    # Montagem do Kit
    path('montar/kit/<int:viagem_instalacao_id>', v.montarKitView, name="ViagemInstalacaoMontarKitView"),
    path('montar/kit/save/<int:viagem_instalacao_id>', v.saveKitAction, name="ViagemInstalacaoSaveKitAction"),
    path('montar/kit/delete/<int:viagem_instalacao_kit_child_id>', v.deleteKitChildAction, name="ViagemInstalacaoDelKitChildAction"),        
]
