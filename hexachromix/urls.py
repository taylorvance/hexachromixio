from django.urls import path, re_path

from . import views

urlpatterns = [
    path('new/', views.new_game, name='new_game'),
    path('create/', views.create_game, name='create_game'),

    path('search/', views.find_game, name='find_game'),
    re_path(r'^(?P<game_identifier>[A-Za-z0-9-]+)/$', views.view_game, name='view_game'),
]
