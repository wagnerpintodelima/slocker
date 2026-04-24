from django.urls import path
from backend.Controller import DashboardController as dash

urlpatterns = [
    path('', dash.indexView, name="indexView"),
    path('mapaAgroLine', dash.mapaAgroLineView, name="mapaAgroLineView"),
    path('mapaAgroLine/devices', dash.mapaAgroLineDevicesAction, name="mapaAgroLineDevicesAction"),
]
