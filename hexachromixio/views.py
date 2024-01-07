from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.contrib.auth import get_user_model

from hexachromix.models import Game, GamePlayer
from friends.models import FriendRequest


def home(request):
    return render(request, 'home.html', {
        'my_turn': None if not request.user.is_authenticated else request.user.hexachromix_games_my_turn(),
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def profile(request):
    if request.user.is_superuser:
        games = Game.objects.all().order_by('-datetime_created')
    else:
        games = request.user.hexachromix_games().order_by('-datetime_created')

    return render(request, 'profile.html', {
        'games': games,
        'show_friends': False,
        'friends': request.user.friends(),
        'pending_you': FriendRequest.pending_requests_to_user(request.user).order_by('requester__username'),
        'pending_them': FriendRequest.pending_requests_from_user(request.user).order_by('responder__username'),
    })

def user_profile(request, username):
    User = get_user_model()
    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        return HttpResponse("user %s not found" % username)

    games = user.hexachromix_games().order_by('-datetime_created')

    return render(request, 'profile.html', {'games': games, 'show_friends': False})
