from django.urls import path

from . import views

urlpatterns = [
    path('create_or_join', views.create_or_join, name='create_or_join'),
]
