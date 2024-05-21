from django.urls import path
from . import views
from .views import learn_view
from .views import root_view


urlpatterns = [
    path('', views.home, name='home'),
    path('play_pong/', views.play_pong, name='play_pong'),
    path('tournament.html', views.tournament, name='tournament'),
    path('login.html', views.login, name='login'),
    path('learn.html', learn_view, name='learn'),
    path('.html', root_view, name='root')
]
