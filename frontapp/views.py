from django.shortcuts import render

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

def learn_view(request):
    return render(request, 'learn.html')