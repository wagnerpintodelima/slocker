from django.urls import path
from backend.Controller import AlarmBarController as ab

urlpatterns = [
    path('', ab.indexView, name="AlarmbarIndexView"),
    path('new', ab.newView, name="AlarmbarNewView"),
    path('save', ab.saveAction, name="AlarmbarSaveAction"),
    path('edit/<int:alarmbar_id>', ab.editView, name="AlarmbarEditView"),
    path('edit/save/<int:alarmbar_id>', ab.editSaveAction, name="AlarmbarEditAction"),
    path('delete/<int:alarmbar_id>', ab.deleteAction, name="AlarmbarDeleteAction"),
]
