from django.urls import path
from backend.Controller import LoginController as login

urlpatterns = [
    path('', login.loginView, name="loginView"),
    path('do', login.do_login, name="loginAction"),
    path('do/logout', login.loginView, name="logoutAction"),
]
