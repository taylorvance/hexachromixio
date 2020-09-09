from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse

from hexachromix.models import Game


def create_game(request):
    game = Game(variant=request.POST['variant'])
    game.save()

    return redirect('/game/%s' % game.uid)

def view_game(request, game_uid):
    try:
        game = Game.objects.get(uid=game_uid)
    except Game.DoesNotExist:
        return HttpResponse("game %s not found :(" % game_uid)

    return HttpResponse("here's game %s (id %d)" % (game.uid, game.pk))
