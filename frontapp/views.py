from django.contrib.auth.decorators import login_required
from frontapp.models import CustomUser
import jwt, requests, json
from django.utils import timezone
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseRedirect
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import base64
from io import BytesIO
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.images import ImageFile
import os
from django.contrib import messages
from typing import Callable
from PIL import Image

class APIError(Exception):
    pass

# JSON POST request Wrapper
def json_request(callable: Callable[[HttpRequest, dict], dict]):
    def wrapper(request: HttpRequest) -> JsonResponse:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'reason': 'Method not allowed'}, status=405)
        if not request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'reason': 'Invalid content type'}, status=415)
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            return JsonResponse({'success': False, 'reason': 'Malformed JSON'}, status=400)
        try:
            data = callable(request, data)
        except APIError as error:
            return JsonResponse({'success': False, 'reason': str(error)}, status=400)
        except:
            return JsonResponse({'success': False, 'reason': 'Internal server error'}, status=500)
        return JsonResponse({'success': True, 'data': data})
    return wrapper

#Login Required Wrapper
def login_required(callable):
    def wrapper(request: HttpRequest) -> HttpResponse:
        if (session := request.COOKIES.get('session', None)) == None:
            return render(request, 'login.html')
        try:
            data = jwt.decode(session, settings.JWT_SECRET, algorithms=['HS256'])
            user = CustomUser.objects.get(username=data['intra_name'])
        except:
            return HttpResponseBadRequest('Invalid session')
        if data['2FA_Activated'] and not data['2FA_Passed']:
            return render(request, 'otp_login.html')
        print(user.last_active)
        user.last_active = timezone.now()
        user.save()
        return callable(request, data)
    return wrapper

#Simple Website Renderer Functions

def home(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'home.html')
    
    session = request.COOKIES.get('session', None)   
    isAuthenticated = False
    friends = None
    pending_friend_requests = None
    avatar = None
    intra_name = None
    try:
        data = jwt.decode(session, settings.JWT_SECRET, algorithms=['HS256'])
        isAuthenticated = True
    except:
        isAuthenticated = False
    if (isAuthenticated):
        user = CustomUser.objects.get(username=data['intra_name'])
        avatar = user.avatar
        friends = user.get_friends()
        pending_friend_requests = user.get_pending_friend_requests()
        intra_name = data['intra_name']
    return render(request, 'base.html', {
        'user': {
            'is_authenticated': isAuthenticated,
            'avatar': avatar,
            'friends': friends,
            'pending_friend_requests': pending_friend_requests,
            'intra_name': intra_name,
        }
    })

def otp_login(request: HttpRequest) -> HttpResponse:
    return render(request, 'otp_login.html')

def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

@login_required
def tournament(request, data):
    return render(request, 'tournament.html')

def login(request):
    return render(request, 'login.html')

def play_pong(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'play_pong.html')
    return render(request, 'base.html')

def login_with_2FA(request):
    return render(request, 'login_with_2FA.html')

@login_required
def learn_view(request, data):
    return render(request, 'learn.html')

@login_required
def profile_view(request, data):
    return render(request, 'profile.html')

def root_view(request):
    return render(request, 'root.html')

@login_required
def enable_otp_page(request, data):
    return render(request, 'enable_otp.html')

def logout(request):
    response = redirect('home')
    response.delete_cookie('session') 
    return response

@login_required
def change_info_site(request, data):
    data = jwt.decode(request.COOKIES['session'], settings.JWT_SECRET, algorithms=['HS256'])
    user = CustomUser.objects.get(username=data['intra_name'])
    return render(request, 'change_info_site.html', {
        'user' : user,
        'display_name': user.display_name,
        'avatar': user.avatar

    })


