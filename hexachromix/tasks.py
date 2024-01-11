from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache

import os
import logging
import urllib
import json

from hexachromix.models import Game, Move

logger = logging.getLogger(__name__)
logger.debug(f'using logger {__name__}')


@shared_task
def check_ai(game_uid):
    logger.debug(f'check_ai: begin {game_uid}')
    game = Game.objects.get(uid=game_uid)
    hfen = game.hfen

    color = hfen.split()[1]
    color_players = cache.get(f'game_{game_uid}_colors', {})
    logger.debug(f'check_ai: color_players {color_players}')
    if not str(color_players.get(color)).startswith('ai:'):
        logger.debug('check_ai: X not an ai')
        # return
    logger.debug('check_ai: √ is ai')

    # -- THE FOLLOWING IS DUPLICATED FROM THE MAKE_MOVE ACTION IN PLAYCONSUMER --

    # Is the game over?
    state = Game.state_from_hfen(hfen)
    if state.is_terminal():
        logger.debug('check_ai: X game is terminal')
        return
    logger.debug('check_ai: √ game not terminal')

    best_move = find_best_move(hfen)
    if not best_move:
        logger.debug('check_ai: X no best move')
        return
    logger.debug('check_ai: √ found best move')

    # Is the move legal?
    q = best_move['q']
    r = best_move['r']
    if (q,r) not in state.get_legal_moves():
        logger.debug('check_ai: X illegal move')
        return
    logger.debug('check_ai: √ move is legal. saving...')

    # Make the move
    move = Move()
    move.game = game
    move.color = best_move['color']
    move.q = q
    move.r = r
    move.detail = 'ai'
    move.save()

    state = state.make_move((q, r))
    hfen = state.hfen

    # Once done, use Channels to communicate back to WebSocket clients
    logger.debug('check_ai: done. BROADCASTING?')
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'play_{game_uid}', {
        'type': 'broadcast_hfen',
        'hfen': hfen,
        'move': [move.color, move.q, move.r],
    })

    # Is the game over?
    if state.did_win():
        async_to_sync(channel_layer.group_send)(f'play_{game_uid}', {
            'type': 'broadcast_game_over',
            'result': 'RYGCBM'[state.prev_color_idx],
        })
        cache.delete(f'game_{game_uid}_colors')
    elif len(state.get_legal_moves()) == 0:
        async_to_sync(channel_layer.group_send)(f'play_{game_uid}', {
            'type': 'broadcast_game_over',
            'result': 'DRAW',
        })
        cache.delete(f'game_{game_uid}_colors')

    # Check again, in case it's still the AI's turn.
    check_ai(game_uid)

API_URL = os.environ.get('HEXACHROMIX_API_URL', 'http://api')
MAX_TIME = int(os.environ.get('HEXACHROMIX_AI_MAX_TIME', 1))
MAX_ITERATIONS = int(os.environ.get('HEXACHROMIX_AI_MAX_ITERATIONS', 100000))
def find_best_move(hfen1):
    logger.debug(f'finding best move for {hfen1}')
    url = API_URL + '/best/?' + urllib.parse.urlencode({'hfen':hfen1, 'max_time':MAX_TIME, 'max_iterations':MAX_ITERATIONS})
    #.use httpx instead. make it async to avoid blocking.
    response = urllib.request.urlopen(url)
    hfen2 = json.loads(response.read().decode('utf-8'))

    state = Game.state_from_hfen(hfen1)
    for move in state.get_legal_moves():
        if state.make_move(move).hfen == hfen2:
            logger.debug(f'move {move} matches')
            return {
                'hfen': hfen2,
                'q': move[0],
                'r': move[1],
                'color': hfen1.split()[1],
            }
