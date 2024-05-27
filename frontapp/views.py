from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import jwt, requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseRedirect
from django_otp.plugins.otp_totp.models import TOTPDevice

def login_required(callable):
    def wrapper(request: HttpRequest) -> HttpResponse:
        if (session := request.COOKIES.get('session', None)) == None:
            return render(request, 'login.html')
        try:
            data = jwt.decode(session, settings.JWT_SECRET, algorithms=['HS256'])
        except:
            return HttpResponseBadRequest('Invalid session')
        return callable(request, data)
    return wrapper

def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def auth(request: HttpRequest) -> HttpResponse:
    if (code := request.GET.get('code')) == None:
        return HttpResponseBadRequest()
    oauth_response = requests.post('https://api.intra.42.fr/oauth/token', data={
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': settings.OAUTH2_CLIENT_ID,
        'client_secret': settings.OAUTH2_SECRET,
        'redirect_uri': 'http://127.0.0.1:8000/auth'
    }).json()
    response = HttpResponseRedirect('/')
    response.headers['Content-Type'] = 'text/html'
    response.set_cookie('session', jwt.encode(oauth_response, settings.JWT_SECRET, algorithm='HS256'))
    return response

@login_required
def get_user_info(request: HttpRequest, data: dict) -> HttpResponse:
    response = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + data['access_token']
    })
    return JsonResponse(response.json(), safe=False)


def home(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'home.html')
    session = request.COOKIES.get('session', None)   
    isAuthenticated = False
    try:
        data = jwt.decode(session, settings.JWT_SECRET, algorithms=['HS256'])
        isAuthenticated = True
    except:
        isAuthenticated = False
    return render(request, 'base.html', {
        'user': {
            'is_authenticated': isAuthenticated
        }
    })

def play_pong(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'play_pong.html')
    return render(request, 'base.html')

@login_required
def tournament(request, data):
    return render(request, 'tournament.html')

def login(request):
    return render(request, 'login.html')

@login_required
def learn_view(request, data):
    return render(request, 'learn.html')

@login_required
def profile_view(request, data):
    return render(request, 'profile.html')

def root_view(request):
    return render(request, 'root.html')

def logout(request):
    response = redirect('home')
    response.delete_cookie('session') 
    return response

@login_required
def enable_otp(request, data):
    user_info = get_user_info(request)
    intra_name = user_info.get('login')
    user = User.objects.get(username=intra_name)
    device = TOTPDevice.objects.create(user=intra_name, name='default')
    uri = device.config_url()
    return JsonResponse({'uri': uri})