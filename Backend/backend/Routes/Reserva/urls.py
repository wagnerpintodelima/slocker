from django.urls import path
from backend.Controller import ReservaController as res

urlpatterns = [
    path('', res.indexView, name="ReservaIndexView"),
    path('aprovar/<int:reserva_id>', res.aprovarView, name="ReservaAprovarAction"),
    path('negar/<int:reserva_id>', res.negarView, name="ReservaNegarAction"),
    path('delete/<int:reserva_id>', res.deleteAction, name="ReservaDeleteAction"),
]
