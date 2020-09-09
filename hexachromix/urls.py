from django.urls import path, re_path

from . import views

urlpatterns = [
    path('create/', views.create_game, name='create_game'),

    re_path(r'^(?P<game_uid>[0-9a-z]{12})/$', views.view_game, name='view_game'),
]
