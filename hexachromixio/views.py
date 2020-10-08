from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q

from hexachromix.models import Game, GamePlayer
from friends.models import FriendRequest


def home(request):
    variants = []
    for variant in Game.Variant:
        num = len(variant.label.split())
        variants.append({
            'label': variant.label,
            'value': variant.value,
            'teams': num,
            'players': '%d%s' % (num, '+' if num < 6 else ''),
        })

    return render(request, 'home.html', {'variants': variants})

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
        # All games
        games = Game.objects.all().order_by('-datetime_created')
    else:
        # All games the user created or played
        games = Game.objects.filter(Q(author=request.user) | Q(gameplayer__player=request.user) | Q(move__player=request.user)).order_by('-datetime_created').distinct()

    friends = request.user.friend_requesters.filter(status=FriendRequest.Status.YES)
    friends = friends.union(request.user.friend_responders.filter(status=FriendRequest.Status.YES))
    for friend in friends:
        friend.other_user = friend.responder.username if request.user.pk == friend.requester.pk else friend.requester.username
    friends = sorted(friends, key=lambda x: x.other_user)

    return render(request, 'profile.html', {
        'games': games,
        'friends': friends,
        'pending_you': request.user.friend_responders.filter(status__isnull=True).order_by('requester__username'),
        'pending_them': request.user.friend_requesters.filter(status__isnull=True).order_by('responder__username'),
    })
