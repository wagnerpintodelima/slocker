from django.urls import path
from backend.Controller import MaquinaController as m

urlpatterns = [
    path('', m.indexView, name="MaquinaIndexView"),
    path('new', m.newView, name="MaquinaNewView"),
    path('save', m.saveAction, name="MaquinaSaveAction"),
    path('edit/<int:maquina_id>', m.editView, name="MaquinaEditView"),
    path('edit/save/<int:maquina_id>', m.editAction, name="MaquinaEditAction"),
    path('delete/<int:maquina_id>', m.deleteAction, name="MaquinaDeleteAction"),
]


