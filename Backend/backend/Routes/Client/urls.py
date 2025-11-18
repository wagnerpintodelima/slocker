from django.urls import path
from backend.Controller import ClientController as cc

urlpatterns = [
    path('', cc.indexView, name="ClientIndexView"),
    path('new', cc.newView, name="ClientNewView"),
    path('save', cc.saveAction, name="ClientSaveAction"),
    path('edit/<int:client_id>', cc.editView, name="ClientEditView"),
    path('edit/save/<int:client_id>', cc.editAction, name="ClientEditAction"),
    path('delete/<int:client_id>', cc.deleteAction, name="ClientDeleteAction"),
]
