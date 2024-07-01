"""
URL configuration for frontend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.urls import path , include
from frontapp import views
from frontapp.views import learn_view, root_view, profile_view, auth, get_user_info, remove_all_otp_devices, change_info_site, change_info, accept_friend_request, send_friend_request
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog
from django.contrib import admin
from frontapp.views import request_single_game_view

urlpatterns = [
    path('decline_friend_request/', views.decline_friend_request, name='decline_friend_request'),
    path('change_info/', views.change_info, name='change_info'),
    path('enable_otp/', views.enable_otp, name='enable_otp'),
    path('login_with_otp/', views.login_with_otp, name='login_with_otp'),
    path('auth', auth),
    path('remove_all_otp_devices.html', views.remove_all_otp_devices, name='remove_otp'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('send_friend_request/', views.send_friend_request, name='send_friend_request'),
    path('accept_friend_request/', views.accept_friend_request, name='accept_friend_request'),
    path('decline_friend_request/', views.decline_friend_request, name='decline_friend_request'),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('rank_list.html', views.rank_list, name='rank_list'),
    path('game_sessions.html', views.game_sessions, name='game_sessions'),
    path('request_single_game/', request_single_game_view, name='request_single_game'),
    path('tournament.html/', views.tournament_view, name='tournament'),


]

urlpatterns += i18n_patterns(

    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('allauth.socialaccount.urls')),
    path('', views.home, name='home'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('tournament_list.html', views.tournament_list, name='tournament_list'),
    path('login.html', views.login, name='login'),
    path('.html', root_view, name='root'),
    path('logout/', views.logout, name='logout'),
    path('profile.html', profile_view, name ='profile'),
    path('enable_otp/', views.enable_otp, name='enable_otp'),
    path('enable_otp_page.html', views.enable_otp_page, name='enable_otp_page'),
    path('otp_login/', views.otp_login, name='otp_login'),
    path('login_with_otp/', views.login_with_otp, name='login_with_otp'),
    path('change_info_site.html', views.change_info_site, name='change_info_site'),
    path('change_info/', views.change_info, name='change_info'),
    path('', views.home, name='home'),
    path('play_pong/', views.play_pong, name='play_pong'),
    path('learn.html', learn_view, name='learn'),
    path('auth', auth),
    path('get_user_info', get_user_info),
    path('remove_all_otp_devices.html', views.remove_all_otp_devices, name='remove_otp'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('send_friend_request/', views.send_friend_request, name='send_friend_request'),
    path('accept_friend_request/', views.accept_friend_request, name='accept_friend_request'),
    path('decline_friend_request/', views.decline_friend_request, name='decline_friend_request'),
    path('get_pending_friend_requests/', views.get_pending_friend_requests, name='get_pending_friend_requests'),
    path('rank_list.html', views.rank_list, name='rank_list'),
    path('game_sessions.html', views.game_sessions, name='game_sessions'),
    path('request_single_game/', request_single_game_view, name='request_single_game'),
    path('tournament.html/', views.tournament_view, name='tournament'),
)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)