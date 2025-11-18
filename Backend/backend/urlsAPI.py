from django.urls import path, include

urlpatterns = [                    
    path('slock/', include('backend.Routes.ApiSlock.urls')),
    path('generic/', include('backend.Routes.ApiGeneric.urls')),
    path('healthvis/', include('backend.Routes.ApiHealthvis.urls')),    
    path('atron/', include('backend.Routes.ApiAtron.urls')),    # Usar para o antigo gps
    path('alarm/bar/', include('backend.Routes.ApiAlarmBar.urls')),
    # path('joao/do/caminhao/', include('backend.Routes.ApiAtron.urls')),
]
