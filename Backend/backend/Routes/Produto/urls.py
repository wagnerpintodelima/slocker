from django.urls import path
from backend.Controller import ProdutoController as p

urlpatterns = [
    path('', p.indexView, name="ProdutoIndexView"),
    path('new', p.newView, name="ProdutoNewView"),
    path('save', p.saveAction, name="ProdutoSaveAction"),
    path('edit/<int:produto_id>', p.editView, name="ProdutoEditView"),
    path('edit/save/<int:produto_id>', p.editAction, name="ProdutoEditAction"),
    path('componentes/<int:produto_id>', p.componentesView, name="ProdutoComponentsView"),
    path('componentes/save/<int:produto_composto_id>', p.saveComponenteChildAction, name="ProdutoComponentsSaveAction"),
    path('componentes/delete/<int:produto_composto_child_id>', p.deleteProdutoComponenteChild, name="ProdutoComponentsDeleteAction"),
]


