from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from time import time
import random


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
    def is_active(self):
        return True#.

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
    def hfen(self):
        # The initial HFEN
        hfen = '3/4/5/4/3 R %s' % self.variant

        #.get hfen from most recent move
        chars = "RYGCBMrygcbm"
        hfen = ''
        for n in [3,4,5,4,3]:
            hfen += ''.join(random.choices(chars,k=n)) + '/'
        hfen = '%s %s %s' % (hfen[:-1], random.choice('RYGCBM'), self.variant)

        return hfen


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
        hfen = ''

        # state = HexachromixState()

        moves = self.game.moves
        for move in moves:
            # state = state.make_move(move)
            # hfen += state.get_hfen()
            pass

        return hfen

    class Meta:
        order_with_respect_to = 'game'
