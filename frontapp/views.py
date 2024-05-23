from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'home.html')
    return render(request, 'base.html')

def play_pong(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'play_pong.html')
    return render(request, 'base.html')

def tournament(request):
    return render(request, 'tournament.html')

def login(request):
    return render(request, 'login.html')
@login_required
def learn_view(request):
    return render(request, 'learn.html')

@login_required
def profile_view(request):
    return render(request, 'profile.html')

def root_view(request):
    return render(request, 'root.html')