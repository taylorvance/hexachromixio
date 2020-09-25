from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json

from hexachromix.models import Game

class PlayConsumer(WebsocketConsumer):
    def connect(self):
        self.game_uid = self.scope['url_route']['kwargs']['game_uid']
        self.group_name = 'play_%s' % self.game_uid

        game = Game.objects.get(uid=self.game_uid)

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        print('PlayConsumer: %s connected to %s' % (self.scope['user'].username or 'anon', self.game_uid))
        self.accept()

        self.send(text_data=json.dumps({
            'connected_user': self.scope['user'].id,
            'grpname': self.group_name,
            'channelname': self.channel_name,
            'hfen': game.hfen,
            # 'sess': self.scope['session'],
        }))

        state = Game.state_from_hfen(game.hfen)
        if state.is_terminal():
            self.send(text_data=json.dumps({
                'termination': 'generic game over',
            }))

    def disconnect(self, close_code):
        #.free up that player's color(s)

        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        if text_data_json['action'] == 'claim_color':
            #.is it unclaimed?
            #.is it on their same team?
            #.add them to that team's group and set something in a self/static var or session or db??
            async_to_sync(self.channel_layer.group_add)(
                'play_%s_color_%s' % (self.game_uid, Move.Color[text_data_json['color']]),
                self.channel_name
            )
            #.broadcast the claim to everyone
            #.but how would we let people who join later know? how would we reestablish claims on dis/reconnect?
        elif text_data_json['action'] == 'make_move':
            # print('moving', self.group_name, self.channel_layer.group_channels(self.group_name))

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

            state = state.make_move((q, r))
            hfen = state.hfen

            # Is the game over?
            if state.did_win():
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {
                        'type': 'game_over',
                        'winner': 'RYGCBM'[state.prev_color_idx],
                    }
                )
            elif len(state.get_legal_moves()) == 0:
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {
                        'type': 'game_over',
                        'winner': 'CAT',
                    }
                )

            # Broadcast the new HFEN to everyone
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'send_hfen',
                    'hfen': hfen,
                    'move': [move.color, move.q, move.r],
                }
            )

    def send_hfen(self, event):
        self.send(text_data=json.dumps({
            'hfen': event['hfen'],
            'move': event['move'],
        }))

    def game_over(self, event):
        self.send(text_data=json.dumps({
            'termination': event['winner'],
        }))
