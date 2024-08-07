from django.contrib.auth.decorators import login_required
from frontapp.models import CustomUser, Friendship
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
from django.template.defaulttags import register
from django import template
import os
from django.contrib import messages
from typing import Callable
from PIL import Image
from cryptography.fernet import Fernet
from base64 import b64decode, b64encode
from django_otp.oath import TOTP

@register.tag(name='env')
def env(parser, token):
    try:
        # Split the token to get the environment variable name
        tag_name, env_var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )

    return EnvNode(env_var_name)

class EnvNode(template.Node):
    def __init__(self, env_var_name):
        self.env_var_name = env_var_name

    def render(self, context):
        # Retrieve the environment variable value
        return os.environ.get(self.env_var_name, '')

from .rpc_client import get_matchmaker_service

from django.utils.translation import gettext as _
import logging
from frontapp.models import Game, Tournament
class APIError(Exception):
    pass


# Encryption setup
fernet = Fernet(os.environ.get('ENCRYPTION_KEY'))


# JSON POST request Wrapper
def json_request(callable: Callable[[HttpRequest, dict], dict]):
    def wrapper(request: HttpRequest) -> JsonResponse:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'reason': _('Method not allowed')}, status=405)
        if not request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'reason': _('Invalid content type')}, status=415)
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            return JsonResponse({'success': False, 'reason': _('Malformed JSON')}, status=400)
        try:
            data = callable(request, data)
        except APIError as error:
            return JsonResponse({'success': False, 'reason': str(error)}, status=400)
        except:
            return JsonResponse({'success': False, 'reason': _('Internal server error')}, status=500)
        return JsonResponse({'success': True, 'data': data})
    return wrapper

#Login Required Wrapper
def login_required(callable):
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if (session := request.COOKIES.get('session', None)) == None:
            return render(request, 'login.html')
        try:
            data = jwt.decode(session, os.environ['JWT_SECRET'], algorithms=['HS256'])
            user = CustomUser.objects.get(username=data['intra_name'])
        except Exception as e:
            logging.error("Error in login_required: %s", e)
            response = HttpResponseRedirect('/')
            response.delete_cookie('session')
            return response

        if data['2FA_Activated'] and not data['2FA_Passed']:
            return render(request, 'otp_login.html')
        user.last_active = timezone.now()
        user.save()
        return callable(request, data, *args, **kwargs)
    return wrapper

#Login Required Wrapper
def login_required2(callable):
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if (session := request.COOKIES.get('session', None)) == None:
            return render(request, 'login.html')
        try:
            data = jwt.decode(session, os.environ['JWT_SECRET'], algorithms=['HS256'])
            user = CustomUser.objects.get(username=data['intra_name'])
        except Exception as e:
            logging.error("Error in login_required: %s", e)
            response = HttpResponseRedirect('/')
            response.delete_cookie('session')
            return response

        if data['2FA_Activated'] and not data['2FA_Passed']:
            return render(request, 'otp_login.html')
        user.last_active = timezone.now()
        user.save()
        return callable(request, data, user, *args, **kwargs)
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
    user_id = None
    try:
        data = jwt.decode(session, os.environ['JWT_SECRET'], algorithms=['HS256'])
        isAuthenticated = True
    except:
        isAuthenticated = False
    if (isAuthenticated):
        try:
            user = CustomUser.objects.get(username=data['intra_name'])
        except:
            response = HttpResponseRedirect('/')
            response.delete_cookie('session')
            return response
        avatar = user.avatar
        friends = user.get_friends()
        pending_friend_requests = user.get_pending_friend_requests()
        intra_name = data['intra_name']
        user_id = user.id
    return render(request, 'base.html', {
        'user': {
            'is_authenticated': isAuthenticated,
            'avatar': avatar,
            'friends': friends,
            'pending_friend_requests': pending_friend_requests,
            'intra_name': intra_name,
            'user_id': user_id,
        }
    })

def otp_login(request: HttpRequest) -> HttpResponse:
    return render(request, 'otp_login.html')

