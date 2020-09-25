from django.test import TestCase

from hexachromix.models import Game, Move
from hexachromix.utils import HexachromixState

class StateTestCase(TestCase):
    def test_state_from_hfen(self):
        hfens = [
            '3/4/5/4/3 M MR',
            'RRR/RRRR/RRRRR/RRRR/RRR M MR',
            'R1R/RRRR/RRRRR/RRRR/RRR M MR',
            '1R1/2R1/2R2/2R1/1R1 M MR',
        ]
        for hfen in hfens:
            state = HexachromixState.state_from_hfen(hfen)
            self.assertEqual(state.hfen, hfen)
            self.assertEqual(state.get_current_color(), Move.Color.M)
            self.assertEqual(state.variant, Game.Variant.MR)

    def test_get_legal_moves(self):
        state = HexachromixState()
        self.assertEqual(state.get_current_color(), Move.Color.R)
        self.assertEqual(len(state.get_legal_moves()), 19)

        self.assertEqual(len(HexachromixState.state_from_hfen('3/4/5/4/3 R MRY').get_legal_moves()), 19)
        self.assertEqual(len(HexachromixState.state_from_hfen('R2/4/5/4/3 R MRY').get_legal_moves()), 18)
        self.assertEqual(len(HexachromixState.state_from_hfen('RRR/RRRR/RRRRR/RRRR/RRR R MRY').get_legal_moves()), 0)

    def test_did_win(self):
        self.assertEqual(HexachromixState.state_from_hfen('R2/R3/R4/R3/R2 Y MRY').did_win(), True)
        self.assertEqual(HexachromixState.state_from_hfen('C2/C3/C4/C3/C2 B MRY').did_win(), True)
        self.assertEqual(HexachromixState.state_from_hfen('C2/C3/5/C3/C2 B MRY').did_win(), False)

        self.assertEqual(HexachromixState.state_from_hfen('3/4/BBBBB/4/3 M MRY').did_win(), True)
        self.assertEqual(HexachromixState.state_from_hfen('3/4/MMMMM/4/3 R MRY').did_win(), True)
        self.assertEqual(HexachromixState.state_from_hfen('3/4/YYYYY/4/3 G MRY').did_win(), True)
        self.assertEqual(HexachromixState.state_from_hfen('3/4/GGGGG/4/3 C MRY').did_win(), True)

    def test_is_terminal(self):
        self.assertEqual(HexachromixState.state_from_hfen('3/4/5/4/3 R MRY').is_terminal(), False)
