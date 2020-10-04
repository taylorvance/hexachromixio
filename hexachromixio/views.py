from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q

from hexachromix.models import Game


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
    # All games the user created or played
    if request.user.username == 'taylorvance':
        games = Game.objects.all().order_by('-datetime_created')
    else:
        games = Game.objects.filter(Q(author=request.user) | Q(move__player=request.user)).order_by('-datetime_created').distinct()

    return render(request, 'profile.html', {'games': games})
