from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.db.models import Q
from django.contrib.auth import get_user_model

import os
from time import time
import random, re

from hexachromix.utils import HexachromixState


class Game(models.Model):
    class Variant(models.TextChoices):
        MRY = 'MRY', _('MRY GCB')
        # RGB = 'RGB', _('RGB CMY')
        MR = 'MR', _('MR YG CB')
        # RC = 'RC', _('RC BY GM')
        R = 'R', _('R Y G C B M')
        # SANDBOX = 'etc', _('RYGCBM')

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
        # FYI: Until Christmas Eve 2038 (ZZZZZZ), that means 6 extra chars. For a long time after that, it's 5.
        uid += ''.join(random.choices(alphabet, k=(12-len(uid))))

        return uid

    def gen_code():
        with open(os.path.join(os.path.dirname(__file__), 'wordlist.txt'), 'r') as file:
            words = [word.strip() for word in file.readlines()]

        for n in (2,3,4): # Try n times to find an n-char unique code.
            for _ in range(n):
                code = '-'.join(random.sample(words, n))
                if not Game.objects.filter(code=code).exists():
                    return code

        raise Exception('Could not generate unique code.')

    # Model fields
    id = models.AutoField(primary_key=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.RESTRICT)
    uid = models.CharField(max_length=12, unique=True, default=gen_uid, editable=False)
    code = models.CharField(max_length=26, unique=True, default=gen_code, editable=False)
    variant = models.CharField(choices=Variant.choices, max_length=3, editable=False)


    @property
    def moves(self):
        return self.move_set.all()

    @property
    def result(self):
        state = self.state
        if state.did_win():
            return Move.Color['RYGCBM'[state.prev_color_idx]]
        elif len(state.get_legal_moves()) == 0:
            return 'DRAW'

    @property
    def winner(self):
        state = self.state
        if state.did_win():
            gp = self.gameplayer_set.filter(color=Move.Color['RYGCBM'[state.prev_color_idx]]).first()
            if gp:
                return gp.player

    @property
    def is_active(self):
        return not self.state.is_terminal()

    @property
    def teams(self):
        return self.get_variant_display().split(' ')

    def team_players(self, team):
        return get_user_model().objects.filter(gameplayer__game=self, gameplayer__color__in=team).order_by('username').distinct()
    def team_players_display(self, team):
        return ' / '.join([player.username for player in self.team_players(team)])
    def all_players(self):
        return {team:self.team_players_display(team) for team in self.teams}

    @property
    def current_color(self):
        return Move.Color[self.state.get_current_color()]

    @property
    def hpgn(self):
        hpgn = '[Date "%s"]' % self.datetime_created.strftime('%Y-%m-%d')
        hpgn += '\n[Variant "%s"]' % self.get_variant_display()

        player_tags = self.hpgn_player_tags
        if player_tags:
            hpgn += '\n%s' % player_tags

        result = self.result
        if result:
            hpgn += '\n[Result "%s"]' % self.result

        moves = self.hpgn_moves
        if moves:
            hpgn += '\n\n' + self.hpgn_moves

        return hpgn

    @property
    def hpgn_player_tags(self):
        teams = []
        for team, players in self.all_players().items():
            if players:
                teams.append('[%s "%s"]' % (team, players))
        return '\n'.join(teams)

    @property
    def hpgn_moves(self):
        n = 1
        moves = []
        for move in self.moves:
            q = move.q if move.q < 0 else '+'+str(move.q)
            r = move.r if move.r < 0 else '+'+str(move.r)
            moves.append('%d. %s%s' % (n, q, r))
            n += 1
        return ' '.join(moves)

    @property
    def formatted_hpgn(self):
        hpgn = self.hpgn

        pattern = r'(\d+)\. '

        nmoves = len(re.findall(pattern, hpgn))
        maxdigs = len(str(nmoves))

        def repl(m):
            n = int(m.group(1))
            out = ''
            if n > 1 and n % 6 == 1:
                out += '\n'
            out += str(n).rjust(maxdigs, ' ') + '. '
            return out

        return re.sub(pattern, repl, self.hpgn)


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

    id = models.AutoField(primary_key=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    datetime_created = models.DateTimeField(auto_now_add=True)
    color = models.CharField(choices=Color.choices, max_length=1)
    q = models.SmallIntegerField()
    r = models.SmallIntegerField()
    # hfen = models.CharField(max_length=32, null=True, editable=False)#.make required
    details = models.TextField(null=True)

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
    id = models.AutoField(primary_key=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    color = models.CharField(choices=Move.Color.choices, max_length=1)


User = get_user_model()

# Extend the User model with a helper method to find all of their games:
#  - they authored it,
#  - they're a GamePlayer in it, or
#  - they're the author of a move in it.
def games_for_user(self):
    return Game.objects.filter(Q(author=self) | Q(gameplayer__player=self) | Q(move__player=self)).distinct()
User.add_to_class('hexachromix_games', games_for_user)

def games_my_turn(self):
    my_turn = []
    for game in Game.objects.filter(gameplayer__player=self).distinct().order_by('-datetime_created'):#.sort by oldest most-recent-move instead
        state = game.state
        gp = self.gameplayer_set.filter(game=game, color=state.get_current_color()).first()
        if gp and not state.is_terminal():
            my_turn.append(game)
    return my_turn
User.add_to_class('hexachromix_games_my_turn', games_my_turn)
