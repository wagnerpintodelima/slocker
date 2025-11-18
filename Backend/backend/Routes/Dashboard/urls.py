from django.urls import path
from backend.Controller import DashboardController as dash

urlpatterns = [
    path('', dash.indexView, name="indexView")
]