#Authentication/API related Functions

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

    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + oauth_response['access_token']
    }).json()

    session_token = {
        'access_token': oauth_response['access_token'],
        '2FA_Activated': False,
        '2FA_Passed': False,
        'intra_name': user_info['login'],
    }
    intra_name = user_info['login']
    if intra_name:
        user, created = CustomUser.objects.get_or_create(username=intra_name)
        if created or not user.display_name or not user.avatar or not user.stats:
            print(user_info)
            initialize_user(user, user_info)
            existing_user = CustomUser.objects.filter(display_name=intra_name).first()
            if existing_user:
                # Reset the display name of the existing user
                existing_user.display_name = existing_user.username
                existing_user.save()
            

        if user.two_factor_auth_enabled:
            response = HttpResponseRedirect('/') # redirect to otp login page
            response.headers['Content-Type'] = 'text/html'
            session_token['2FA_Activated'] = True
            response.set_cookie('session', jwt.encode(session_token, settings.JWT_SECRET, algorithm='HS256'))
            return response
        else:
            response = HttpResponseRedirect('/')
            response.headers['Content-Type'] = 'text/html'
            response.set_cookie('session', jwt.encode(session_token, settings.JWT_SECRET, algorithm='HS256'))
            return response
    else:
        return HttpResponse({'error': 'Username is not provided'}, status=400)

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


def initialize_user(user: CustomUser, user_info) -> None:
    user.display_name = user.username
    user.avatar = user_info['image']['versions']['medium']
    user.stats = {
        "games_played": 0,
        "games_won": 0,
        "games_lost": 0,
        "games_draw": 0,
        "highest_score": 0
    }
    user.save()


#OTP Functions

@login_required
def enable_otp(request, data):
    user_info = get_user_info_dict(request)
    intra_name = user_info['login']
    if intra_name:
        user, created = CustomUser.objects.get_or_create(username=intra_name)
        device, created = TOTPDevice.objects.get_or_create(user=user, name='default')
        if created:
            uri = device.config_url
            qr = qrcode.make(uri)
            buf = BytesIO()
            qr.save(buf, format='PNG')
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return JsonResponse({'uri': uri, 'qr_code': image_base64})
        elif device:
            uri = device.config_url
            qr = qrcode.make(uri)
            buf = BytesIO()
            qr.save(buf, format='PNG')
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return JsonResponse({'uri': uri, 'qr_code': image_base64})
    else:
        return JsonResponse({'error': 'Username is not provided'}, status=400)
      
@login_required
def verify_otp(request, data):
    user_info = get_user_info_dict(request)
    intra_name = user_info['login']

    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    otp = body_data.get('otp')
    
    user = CustomUser.objects.get(username=intra_name)
    device = user.totpdevice_set.first()
    print(otp)
    print(user)
    if device is None:
        return HttpResponse('No TOTPDevice associated with this user')
    if device.verify_token(otp):
        # OTP is valid
        user.two_factor_auth_enabled = True
        user.save()
        return HttpResponse('OTP is valid')
    else:
        # OTP is invalid
        return HttpResponse('OTP is invalid')
    
@login_required
def remove_all_otp_devices(request, data):
    user_info = get_user_info_dict(request)
    intra_name = user_info['login']
    if intra_name:
        try:
            user = CustomUser.objects.get(username=intra_name)
            TOTPDevice.objects.filter(user=user).delete()
            user.two_factor_auth_enabled = False
            user.save()
            return HttpResponse({"All OTP devices have been removed.".format(intra_name)})
        except CustomUser.DoesNotExist:
            return HttpResponse({'error': "User {} does not exist.".format(intra_name)}, status=400)
        
@csrf_exempt
def login_with_otp(request):
    
    encoded_session = request.COOKIES['session']
    session = jwt.decode(encoded_session, settings.JWT_SECRET, algorithms=['HS256'])
    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + session['access_token']
    }).json()

    if not user_info:
        return HttpResponse('No user info found')
    intra_name = user_info['login']
  

    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    otp = body_data.get('otp')
    
    user = CustomUser.objects.get(username=intra_name)
    device = user.totpdevice_set.first()

    if device is None:
        return HttpResponse('No TOTPDevice associated with this user')
    if device.verify_token(otp):
        # OTP is valid
        response = HttpResponse('OTP is valid')
        session['2FA_Passed'] = True
        response.set_cookie('session', jwt.encode(session, settings.JWT_SECRET, algorithm='HS256'))
        return response
    else: 
        # OTP is invalid
        return HttpResponse('OTP is invalid')
    
