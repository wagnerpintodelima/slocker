from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from slock.settings import BLACKLIST_USERS
from backend.Controller.BaseController import doLog
from datetime import datetime

def loginView(request):
    context = {}
    return render(request, 'Login/index.html', context)

def do_login(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']                
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            
            # ACHOU o usuário nas credenciais
            if user.username in BLACKLIST_USERS: #usuario_proibido
                # se for o “usuário específico”, já desloga e retorna erro
                logout(request)
                ip = (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR'))
                messages.error(request, fr"Barbaridade, que feio hein. Deus está vendo! E-mail de segurança enviado com sucesso! Seu IP é: {ip}")
                doLog('+BLACKLIST', f'<b>AUTO MESSAGE</b> - Houve uma tentativa de acesso ao sistema com o usuário {user.id}! Hora da tentativa: {datetime.now()}', 0) # Error
                url = reverse('loginView')                
                return redirect(f"{url}?pega_ladrao=true")                
            
            login(request, user)
            return redirect('indexView')
        else:
            messages.add_message(request, messages.WARNING, 'Usuário ou senha errado!')
            context = {}
            return render(request, 'Login/index.html', context)

@login_required
def logout_view(request):
    logout(request)
    context = {}
    return redirect('loginView')
