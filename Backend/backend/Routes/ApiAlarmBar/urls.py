from django.urls import path
from backend.Controller import ApiAlarmBarController as api

urlpatterns = [
    path('login', api.login, name="ApiAlarmBarLogin"),
    path('sync', api.sync, name="ApiAlarmBarSync"),
    path('set/status', api.setStatus, name="ApiAlarmBarSetStatus"),
    path('get/history', api.history, name="ApiAlarmBarGetHistory"),
]
