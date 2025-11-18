from django.urls import path
from backend.Controller import CarroController as cc

urlpatterns = [
    path('', cc.indexView, name="CarroIndexView"),
    path('new', cc.newView, name="CarroNewView"),
    path('save', cc.saveAction, name="CarroSaveAction"),
    path('edit/<int:carro_id>', cc.editView, name="CarroEditView"),
    path('edit/save/<int:carro_id>', cc.editAction, name="CarroEditAction"),
    path('delete/<int:carro_id>', cc.deleteAction, name="CarroDeleteAction"),
]


