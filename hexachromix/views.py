from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from hexachromix.models import Game
from hexachromix.utils import HexachromixState

import re


def find_game(request):
    game_identifier = request.GET['game_identifier']
    if not game_identifier:
        return HttpResponse("No game identifier provided.")
    game_identifier = re.sub(r'\s+', '-', game_identifier.strip().lower())

    try:
        game = Game.objects.get(Q(uid=game_identifier) | Q(code=game_identifier))
    except Game.DoesNotExist:
        return HttpResponse("game %s not found" % game_identifier)

    return redirect('/game/%s' % game.code)

@login_required
def new_game(request):
    variants = []
    for variant in Game.Variant:
        num = len(variant.label.split())
        variants.append({
            'label': variant.label,
            'value': variant.value,
            'teams': num,
            'players': '%d%s' % (num, '-6' if num < 6 else ''),
        })

    return render(request, 'hexachromix/new_game.html', {
        'variants': variants,
    })

@login_required
def create_game(request):
    game = Game(variant=Game.Variant[request.POST['variant']])
    game.author = request.user
    game.save()
    return redirect('/game/%s' % game.code)

def view_game(request, game_identifier):
    try:
        game = Game.objects.get(Q(uid=game_identifier) | Q(code=game_identifier))
    except Game.DoesNotExist:
        return HttpResponse("game %s not found" % game_identifier)

    if game.is_active:
        # Make sure a session exists so the channel can generate a player identifier.
        if not request.session.session_key:
            request.session.create()

        return render(request, 'hexachromix/play.html', {'game':game, 'game_code':game.code.replace('-',' ')})
    else:
        state = HexachromixState(variant=game.variant)

        moves = []
        for move in game.moves:
            state = state.make_move((move.q, move.r))
            moves.append({
                'color': move.color,
                'q': move.q,
                'r': move.r,
                'hfen': state.hfen,
            })

        return render(request, 'hexachromix/view_game.html', {'game': game, 'moves': moves})
