from django.urls import path, re_path

from . import views

urlpatterns = [
    path('request/', views.request_friend, name='request_friend'),
    path('remove/', views.remove_friend, name='remove_friend'),
    path('accept/', views.accept_request, name='accept_request'),
    path('decline/', views.decline_request, name='decline_request'),
    path('cancel/', views.cancel_request, name='cancel_request'),
]
