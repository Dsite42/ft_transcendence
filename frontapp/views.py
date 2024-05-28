from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import jwt, requests, json
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
    response = HttpResponseRedirect('landing')
    response.headers['Content-Type'] = 'text/html'
    response.set_cookie('session', jwt.encode(oauth_response, settings.JWT_SECRET, algorithm='HS256'))
    return response

@login_required
def create_user(request, data):
    user_info = get_user_info_dict(request)
    intra_name = user_info['login']
    if intra_name:
        user = User.objects.get_or_create(username=intra_name)
    return HttpResponseRedirect('/')

@login_required
def get_user_info(request: HttpRequest, data: dict) -> HttpResponse:
    response = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + data['access_token']
    })
    return JsonResponse(response.json(), safe=False)

@login_required
def get_user_info_dict(request: HttpRequest, data: dict) -> dict:
    user_info = get_user_info(request)
    user_info_dict = json.loads(user_info.content.decode('utf-8'))
    return user_info_dict

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


# @login_required
# def enable_otp(request, data):
#     return 


@login_required
def enable_otp(request, data):
    user_info = get_user_info_dict(request)
    intra_name = user_info['login']
    if intra_name:
        user, created = User.objects.get_or_create(username=intra_name)
        device, created = TOTPDevice.objects.get_or_create(user=user, name='default')
        if created:
            uri = device.config_url
            return JsonResponse({'uri': uri})
        else:
            return JsonResponse({'error': 'TOTPDevice already exists for this user'}, status=400)
    else:
        return JsonResponse({'error': 'Username is not provided'}, status=400)
    
@login_required
def remove_all_otp_devices(request, data):
    user_info = get_user_info_dict(request)
    intra_name = user_info['login']
    if intra_name:
        try:
            user = User.objects.get(username=intra_name)
            TOTPDevice.objects.filter(user=user).delete()
            return JsonResponse({'message': "All OTP devices for user {} have been removed.".format(intra_name)})
        except User.DoesNotExist:
            return JsonResponse({'error': "User {} does not exist.".format(intra_name)}, status=400)
        
@login_required
def verify_otp(request, data):
    otp = request.POST.get('otp')
    user = request.user
    device = user.totpdevice_set.first()
    if device.verify_token(otp):
        # OTP is valid
        return HttpResponse('OTP is valid')
    else:
        # OTP is invalid
        return HttpResponse('OTP is invalid')