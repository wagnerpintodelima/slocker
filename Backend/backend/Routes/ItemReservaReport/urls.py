from django.urls import path
from backend.Controller import ItemReservaReportController as p

urlpatterns = [
    path('', p.indexView, name="ItemReservaReportView")    
]


