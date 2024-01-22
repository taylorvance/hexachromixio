from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.cache import cache
from channels.db import database_sync_to_async

import os
import json
import hashlib
import urllib.parse, urllib.request
import logging

from hexachromix.models import Game, Move, GamePlayer
from hexachromix.tasks import check_ai

logger = logging.getLogger(__name__)
logger.debug(f'using logger {__name__}')


class PlayConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_uid = self.scope['url_route']['kwargs']['game_uid']
        if not self.game_uid:
            self.close()

        self.group_name = f'play_{self.game_uid}'

        # Add this channel to the game group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        game = await fetch_game(self.game_uid)
        if not game:
            self.close()

        # Generate an identifier for this player so they can reconnect and maintain color control.
        if self.scope['user'].is_authenticated:
            # This allows an authenticated user to maintain colors across devices.
            # If this changes, update get_color_players().
            self.player_identifier = f'user:{self.scope["user"].username}'
        elif self.scope['session'].session_key:
            # Hash based on ses key, game uid, and salt.
            hashid = f'{self.scope["session"].session_key} - {self.game_uid} - makes my steaks taste great'
            hashid = hashlib.md5(hashid.encode('utf-8')).hexdigest()
            hashid = str(hashid)[:16]
            self.player_identifier = f'anon:{hashid}'
        else:
            # If they somehow don't have a session, treat them all the same.
            self.player_identifier = 'anon:whoareyou'

        logger.info(f'PlayConsumer: {self.player_identifier} connected to {self.game_uid}')

        hfen = await fetch_game_hfen(game)
        color_players = await self.get_color_players()

        await self.send(text_data=json.dumps({
            'pid': self.player_identifier,
            'hfen': hfen,
            'color_players': color_players,
        }))

        state = Game.state_from_hfen(hfen)
        if state.is_terminal():
            await self.send(text_data=json.dumps({
                'termination': 'generic game over',
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        logger.debug(f'received msg: {text_data_json}')

        if text_data_json['action'] == 'claim_color':
            await self.claim_color(text_data_json['color'])
        elif text_data_json['action'] == 'ai_claim_colors':
            # Is this the game author?
            game = await fetch_game(self.game_uid)
            if self.scope['user'] != await fetch_game_author(game):
                await self.send(text_data=json.dumps({
                    'error': 'NO_PERMISSION',
                }))
                return

            cache_val = await self.get_color_players()
            remaining_colors = [c for c in 'RYGCBM' if not cache_val.get(c)]
            for color in remaining_colors:
                cache_val[color] = 'ai:v1'

            await async_cache_set(f'game_{self.game_uid}_colors', cache_val, 3600)

            await self.channel_layer.group_send(self.group_name, {
                'type': 'broadcast_color_players',
                'color_players': cache_val,
            })
        elif text_data_json['action'] == 'release_color':
            color = Move.Color[text_data_json['color']]

            cache_val = await self.get_color_players()

            # Does the player control that color?
            if cache_val.get(color) != self.player_identifier:
                await self.send(text_data=json.dumps({'error': 'NOT_YOUR_COLOR'}))
                return

            # Delete that color-player from the db and the cache
            if self.scope['user'].is_authenticated:
                # gp = await database_sync_to_async(GamePlayer.objects.filter)(color=color, game__uid=self.game_uid)
                # delete_game_player(gp)
                queryset = await database_sync_to_async(GamePlayer.objects.filter)(color=color, game__uid=self.game_uid)
                await database_sync_to_async(queryset.delete)()
            del cache_val[color]

            await async_cache_set(f'game_{self.game_uid}_colors', cache_val, 3600)

            await self.channel_layer.group_send(self.group_name, {
                'type': 'broadcast_color_players',
                'color_players': cache_val,
            })
        elif text_data_json['action'] == 'reset_colors':
            await self.reset_colors()
        elif text_data_json['action'] == 'make_ai_move':
            check_ai.delay(self.game_uid, text_data_json.get('difficulty'))
        elif text_data_json['action'] == 'make_move':
            #.move all of this into a function so we can use it for ai moves too
            game = await fetch_game(self.game_uid)
            hfen = await fetch_game_hfen(game)

            # Does the player's HFEN match the game's current HFEN?
            if text_data_json['hfen'] != hfen:
                await self.send(text_data=json.dumps({
                    'error': 'OUTDATED_HFEN',
                    'hfen': hfen,
                }))
                return

            # Is it that color's turn?
            color = text_data_json['color']
            expected_color = hfen.split()[1]
            if color != expected_color:
                await self.send(text_data=json.dumps({
                    'error': 'OUT_OF_TURN',
                    'color': color,
                    'expected_color': expected_color,
                }))
                return

            # Does the player control that color?
            if False:
                #.todo
                await self.send(text_data=json.dumps({
                    'error': 'NOT_YOUR_COLOR',
                    'color': color,
                }))
                return

            # Is the game over?
            state = Game.state_from_hfen(hfen)
            if state.is_terminal():
                await self.send(text_data=json.dumps({'error': 'GAME_OVER'}))
                return

            # Is the move legal?
            q = text_data_json['q']
            r = text_data_json['r']
            if (q, r) not in state.get_legal_moves():
                await self.send(text_data=json.dumps({'error': 'ILLEGAL_MOVE'}))
                return

            # Make the move
            move = Move()
            move.game = game
            if self.scope['user'].is_authenticated:
                move.player = self.scope['user']
            move.color = color
            move.q = q
            move.r = r
            await save_move(move)

            # Renew the color-player cache
            await async_cache_touch(f'game_{self.game_uid}_colors', 3600)

            state = state.make_move((q, r))
            hfen = state.hfen

            # Is the game over?
            if state.did_win():
                await self.channel_layer.group_send(self.group_name, {
                    'type': 'broadcast_game_over',
                    'result': 'RYGCBM'[state.prev_color_idx],
                })
                # Delete the color-player cache
                await async_cache_delete(f'game_{self.game_uid}_colors')
            elif len(state.get_legal_moves()) == 0:
                await self.channel_layer.group_send(self.group_name, {
                    'type': 'broadcast_game_over',
                    'result': 'DRAW',
                })
                # Delete the color-player cache
                await async_cache_delete(f'game_{self.game_uid}_colors')

            # Broadcast the new HFEN to everyone
            await self.channel_layer.group_send(self.group_name, {
                'type': 'broadcast_hfen',
                'hfen': hfen,
                'move': [move.color, move.q, move.r],
            })


    async def claim_color(self, color:str):
        color = Move.Color[color]

        # Did they ask for a valid color?
        if not color:
            self.send(text_data=json.dumps({'error': 'INVALID_COLOR'}))
            return

        cache_val = await self.get_color_players()

        # Is the color available?
        color_owner = cache_val.get(color)
        if color_owner and color_owner != self.player_identifier:
            self.send(text_data=json.dumps({'error': 'COLOR_UNAVAILABLE'}))
            return

        #.Is the color on an opposing team?
        if not 'on the same team':
            self.send(text_data=json.dumps({'error': 'OPPOSING_TEAM'}))
            return

        # Set that color-player in the db and the cache.
        if self.scope['user'].is_authenticated:
            game = await fetch_game(self.game_uid)
            await database_sync_to_async(GamePlayer.objects.create)(
                game = game,
                player = self.scope['user'],
                color = color
            )
        cache_val[color] = self.player_identifier

        await async_cache_set(f'game_{self.game_uid}_colors', cache_val, 3600)

        await self.channel_layer.group_send(self.group_name, {
            'type': 'broadcast_color_players',
            'color_players': cache_val,
        })

    async def reset_colors(self):
        # Is this the game author?
        game = await fetch_game(self.game_uid)
        if self.scope['user'] != await fetch_game_author(game):
            await self.send(text_data=json.dumps({
                'error': 'NO_PERMISSION',
            }))
            return

        await delete_game_players(self.game_uid)
        await async_cache_delete(f'game_{self.game_uid}_colors')

        await self.channel_layer.group_send(self.group_name, {
            'type': 'broadcast_color_players',
            'color_players': {},
        })

    async def get_color_players(self):
        cache_key = f'game_{self.game_uid}_colors'

        cache_val = await async_cache_get(cache_key)
        if cache_val is not None:
            return cache_val

        cache_val = {}

        gps = await fetch_game_players(self.game_uid)
        for gp in gps:
            cache_val[gp['color']] = f'user:{gp["player__username"]}'

        await async_cache_set(cache_key, cache_val, 3600)

        return cache_val

    async def broadcast_hfen(self, event):
        await self.send(text_data=json.dumps({
            'hfen': event['hfen'],
            'move': event['move'],
        }))

    async def broadcast_color_players(self, event):
        await self.send(text_data=json.dumps({
            'color_players': event['color_players'],
        }))

    async def broadcast_game_over(self, event):
        await self.send(text_data=json.dumps({
            'termination': event['result'],
        }))


@database_sync_to_async
def fetch_game(uid):
    return Game.objects.get(uid=uid)
@database_sync_to_async
def fetch_game_hfen(game):
    return game.hfen
@database_sync_to_async
def fetch_game_author(game):
    return game.author

@database_sync_to_async
def fetch_game_players(game_uid):
    return list(GamePlayer.objects.filter(game__uid=game_uid).values('color', 'player__username'))

@database_sync_to_async
def delete_game_player(gp):
    gp.delete()
@database_sync_to_async
def delete_game_players(game_uid):
    GamePlayer.objects.filter(game__uid=game_uid).delete()

@database_sync_to_async
def save_move(move):
    move.save()

@sync_to_async
def async_cache_get(key, default=None): return cache.get(key, default)
@sync_to_async
def async_cache_set(key, value, timeout): return cache.set(key, value, timeout)
@sync_to_async
def async_cache_delete(key): return cache.delete(key)
@sync_to_async
def async_cache_touch(key, timeout): return cache.touch(key, timeout)