#Profile Editing Functions

@login_required
def change_info(request: HttpRequest, data) -> JsonResponse:
    print("change_info called")
    print(request.POST)
    avatar_file = None
    display_name = None
    avatar_url = None
    
    if request.method == 'POST':
        avatar_file = request.FILES.get('avatarFile', None)
        display_name = request.POST.get('displayName', '')
        avatar_url = request.POST.get('avatarUrl', '')

        data = jwt.decode(request.COOKIES['session'], settings.JWT_SECRET, algorithms=['HS256'])
        user = CustomUser.objects.get(username=data['intra_name'])
        if display_name:
            if CustomUser.objects.filter(display_name=display_name).exists() and user.display_name != display_name:
                return JsonResponse({'success': False, 'reason': 'Display name is already in use.'})
            existing_user = CustomUser.objects.filter(username=display_name).exclude(username=user.username).first()
            if existing_user:
                return JsonResponse({'success': False, 'reason': 'Display name is someones intra name.'})
            user.display_name = display_name
            
        if avatar_file:
            # Save the uploaded file and get its URL
            if not is_image(avatar_file):
                return JsonResponse({'success': False, 'reason': 'File is not an image.'})
            file_name = default_storage.save(os.path.join('avatars', user.username, avatar_file.name), avatar_file)
            avatar_url = os.path.join(settings.MEDIA_URL, file_name)
            user.avatar = avatar_url
        elif avatar_url:
            if not is_image_url(avatar_url):
                return JsonResponse({'success': False, 'reason': 'File is not an image.'})
            user.avatar = avatar_url
        
        user.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'reason': 'Method not allowed'}, status=405)
    

#Friendship Functions

@login_required
def send_friend_request(request, data):
    if request.method == 'POST':
        friend_username = request.POST.get('friend_username')
        data = jwt.decode(request.COOKIES['session'], settings.JWT_SECRET, algorithms=['HS256'])
        user = CustomUser.objects.get(username=data['intra_name'])
        try:
            friend_user = CustomUser.objects.get(username=friend_username)
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User does not exist'})
        success = user.add_friend_request(friend_user)
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Could not add friend'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
@login_required
def accept_friend_request(request, data):
    if request.method == 'POST':
        user_intra_name = request.POST.get('user_intra_name')
        friend_username = request.POST.get('friend_username')
        user = CustomUser.objects.get(username=user_intra_name)
        friend = CustomUser.objects.get(username=friend_username)
        success = user.accept_friend_request(friend)
        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'error': 'Could not accept friend request'})
    else:
        return JsonResponse({'status': 'error', 'error': 'Invalid request method'})
    
#Also used for removing friends
@login_required
def decline_friend_request(request, data):
    if request.method == 'POST':
        remove = request.POST.get('remove')
        user_intra_name = request.POST.get('user_intra_name')
        friend_username = request.POST.get('friend_username')
        try:
            user = CustomUser.objects.get(username=user_intra_name)
            friend = CustomUser.objects.get(username=friend_username)
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': 'User does not exist'})
        success = user.remove_friend(friend)
        if remove == 'true' and not success:
            success = friend.remove_friend(user)
        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'error': 'Could not decline friend request'})
    else:
        return JsonResponse({'status': 'error', 'error': 'Invalid request method'})
#Helper Functions

def is_image(file_path):
    try:
        Image.open(file_path)
        return True
    except IOError:
        return False
    
def is_image_url(url):
    try:
        response = requests.head(url)
        return response.headers['Content-Type'].startswith('image/')
    except:
        return False