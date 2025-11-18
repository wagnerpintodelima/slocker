from django.urls import path
from backend.Controller import UserAppController as up

urlpatterns = [
    path('', up.indexView, name="UserAppIndexView"),
    path('new', up.newView, name="UserAppNewView"),
    path('save', up.saveAction, name="UserAppSaveAction"),
    path('edit/<int:user_app_id>', up.editView, name="UserAppEditView"),
    path('edit/save/<int:user_app_id>', up.editAction, name="UserAppEditAction"),
    path('delete/<int:user_app_id>', up.deleteAction, name="UserAppDeleteAction"),
]
