from django.urls import path
from backend.Controller import AtronUpdateController as au

urlpatterns = [
    path('', au.indexView, name="atronUpdateView"),
    path('new', au.newView, name="atronUpdateNewView"),
    path('save', au.SaveAction, name="atronUpdateSaveAction"),
    path('edit/<int:atron_id>', au.editView, name="atronUpdateEditView"),
    path('edit/save', au.editAction, name="atronUpdateEditSaveAction"),
    path('delete/<int:atron_id>', au.deleteAction, name="atronUpdateDeleteAction"),
    path('download/apk/<int:atron_id>', au.downloadAPKAction, name="atronUpdateDownloadAPKAction"),
    path('download/habilita', au.habilitarDownloadSecurity, name="atronHablitaDownloadAction"),
]
