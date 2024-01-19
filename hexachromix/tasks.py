from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache

import os
import logging
import urllib
import json
from time import time
from base64 import b64encode

from hexachromix.models import Game, Move

logger = logging.getLogger(__name__)
logger.debug(f'using logger {__name__}')


@shared_task
def check_ai(game_uid):
    logger.debug(f'check_ai: begin {game_uid}')

    lock_key = f'ai-proc-{game_uid}'
    if not cache.add(lock_key, "true", 10):
        logger.debug(f'check_ai: X game {game_uid} is locked')
        return
    logger.debug(f'check_ai: √ game {game_uid} not locked')

    try:
        game = Game.objects.get(uid=game_uid)
        hfen = game.hfen

        color = hfen.split()[1]
        color_players = cache.get(f'game_{game_uid}_colors', {})
        logger.debug(f'check_ai: color_players {color_players}')
        if not str(color_players.get(color)).startswith('ai:'):
            logger.debug('check_ai: X not an ai')
            return
        logger.debug('check_ai: √ is ai')

        # -- THE FOLLOWING IS DUPLICATED FROM THE MAKE_MOVE ACTION IN PLAYCONSUMER --

        # Is the game over?
        state = Game.state_from_hfen(hfen)
        if state.is_terminal():
            logger.debug('check_ai: X game is terminal')
            return
        logger.debug('check_ai: √ game not terminal')

        logger.info(f'{game_uid}: Finding best move for "{hfen}"...')
        best_move = find_best_move(hfen)
        if not best_move:
            logger.debug('check_ai: X no best move')
            return
        logger.debug('check_ai: √ found best move')
        logger.info(f'{game_uid}: Found best move "{best_move["hfen"]}" in {best_move["time"]:.3f}s.')

        # Is the move legal?
        q = best_move['q']
        r = best_move['r']
        if (q,r) not in state.get_legal_moves():
            logger.debug('check_ai: X illegal move')
            return
        logger.debug('check_ai: √ move is legal. saving...')

        state = state.make_move((q,r))
        hfen = state.hfen

        # Make the move
        move = Move()
        move.game = game
        move.color = best_move['color']
        move.q = q
        move.r = r
        move.details = f'ai: t={best_move["time"]:.3f}s'
        move.save()

        # Once done, use Channels to communicate back to WebSocket clients.
        logger.debug('check_ai: done. BROADCASTING?')
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'play_{game_uid}', {
            'type': 'broadcast_hfen',
            'hfen': hfen,
            'move': [move.color,move.q,move.r],
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
    finally:
        logger.debug('check_ai: releasing lock')
        cache.delete(lock_key)


def find_best_move(hfen1):
    logger.debug(f'finding best move for {hfen1}')

    mt = int(os.environ.get('HEXACHROMIX_AI_MAX_TIME', 1))
    mi = int(os.environ.get('HEXACHROMIX_AI_MAX_ITERATIONS', 100000))

    apiuser = os.getenv('HEXACHROMIX_API_USER')
    apipass = os.getenv('HEXACHROMIX_API_PASS')
    if apiuser and apipass:
        creds = b64encode(f'{apiuser}:{apipass}'.encode()).decode()
        headers = {'Authorization': f'Basic {creds}'}
    else:
        headers = {}

    apiurl = os.environ.get('HEXACHROMIX_API_URL', 'http://api') + '/best/?' + urllib.parse.urlencode({'hfen':hfen1, 'max_time':mt, 'max_iterations':mi})

    #.use httpx instead. make it async to avoid blocking.
    t = time()
    req = urllib.request.Request(apiurl, headers=headers)
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode('utf-8'))
    t = time() - t

    hfen2 = data

    state = Game.state_from_hfen(hfen1)
    for move in state.get_legal_moves():
        if state.make_move(move).hfen == hfen2:
            logger.debug(f'move {move} matches')
            return {
                'hfen': hfen2,
                'q': move[0],
                'r': move[1],
                'color': hfen1.split()[1],
                'max_time': mt,
                'max_iterations': mi,
                'time': t,
            }
