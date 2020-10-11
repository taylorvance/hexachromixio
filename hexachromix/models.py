from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.db.models import Q
from django.contrib.auth import get_user_model

from time import time
import random

from hexachromix.utils import HexachromixState


class Game(models.Model):
    class Variant(models.TextChoices):
        MRY = 'MRY', _('MRY GCB')
        RGB = 'RGB', _('RGB CMY')
        MR = 'MR', _('MR YG CB')
        RC = 'RC', _('RC BY GM')
        R = 'R', _('R Y G C B M')

    def gen_uid():
        alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'

        # Get the time (Unix epoch seconds) in base-36 representation.
        # (based on numpy.base_repr)
        num = int(time())
        base = len(alphabet)
        chars = []
        while num:
            chars.append(alphabet[num % base])
            num //= base
        uid = ''.join(reversed(chars or '0'))

        # Append some extra random chars to bring the total length to 12 characters.
        # FYI: Until Christmas Eve 2038 (ZZZZZZ), that means 6 extra chars.
        uid += ''.join(random.choices(alphabet, k=(12-len(uid))))

        return uid


    # Model fields
    datetime_created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.RESTRICT)
    uid = models.CharField(unique=True, editable=False, default=gen_uid, max_length=12)
    variant = models.CharField(choices=Variant.choices, max_length=3)


    @property
    def moves(self):
        return Move.objects.filter(game=self)

    @property
    def result(self):
        state = self.state
        if state.did_win():
            return Move.Color['RYGCBM'[state.prev_color_idx]]
        elif len(state.get_legal_moves()) == 0:
            return 'DRAW'
        else:
            return ''

    @property
    def winner(self):
        state = self.state
        if state.did_win():
            gp = GamePlayer.objects.filter(game=self, color=Move.Color['RYGCBM'[state.prev_color_idx]]).first()
            if gp is not None:
                return gp.player.username
        return ''

    @property
    def is_active(self):
        return not self.state.is_terminal()

    @property
    def current_color(self):
        return Move.Color[self.state.get_current_color()]

    @property
    def hpgn(self):
        hpgn = ''
        hpgn += '[Sometag "some value"]'
        hpgn += '\n[Anothertag "another value"]'

        hpgn += '\n1. '
        moves = self.moves
        for move in moves:
            hpgn += ' %s,%s' % (move.q, move.r)

        return hpgn

    @property
    def players(self):
        return get_user_model().objects.filter(gameplayer__game=self).distinct()

    @cached_property
    def hfen(self):
        state = HexachromixState(variant=self.variant)

        for move in self.moves:
            state = state.make_move((move.q, move.r))

        return state.hfen

    @cached_property
    def state(self):
        return self.state_from_hfen(self.hfen)

    @staticmethod
    def state_from_hfen(hfen):
        return HexachromixState.state_from_hfen(hfen)


class Move(models.Model):
    class Color(models.TextChoices):
        R = 'R', _('Red')
        Y = 'Y', _('Yellow')
        G = 'G', _('Green')
        C = 'C', _('Cyan')
        B = 'B', _('Blue')
        M = 'M', _('Magenta')

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    datetime_created = models.DateTimeField(auto_now_add=True)
    color = models.CharField(choices=Color.choices, max_length=1)
    q = models.SmallIntegerField()
    r = models.SmallIntegerField()

    @property
    def hfen(self):
        state = HexachromixState(variant=self.game.variant)

        for move in self.game.moves:
            state = state.make_move((move.q, move.r))
            if self is move:
                break

        return state.hfen

    class Meta:
        order_with_respect_to = 'game'


class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    color = models.CharField(choices=Move.Color.choices, max_length=1)


# Extend the User model with a helper method to find all of their games
# Games where they are the author, a game-player, or a move-player
User = get_user_model()

def games_for_user(self):
    return Game.objects.filter(Q(author=self) | Q(gameplayer__player=self) | Q(move__player=self)).distinct()
User.add_to_class('hexachromix_games', games_for_user)

def games_my_turn(self):
    my_turn = []
    for game in Game.objects.filter(gameplayer__player=self).distinct().order_by('-datetime_created'):
        state = game.state
        gp = GamePlayer.objects.filter(game=game, color=state.get_current_color(), player=self).first()
        if gp and not state.is_terminal():
            my_turn.append(game)
    return my_turn
User.add_to_class('hexachromix_games_my_turn', games_my_turn)
