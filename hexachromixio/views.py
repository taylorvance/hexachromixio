from django.shortcuts import render, redirect

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

def profile(request):
    if not request.user.is_authenticated:
        return redirect('/account/login/')

    if request.user.username == 'taylorvance':
        games = Game.objects.all().order_by('-datetime_created')
    else:
        games = []

    return render(request, 'profile.html', {'games': games})
