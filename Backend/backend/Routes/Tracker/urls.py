from django.urls import path
from backend.Controller import TrackerController as v

urlpatterns = [
    path('', v.indexView, name="TrackerIndexView"),
    path('new/', v.newView, name="TrackerNewView"),
    path('new/proccess/', v.newAction, name="TrackerNewAction"),
    path('mapa/', v.mapView, name="TrackerMapView"),
    path('delete/<int:talhao_id>/', v.deleteAction, name="TrackerDeleteAction"),
]
