from django.urls import path
from . import views
from .views import learn_view, root_view, profile_view, auth, get_user_info


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
]
