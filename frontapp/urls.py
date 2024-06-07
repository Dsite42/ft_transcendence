from django.urls import path
from . import views
from .views import learn_view, root_view, profile_view, auth, get_user_info, remove_all_otp_devices, change_info_site, change_info, accept_friend_request, send_friend_request
from django.conf import settings
from django.conf.urls.static import static
from .views import create_game_view


urlpatterns = [
    path('', views.home, name='home'),
    path('play_pong/', views.play_pong, name='play_pong'),
    path('tournament.html', views.tournament, name='tournament'),
    path('login.html', views.login, name='login'),
    path('learn.html', learn_view, name='learn'),
    path('.html', root_view, name='root'),
    path('profile.html', profile_view, name ='profile'),
    path('auth', auth),
    path('get_user_info', get_user_info),
    path('logout/', views.logout, name='logout'),
    path('enable_otp/', views.enable_otp, name='enable_otp'),
    path('enable_otp_page.html', views.enable_otp_page, name='enable_otp_page'),
    path('remove_all_otp_devices.html', views.remove_all_otp_devices, name='remove_otp'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('otp_login/', views.otp_login, name='otp_login'),
    path('login_with_otp/', views.login_with_otp, name='login_with_otp'),
    path('change_info_site.html', views.change_info_site, name='change_info_site'),
    path('change_info/', views.change_info, name='change_info'),
    path('send_friend_request/', views.send_friend_request, name='send_friend_request'),
    path('accept_friend_request/', views.accept_friend_request, name='accept_friend_request'),
    path('decline_friend_request/', views.decline_friend_request, name='decline_friend_request'),
    path('get_pending_friend_requests/', views.get_pending_friend_requests, name='get_pending_friend_requests'),
    path('create_game/', create_game_view, name='create_game'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)