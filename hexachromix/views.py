from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from hexachromix.models import Game


def find_game(request):
    game_uid = request.GET['game_uid']
    game_uid = game_uid.strip()
    game_uid = game_uid.lower()

    try:
        game = Game.objects.get(uid=game_uid)
    except Game.DoesNotExist:
        return HttpResponse("game %s not found :(" % game_uid)

    return redirect('/game/%s' % game.uid)

@login_required
def create_game(request):
    game = Game(variant=Game.Variant[request.POST['variant']])
    game.author = request.user
    game.save()

    return redirect('/game/%s' % game.uid)

def view_game(request, game_uid):
    try:
        game = Game.objects.get(uid=game_uid)
    except Game.DoesNotExist:
        return HttpResponse("game %s not found :(" % game_uid)

    if game.is_active:
        return render(request, 'hexachromix/play.html', {'game': game})
    else:
        return render(request, 'hexachromix/view_game.html', {'game': game})
