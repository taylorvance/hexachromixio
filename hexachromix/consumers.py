from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.core.cache import cache
import json
import hashlib, uuid

from hexachromix.models import Game, Move

class PlayConsumer(WebsocketConsumer):
    def connect(self):
        self.game_uid = self.scope['url_route']['kwargs']['game_uid']
        if not self.game_uid:
            self.close()

        self.group_name = 'play_' + self.game_uid

        # Add this channel to the game group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        # Generate an identifier for this player so they can reconnect and maintain color control
        if self.scope['user'].is_authenticated:
            # This allows a user to maintain colors across devices
            self.player_identifier = self.scope['user'].username
        elif self.scope['session'].session_key:
            # Hash based on ses key, game uid, and salt
            #.move the salt to untracked cfg
            hashid = str(self.scope['session'].session_key) + self.game_uid + 'makes ma steaks taste great'
            hashid = hashlib.md5(hashid.encode('utf-8')).hexdigest()
            self.player_identifier = str(hashid)[:12]
        else:
            # If they somehow don't have a session, treat them all the same
            self.player_identifier = 'whoareyou'
        # print('PlayConsumer: %s connected to %s' % (self.player_identifier, self.game_uid))

        # Accept the connection before sending information about the current game state
        self.accept()

        game = Game.objects.get(uid=self.game_uid)

        self.send(text_data=json.dumps({
            'pid': self.player_identifier,
            'hfen': game.hfen,
            'color_players': cache.get('game_%s_colors' % self.game_uid, {}),
        }))

        state = Game.state_from_hfen(game.hfen)
        if state.is_terminal():
            self.send(text_data=json.dumps({
                'termination': 'generic game over',
            }))


    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )


    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        if text_data_json['action'] == 'claim_color':
            color = Move.Color[text_data_json['color']]

            cache_key = 'game_%s_colors' % self.game_uid
            cache_val = cache.get(cache_key, {})

            # Is the color available?
            if cache_val.get(color) and cache_val.get(color) != self.player_identifier:
                self.send(text_data=json.dumps({
                    'error': 'COLOR_UNAVAILABLE',
                }))
                return

            #.Is the color on an opposing team?
            if not 'on the same team':
                self.send(text_data=json.dumps({
                    'error': 'OPPOSING_TEAM',
                }))
                return

            cache_val[color] = self.player_identifier
            cache.set(cache_key, cache_val, 3600)

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'broadcast_color_players',
                    'color_players': cache_val,
                }
            )
        elif text_data_json['action'] == 'release_color':
            color = Move.Color[text_data_json['color']]

            cache_key = 'game_%s_colors' % self.game_uid
            cache_val = cache.get(cache_key, {})

            # Does the player control that color?
            if cache_val.get(color) != self.player_identifier:
                self.send(text_data=json.dumps({
                    'error': 'NOT_YOUR_COLOR',
                }))
                return

            cache_val[color] = None
            cache.set(cache_key, cache_val, 3600)

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'broadcast_color_players',
                    'color_players': cache_val,
                }
            )
        elif text_data_json['action'] == 'release_all_colors':
            # Is this the game author?
            if self.scope['user'] != Game.objects.get(uid=self.game_uid).author:
                self.send(text_data=json.dumps({
                    'error': 'NO_PERMISSION',
                }))
                return

            cache.delete('game_%s_colors' % self.game_uid)

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'broadcast_color_players',
                    'color_players': {},
                }
            )
        elif text_data_json['action'] == 'make_move':
            game = Game.objects.get(uid=self.game_uid)
            hfen = game.hfen

            # Does the player's HFEN match the game's current HFEN?
            if text_data_json['hfen'] != hfen:
                self.send(text_data=json.dumps({
                    'error': 'OUTDATED_HFEN',
                    'hfen': hfen,
                }))
                return

            # Is it that color's turn?
            color = text_data_json['color']
            expected_color = hfen.split(' ')[1]
            if color != expected_color:
                self.send(text_data=json.dumps({
                    'error': 'OUT_OF_TURN',
                    'color': color,
                    'expected_color': expected_color,
                }))
                return

            # Does the player control that color?
            if False:
                #.todo
                self.send(text_data=json.dumps({
                    'error': 'NOT_YOUR_COLOR',
                    'color': color,
                }))
                return

            # Is the game over?
            state = Game.state_from_hfen(hfen)
            if state.is_terminal():
                self.send(text_data=json.dumps({
                    'error': 'GAME_OVER',
                }))
                return

            # Is the move legal?
            q = text_data_json['q']
            r = text_data_json['r']
            if (q, r) not in state.get_legal_moves():
                self.send(text_data=json.dumps({
                    'error': 'ILLEGAL_MOVE',
                }))
                return

            # Make the move
            move = Move()
            move.game = game
            if self.scope['user'].is_authenticated:
                move.player = self.scope['user']
            move.color = color
            move.q = q
            move.r = r
            move.save()

            # Renew the color-player cache
            cache.touch('game_%s_colors' % self.game_uid, 3600)

            state = state.make_move((q, r))
            hfen = state.hfen

            # Is the game over?
            if state.did_win():
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {
                        'type': 'broadcast_game_over',
                        'result': 'RYGCBM'[state.prev_color_idx],
                    }
                )

                # Delete the color-player cache
                cache.delete('game_%s_colors' % self.game_uid)
            elif len(state.get_legal_moves()) == 0:
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {
                        'type': 'broadcast_game_over',
                        'result': 'DRAW',
                    }
                )

                # Delete the color-player cache
                cache.delete('game_%s_colors' % self.game_uid)

            # Broadcast the new HFEN to everyone
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'broadcast_hfen',
                    'hfen': hfen,
                    'move': [move.color, move.q, move.r],
                }
            )


    def broadcast_hfen(self, event):
        self.send(text_data=json.dumps({
            'hfen': event['hfen'],
            'move': event['move'],
        }))

    def broadcast_color_players(self, event):
        self.send(text_data=json.dumps({
            'color_players': event['color_players'],
        }))

    def broadcast_game_over(self, event):
        self.send(text_data=json.dumps({
            'termination': event['result'],
        }))
