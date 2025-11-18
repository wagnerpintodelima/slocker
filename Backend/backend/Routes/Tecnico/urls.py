from django.urls import path
from backend.Controller import TecnicoController as tec

urlpatterns = [
    path('', tec.indexView, name="TecnicoIndexView"),
    path('new', tec.newView, name="TecnicoNewView"),
    path('save', tec.saveAction, name="TecnicoSaveAction"),
    path('edit/<int:tecnico_id>', tec.editView, name="TecnicoEditView"),
    path('edit/save/<int:tecnico_id>', tec.editAction, name="TecnicoEditAction"),
    path('delete/<int:tecnico_id>', tec.deleteAction, name="TecnicoDeleteAction"),
]
