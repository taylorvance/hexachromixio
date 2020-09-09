from django.db import models
from django.utils.translation import gettext_lazy as _

from time import time
import random


class Game(models.Model):
    class Variant(models.TextChoices):
        MRY = 'MRY', _('MRY GCB')
        MR = 'MR', _('MR YG CB')

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

    datetime_created = models.DateTimeField(auto_now_add=True)
    uid = models.CharField(unique=True, editable=False, default=gen_uid, max_length=12)
    variant = models.CharField(choices=Variant.choices, max_length=3)


class Move(models.Model):
    class Color(models.TextChoices):
        RED = 'R'
        YELLOW = 'Y'
        GREEN = 'G'
        CYAN = 'C'
        BLUE = 'B'
        MAGENTA = 'M'

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    datetime_created = models.DateTimeField(auto_now_add=True)
    color = models.CharField(choices=Color.choices, max_length=1)
    q = models.SmallIntegerField()
    r = models.SmallIntegerField()

    class Meta:
        order_with_respect_to = 'game'