def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

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
    data = jwt.decode(request.COOKIES['session'], os.environ['JWT_SECRET'], algorithms=['HS256'])
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
        'client_id': os.environ['OAUTH2_UID'],
        'client_secret': os.environ['OAUTH2_SECRET'],
        'redirect_uri': f'https://{os.environ["PUBLIC_HOST"]}/auth'
    }).json()
    if (oauth_response.get('error')):
        alert = oauth_response.get('error_description')
        messages.error(request, f'Error: {alert}')
        return render(request, 'base.html')
    print("oauth_response: ", oauth_response)
    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + oauth_response['access_token']
    }).json()

    intra_name = user_info['login']
    if intra_name:
        user, created = CustomUser.objects.get_or_create(username=intra_name)
        if created or not user.display_name or not user.avatar or not user.stats:
            initialize_user(user, user_info)
            existing_user = CustomUser.objects.filter(display_name=intra_name).first()
            if existing_user:
                # Reset the display name of the existing user
                existing_user.display_name = existing_user.username
                existing_user.save()
        session_token = {
        'access_token': b64encode(fernet.encrypt(oauth_response['access_token'].encode('utf-8'))).decode('utf-8'),
        '2FA_Activated': False,
        '2FA_Passed': False,
        'intra_name': user_info['login'],
        'user_id': CustomUser.objects.get(username=user_info['login']).id
    }

        if user.two_factor_auth_enabled:
            response = HttpResponseRedirect('/')
            response.headers['Content-Type'] = 'text/html'
            session_token['2FA_Activated'] = True
            response.set_cookie('session', jwt.encode(session_token, os.environ['JWT_SECRET'], algorithm='HS256'))
            return response
        else:
            response = HttpResponseRedirect('/')
            response.headers['Content-Type'] = 'text/html'
            response.set_cookie('session', jwt.encode(session_token, os.environ['JWT_SECRET'], algorithm='HS256'))
            return response
    else:
        return HttpResponse({'error': _('Username is not provided')}, status=400)

@login_required
def get_user_info(request: HttpRequest, data: dict) -> HttpResponse:
    response = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + fernet.decrypt(b64decode(data['access_token'])).decode('utf-8')
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
        return JsonResponse({'error': _('Username is not provided')}, status=400)

@login_required
def verify_otp(request, data):
    user_info = get_user_info_dict(request)
    intra_name = user_info['login']

    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    otp = body_data.get('otp')

    user = CustomUser.objects.get(username=intra_name)
    device = user.totpdevice_set.first()

    if device is None:
        return HttpResponse(_('No TOTP Device associated with this user'))
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    if totp.verify(int(otp), 2):
        # OTP is valid
        user.two_factor_auth_enabled = True
        user.save()
        return JsonResponse({'success': True})
    else:
        # OTP is invalid
        return JsonResponse({'success': False})

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
            return HttpResponse({_("All OTP devices have been removed.").format(intra_name)})
        except CustomUser.DoesNotExist:
            return HttpResponse({'error': _("User {} does not exist.").format(intra_name)}, status=400)

@csrf_exempt
def login_with_otp(request):

    encoded_session = request.COOKIES['session']
    session = jwt.decode(encoded_session, os.environ['JWT_SECRET'], algorithms=['HS256'])
    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + fernet.decrypt(b64decode(session['access_token'])).decode('utf-8')
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
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    if totp.verify(int(otp), 2):
        # OTP is valid
        response = JsonResponse({'success': True})
        session['2FA_Passed'] = True
        response.set_cookie('session', jwt.encode(session, os.environ['JWT_SECRET'], algorithm='HS256'))
        return response
    else:
        # OTP is invalid
        return JsonResponse({'success': False})

#Profile Editing Functions

@login_required
def change_info(request: HttpRequest, data) -> JsonResponse:
    avatar_file = None
    display_name = None
    avatar_url = None

    if request.method == 'POST':
        avatar_file = request.FILES.get('avatarFile', None)
        display_name = request.POST.get('displayName', '')
        avatar_url = request.POST.get('avatarUrl', '')

        data = jwt.decode(request.COOKIES['session'], os.environ['JWT_SECRET'], algorithms=['HS256'])
        user = CustomUser.objects.get(username=data['intra_name'])
        if display_name:
            if CustomUser.objects.filter(display_name=display_name).exists() and user.display_name != display_name:
                return JsonResponse({'success': False, 'reason': _('Display name is already in use.')})
            existing_user = CustomUser.objects.filter(username=display_name).exclude(username=user.username).first()
            if existing_user:
                return JsonResponse({'success': False, 'reason': _('Display name is someones intra name.')})
            user.display_name = display_name

        if avatar_file:
            # Save the uploaded file and get its URL
            if not is_image(avatar_file):
                return JsonResponse({'success': False, 'reason': _('File is not an image.')})
            file_name = default_storage.save(os.path.join('staticfiles/avatars', user.username, avatar_file.name), avatar_file)
            avatar_url = os.path.join(settings.MEDIA_URL, file_name)
            user.avatar = avatar_url
        elif avatar_url:
            if not is_image_url(avatar_url):
                return JsonResponse({'success': False, 'reason': _('File is not an image.')})
            user.avatar = avatar_url

        user.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'reason': _('Method not allowed')}, status=405)


