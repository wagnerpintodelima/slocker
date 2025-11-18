from django.urls import path
from backend.Controller import MovimentoEstoqueController as movest

urlpatterns = [
    path('', movest.indexView, name="MovimentoEstoqueIndexView"),    
    path('new/', movest.newView, name="MovimentoEstoqueNewView"),
    path('save/', movest.saveAction, name="MovimentoEstoqueSaveAction"),        
    path('delete/<int:movimento_estoque_id>', movest.deleteView, name="MovimentoEstoqueDeleteView"),        
    path('delete', movest.deleteAction, name="MovimentoEstoqueDeleteAction"),    
]
