from django.urls import path, include

urlpatterns = [
    path('automation/', include('backend.Routes.Automation.urls')),
    path('login/', include('backend.Routes.Login.urls')),
    path('dashboard/', include('backend.Routes.Dashboard.urls')),
    path('client/', include('backend.Routes.Client.urls')),
    path('client/auten/', include('backend.Routes.ClienteAuten.urls')),
    path('user/app/', include('backend.Routes.UserApp.urls')),
    path('atron/update/', include('backend.Routes.AtronUpdate.urls')),               
    path('carro/', include('backend.Routes.Carro.urls')),    
    path('tecnico/', include('backend.Routes.Tecnico.urls')),    
    path('viagem/', include('backend.Routes.Viagem.urls')),    
    path('viagem/instalacao/', include('backend.Routes.ViagemInstalacao.urls')),    
    path('call/', include('backend.Routes.Call.urls')),    
    path('email/', include('backend.Routes.Email.urls')),    
    path('maquina/', include('backend.Routes.Maquina.urls')),
    path('posvendas/', include('backend.Routes.PosVenda.urls')),
    path('produto/', include('backend.Routes.Produto.urls')),
    path('movimento/estoque/', include('backend.Routes.MovimentoEstoque.urls')),
    path('itens/com/tecnicos/', include('backend.Routes.ItemReservaReport.urls')),
    path('ordem/producao/', include('backend.Routes.OrdemProducao.urls')),
    path('alarm/bar/', include('backend.Routes.AlarmBar.urls')),
]
