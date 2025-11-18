from django.urls import path
from backend.Controller import OrdemProducaoController as op

urlpatterns = [
    path('', op.indexView, name="OrdemProducaoIndexView"),
    path('new', op.newView, name="OrdemProducaoNewView"),
    path('save', op.saveAction, name="OrdemProducaoSaveAction"),
    path('edit/<int:ordem_producao_id>', op.editView, name="OrdemProducaoEditView"),
    path('edit/save/<int:ordem_producao_id>', op.editAction, name="OrdemProducaoEditAction"),
    path('delete/<int:ordem_producao_id>', op.deleteAction, name="OrdemProducaoDeleteAction"),
    path('componentes/<int:ordem_producao_id>', op.componentesView, name="OrdemProducaoComponentsView"),
    path('componentes/save/<int:ordem_producao_id>', op.saveComponenteChildAction, name="OrdemProducaoComponentsSaveAction"),
    path('componentes/delete/<int:ordem_producao_child_id>', op.deleteProdutoComponenteChild, name="OrdemProducaoComponentsDeleteAction"),
    path('status/<int:ordem_producao_id>/<str:status>', op.setStatusAction, name="OrdemProducaoSetStatus"),
]


