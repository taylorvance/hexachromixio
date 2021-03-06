"""hexachromixio URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('rules/', TemplateView.as_view(template_name='rules.html')),

    path('game/', include('hexachromix.urls')),
    path('friends/', include('friends.urls')),

    path('signup/', views.signup, name='signup'),

    path('profile/<str:username>/', views.user_profile, name='user_profile'),

    path('account/profile/', views.profile, name='profile'),
    path('account/', include('django.contrib.auth.urls')),

    path('admin/', admin.site.urls),
]
