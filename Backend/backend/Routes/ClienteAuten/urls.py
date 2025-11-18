from django.urls import path
from backend.Controller import ClienteAutenController as cc

urlpatterns = [
    path('', cc.indexView, name="ClienteAutenIndexView"),
    path('new', cc.newView, name="ClienteAutenNewView"),
    path('save', cc.saveAction, name="ClienteAutenSaveAction"),
    path('edit/<int:client_auten_id>', cc.editView, name="ClienteAutenEditView"),
    path('edit/save/<int:client_auten_id>', cc.editAction, name="ClienteAutenEditAction"),
    path('delete/<int:client_auten_id>', cc.deleteAction, name="ClienteAutenDeleteAction"),
]
