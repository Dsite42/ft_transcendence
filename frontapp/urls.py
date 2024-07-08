from django.urls import path , include
from . import views
from .views import learn_view, root_view, profile_view, auth, get_user_info, remove_all_otp_devices, change_info_site, change_info, accept_friend_request, send_friend_request
from django.conf import settings
from django.conf.urls.static import static
from .views import request_single_game_view
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

# most likely not needed anymore maybe delete file later