#Friendship Functions

@login_required2
def get_friends(request, data, user):
    friends = []
    for friend in user.get_friends():
        friends.append({ 'username': friend.username, 'last_active': friend.last_active })
    pending_friends = []
    for friend in user.get_pending_friend_requests():
        pending_friends.append({ 'username': friend.username })
    return JsonResponse({'friends': friends, 'pending_friends': pending_friends})

@login_required
def send_friend_request(request, data):
    if request.method == 'POST':
        friend_username = request.POST.get('friend_username')
        data = jwt.decode(request.COOKIES['session'], os.environ['JWT_SECRET'], algorithms=['HS256'])
        user = CustomUser.objects.get(username=data['intra_name'])
        try:
            friend_user = CustomUser.objects.get(username=friend_username)
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': _('User does not exist')})
        success = user.add_friend_request(friend_user)
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': _('Could not add friend')})
    else:
        return JsonResponse({'success': False, 'error': _('Invalid request method')})

@login_required
def accept_friend_request(request, data):
    if request.method == 'POST':
        friend_username = request.POST.get('friend_username')
        try:
            user = CustomUser.objects.get(username=data['intra_name'])
            friend = CustomUser.objects.get(username=friend_username)
            success = user.accept_friend_request(friend)
        except Exception:
            success = False
        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'error': _('Could not accept friend request')})
    else:
        return JsonResponse({'status': 'error', 'error': _('Invalid request method')})

#Also used for removing friends
@login_required
def decline_friend_request(request, data):
    if request.method == 'POST':
        remove = request.POST.get('remove')
        friend_username = request.POST.get('friend_username')
        try:
            user = CustomUser.objects.get(username=data['intra_name'])
            friend = CustomUser.objects.get(username=friend_username)
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': _('User does not exist')})
        success = user.remove_friend(friend)
        if remove == 'true' and not success:
            success = friend.remove_friend(user)
        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'error': _('Could not decline friend request')})
    else:
        return JsonResponse({'status': 'error', 'error': _('Invalid request method')})

@login_required
def get_pending_friend_requests(request, data):
    data = jwt.decode(request.COOKIES['session'], os.environ['JWT_SECRET'], algorithms=['HS256'])
    user = CustomUser.objects.get(username=data['intra_name'])
    pending_requests = Friendship.objects.filter(to_user=user, accepted=False)

    usernames = [friendship.from_user.username for friendship in pending_requests if not friendship.popup_shown]

    for friendship in pending_requests:
        if not friendship.popup_shown:
            friendship.popup_shown = True
            friendship.save()

    return JsonResponse(usernames, safe=False)


#Dashboard Functions

@login_required
def rank_list(request, data):
    players = CustomUser.objects.all()#.order_by('-points') 
    ranking = [{'name': player.username, 'score': player.stats.get('score'), 'games_won': player.stats.get('games_won'), 'games_lost': player.stats.get('games_lost'), 'games_played': player.stats.get('games_played')} for player in players]
    return render(request, 'rank_list.html', {'ranking': json.dumps(ranking)})

@login_required
def tournament_list(request, data):
    tournaments = Tournament.objects.all().order_by('-start_time')
    tournament_list = [tournament.to_dict() for tournament in tournaments]
    return render(request, 'tournament_list.html', {'tournaments': json.dumps(tournament_list)})


@login_required
def tournament_view(request, data, tournament_id):
    print("tournament_id2: ", tournament_id)
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        # Assuming your `to_dict` method correctly converts the model instance to a dictionary
        tournament_dict = tournament.to_dict()
        return JsonResponse(tournament_dict)
    except Tournament.DoesNotExist:
        return JsonResponse({'error': 'Tournament not found'}, status=404)



@login_required
def game_sessions(request, data):
    data = jwt.decode(request.COOKIES['session'], os.environ['JWT_SECRET'], algorithms=['HS256'])
    user = CustomUser.objects.get(username=data['intra_name'])
    games = Game.objects.all().order_by('-date')
    game_sessions = [game.to_dict() for game in games]
    return render(request, 'game_sessions.html', {'game_sessions': json.dumps(game_sessions), 'current_user': user.username})

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
    

#RPC Functions
def request_single_game_view(request):
    player_id = request.GET.get('player_id')
    # RPC-Funktion aufrufen
    #matchmaker_service, connection = get_matchmaker_service()
    #response = matchmaker_service.create_single_game('dnebatz')
    #connection.close()
    return render(request, 'request_single_game.html', {'player_id': player_id})

def websocket_test(request):
    return render(request, 'websocket_test.html')
