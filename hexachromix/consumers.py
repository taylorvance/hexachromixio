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
            #.add them to that team's group
            pass
        elif text_data_json['action'] == 'make_move':
            game = Game.objects.get(uid=self.game_uid)

            #.is it that color's turn?
            #.does this user control that color?
            #.is it a legal move?
            #.create move and broadcast hfen

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'send_hfen',
                    'hfen': game.hfen,
                }
            )

    def send_hfen(self, event):
        self.send(text_data=json.dumps({
            'hfen': event['hfen'],
        }))
