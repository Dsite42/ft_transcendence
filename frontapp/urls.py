from django.urls import path
from . import views
from .views import learn_view, root_view, profile_view, auth, get_user_info, remove_all_otp_devices


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
    
    path('rank_list.html', views.rank_list, name='rank_list'),
    path('game_sessions.html', views.game_sessions, name='game_sessions'),
]
