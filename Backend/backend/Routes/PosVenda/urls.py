from django.urls import path
from backend.Controller import PosVendaController as v

urlpatterns = [
    path('', v.indexView, name="PosVendaIndexView"),    
    path('edit/<int:posvenda_id>', v.editView, name="PosVendaEditView"),
    path('edit/save/<int:posvenda_id>', v.editSaveAction, name="PosVendaEditAction"),            
    path('filter/', v.filterView, name="PosVendaFilterView"),
    path('filter/search', v.filterAction, name="PosVendaFilterAction"),
]
