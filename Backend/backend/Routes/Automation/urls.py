from django.urls import path, include
from backend.Controller import AutomationController as ac, AutomationAtronController as aac, AutomationV2Controller as v2, AutomationTelaController as tela, AutomationSensorController as sensor

urlpatterns = [
    path('', ac.indexView, name="AutomationIndexView"),
    path('new', ac.newView, name="AutomationNewAction"),
    path('save', ac.SaveAction, name="AutomationSaveAction"),
    path('edit/<int:automation_id>', ac.editView, name="AutomationEditView"),
    path('edit/hu/<int:automation_id>', ac.huView, name="AutomationEditHUView"),
    path('edit/save', ac.editAction, name="AutomationEditAction"),
    path('edit/slot/<int:automation_id>', ac.editSlotAction, name="AutomationEditSlotAction"),
    path('edit/slot/save', ac.editSlotSaveAction, name="AutomationEditSlotSaveAction"),
    path('edit/slot/delete/<str:slot_id>', ac.editSlotDeleteAction, name="AutomationEditSlotDeleteAction"),
    path('edit/hu/save', ac.huSaveAction, name="AutomationEditHUSaveAction"),
    path('delete/<str:hu_id>', ac.deleteAction, name="AutomationDeleteHUAction"),

    #------------ MQTT
    path('send/to/mqtt', ac.sendToMqttAction, name="AutomationSendToMqttAction"),
    path('send/to/mqtt/slots', ac.sendToMqttSlotsAction, name="AutomationSendToMqttSlotsAction"),
    path('send/to/mqtt/slots/edit', ac.sendToMqttSlotsEditAction, name="AutomationSendToMqttSlotsEditAction"),

    # Checkout
    path('show/file/json/checkout/<int:automation_id>', ac.showJsonCheckoutFromFileView, name="AutomationFileCheckoutView"),
    path('send/file/checkout/handler', ac.sendHandlerFileCheckout, name="AutomationSendCheckoutFileAction"),    
    
    # Atron
    path('atron/<int:automation_type>', aac.indexView, name="AtronIndexView"),
    path('atron/<int:automation_type>/new', aac.newView, name="AtronNewView"),                 
    path('atron/<int:automation_type>/save', aac.saveAction, name="AtronSaveAction"),
    path('atron/<int:automation_type>/<int:atron_device>/edit', aac.editView, name="AtronEditView"),  
    path('atron/<int:automation_type>/<int:atron_device>/edit/save', aac.editSaveAction, name="AtronEditSaveAction"),  
    path('atron/delete/<int:atron_id>', aac.deleteAction, name="AtronDeleteAction"),  
    path('atron/print/garantia/<int:atron_id>', aac.garantia, name="AtronGarantiaView"),  
    
    # V2
    path('v2/<int:automation_type>', v2.indexView, name="V2IndexView"),
    path('v2/<int:automation_type>/new', v2.newView, name="V2NewView"),                 
    path('v2/<int:automation_type>/save', v2.saveAction, name="V2SaveAction"),
    path('v2/<int:automation_type>/<int:v2_id>/edit', v2.editView, name="V2EditView"),  
    path('v2/<int:automation_type>/<int:v2_id>/edit/save', v2.editSaveAction, name="V2EditSaveAction"),  
    path('v2/delete/<int:v2_id>', v2.deleteAction, name="V2DeleteAction"),  
    path('v2/<int:automation_type>/<int:v2_id>/calibration', v2.calibrationView, name="V2CalibrationView"),  
    path('v2/<int:automation_type>/<int:v2_id>/calibration/save', v2.calibrationSaveAction, name="V2CalibrationSaveView"),  
    
    # Tela
    path('tela/<int:automation_type>', tela.indexView, name="TelaIndexView"),
    path('tela/<int:automation_type>/new', tela.newView, name="TelaNewView"),                 
    path('tela/<int:automation_type>/save', tela.saveAction, name="TelaSaveAction"),
    path('tela/<int:automation_type>/<int:tela_id>/edit', tela.editView, name="TelaEditView"),  
    path('tela/<int:automation_type>/<int:tela_id>/edit/save', tela.editSaveAction, name="TelaEditSaveAction"),  
    path('tela/delete/<int:tela_id>', tela.deleteAction, name="TelaDeleteAction"),
    
    # Sensores Vic sensor
    path('sensor/<int:automation_type>', sensor.indexView, name="SensorIndexView"),
    path('sensor/<int:automation_type>/new', sensor.newView, name="SensorNewView"),                 
    path('sensor/<int:automation_type>/save', sensor.saveAction, name="SensorSaveAction"),
    path('sensor/<int:automation_type>/<int:sensor_id>/edit', sensor.editView, name="SensorEditView"),  
    path('sensor/<int:automation_type>/<int:sensor_id>/edit/save', sensor.editSaveAction, name="SensorEditSaveAction"),      
    path('sensor/delete/<int:sensor_id>', sensor.deleteAction, name="SensorDeleteAction"),
]
