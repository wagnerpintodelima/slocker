from django.urls import path
from backend.Controller import CallController as c

urlpatterns = [    
    path('index/', c.indexView, name="CallIndexView"),
    path('filter/', c.filterView, name="CallFilterView"),
    path('filter/search', c.filterAction, name="CallFilterAction"),
    path('atender/<int:call_id>', c.editView, name="CallIndexAtenderView"),
    path('atender/save/resposta/<int:call_id>', c.saveAnswer, name="CallSaveAnswerAction"),
    path('get/data/', c.getDataForNewCall, name="CallGetData"),
    path('save', c.saveAction, name="CallSaveAction"),

    # Transferência
    path('transferencia/<int:call_id>', c.transferView, name="CallTransferView"),
    path('transferencia/save/<int:call_id>', c.transferAction, name="CallTransferSaveAction"),

]
