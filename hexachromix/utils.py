from copy import deepcopy
from collections import defaultdict
from queue import Queue
import re


class HexachromixState():
    def __init__(self, variant='MRY'):
        self.variant = variant

        # RYGCBM := 012345
        self.cur_color_idx = 0
        self.prev_color_idx = self.cur_color_idx - 1

        self.board = HexachromixBoard()

    def get_current_color(self):
        return 'RYGCBM'[self.cur_color_idx]

    def get_current_team(self):
        color = self.get_current_color()

        if self.variant == 'MRY':
            return 'MRY' if color in 'MRY' else 'GCB'
        elif self.variant == "RGB":
            return 'RGB' if color in 'RGB' else 'CMY'
        elif self.variant == "RC":
            return 'RC' if color in 'RC' else ('BY' if color in 'BY' else 'GM')
        elif self.variant == 'MR':
            return 'MR' if color in 'MR' else ('YG' if color in 'YG' else 'CB')
        else:
            return color

    def get_legal_moves(self):
        valid_chars = self.get_current_color().lower()
        valid_chars += 'RYGCBM'[(self.cur_color_idx - 2) % 6]
        valid_chars += 'RYGCBM'[(self.cur_color_idx + 2) % 6]

        legal_moves = []

        for q in self.board.spaces:
            for r in self.board.spaces[q]:
                char = self.board.spaces[q][r]
                if char in valid_chars or char == '':
                    legal_moves.append((q, r))

        return legal_moves

    def make_move(self, move):
        """ move is a tuple(q, r) """
        (q, r) = move

        new_state = deepcopy(self)

        my_char = new_state.get_current_color()

        old_char = new_state.board.spaces[q][r]
        if old_char == 'RYGCBM'[(new_state.cur_color_idx - 2) % 6]:
            new_char = 'RYGCBM'[(new_state.cur_color_idx - 1) % 6].lower()
        elif old_char == 'RYGCBM'[(new_state.cur_color_idx + 2) % 6]:
            new_char = 'RYGCBM'[(new_state.cur_color_idx + 1) % 6].lower()
        else:
            new_char = my_char

        new_state.board.spaces[q][r] = new_char

        new_state.prev_color_idx = new_state.cur_color_idx
        new_state.cur_color_idx = (new_state.cur_color_idx + 1) % 6

        return new_state

    """#.not using it now but it could be useful in the future
    def path_to_victory(self, color_idx):
        owned = [
            'RYGCBM'[color_idx],
            'RYGCBM'[(color_idx - 1) % 6].lower(),
            'RYGCBM'[(color_idx + 1) % 6].lower()
        ]

        playable = [
            '',
            'rygcbm'[color_idx],
            'RYGCBM'[(color_idx - 2) % 6],
            'RYGCBM'[(color_idx + 2) % 6]
        ]

        sides = self.board.get_sides()
        starts = sides[color_idx]
        goals = sides[(color_idx + 3) % 6]

        # cost of the space if I: own it; can play on it; can't play on it
        own_play_no_cost = [0, 1, 3]

        frontier = PriorityQueue()
        cost_so_far = {}
        for start in starts:
            char = str(self.board.spaces[start[0]][start[1]])
            if char in owned:
                frontier.put(start, own_play_no_cost[0])
                cost_so_far[tuple(start)] = own_play_no_cost[0]
            elif char in playable:
                frontier.put(start, own_play_no_cost[1])
                cost_so_far[tuple(start)] = own_play_no_cost[1]
            else:
                frontier.put(start, own_play_no_cost[2])
                cost_so_far[tuple(start)] = own_play_no_cost[2]

        while not frontier.empty():
            current_space = frontier.get()

            # "neighbors" are all adjacent spaces
            neighbors = []
            directions = [[1,0], [1,-1], [0,-1], [-1,0], [-1,1], [0,1]]
            for direction in directions:
                q = current_space[0] + direction[0]
                if q in self.board.spaces:
                    r = current_space[1] + direction[1]
                    if r in self.board.spaces[q]:
                        neighbors.append([q, r])

            for next_space in neighbors:
                char = str(self.board.spaces[next_space[0]][next_space[1]])

                new_cost = cost_so_far[tuple(current_space)]
                if char in owned:
                    new_cost += own_play_no_cost[0]
                elif char in playable:
                    new_cost += own_play_no_cost[1]
                else:
                    new_cost += own_play_no_cost[2]

                if tuple(next_space) not in cost_so_far or new_cost < cost_so_far[tuple(next_space)]:
                    cost_so_far[tuple(next_space)] = new_cost
                    priority = new_cost
                    # Add the distance to the closest goal space (this is the A* heuristic).
                    manhattan = 10000
                    for goal in goals:
                        dist = (abs(goal[0] - next_space[0]) + abs(goal[0] + goal[1] - next_space[0] - next_space[1]) + abs(goal[1] - next_space[1])) / 2
                        if dist < manhattan:
                            manhattan = dist
                    priority += manhattan
                    frontier.put(next_space, priority)

        shortest = 10000
        for goal in goals:
            if cost_so_far[tuple(goal)] < shortest:
                shortest = cost_so_far[tuple(goal)]

        return shortest
    """

    def has_path(self, color_idx):
        owned = [
            'RYGCBM'[color_idx],
            'RYGCBM'[(color_idx - 1) % 6].lower(),
            'RYGCBM'[(color_idx + 1) % 6].lower()
        ]

        sides = self.board.get_sides()
        starts = sides[color_idx]
        goals = sides[(color_idx + 3) % 6]

        frontier = Queue()
        reached = []
        for start in starts:
            if self.board.spaces[start[0]][start[1]] in owned:
                frontier.put(start)
                reached.append(start)

        while not frontier.empty():
            current_space = frontier.get()

            # "neighbors" are all adjacent owned spaces
            neighbors = []
            directions = [[1,0], [1,-1], [0,-1], [-1,0], [-1,1], [0,1]]
            for direction in directions:
                q = current_space[0] + direction[0]
                if q in self.board.spaces:
                    r = current_space[1] + direction[1]
                    if r in self.board.spaces[q]:
                        if self.board.spaces[q][r] in owned:
                            if [q, r] in goals:
                                return True
                            else:
                                neighbors.append([q, r])

            for next_space in neighbors:
                if next_space not in reached:
                    frontier.put(next_space)
                    reached.append(next_space)

        return False

    def did_win(self):
        return self.has_path(self.prev_color_idx)

    def is_terminal(self):
        return len(self.get_legal_moves()) == 0 or self.did_win()

    def get_reward(self):
        # reward a winner and slightly punish a CAT causer
        return 1 if self.did_win() else -0.5

    @property
    def hfen(self):
        out = ''

        for q in self.board.spaces:
            blanks = 0

            for r in self.board.spaces[q]:
                char = self.board.spaces[q][r]

                if char == '':
                    blanks += 1
                else:
                    if blanks > 0:
                        out += str(blanks)
                        blanks = 0

                    out += char

            if blanks > 0:
                out += str(blanks)

            out += '/'

        out = out[:-1]

        out += ' %s %s' % (self.get_current_color(), self.variant)

        return out

    @staticmethod
    def state_from_hfen(hfen):
        hfen_parts = hfen.split(' ')

        state = HexachromixState(variant=hfen_parts[2])

        state.cur_color_idx = 'RYGCBM'.index(hfen_parts[1])
        state.prev_color_idx = (state.cur_color_idx - 1) % 6

        chars = re.sub('\d', lambda x: '-'*int(x.group(0)), hfen_parts[0].replace('/',''))
        i = 0
        for q in state.board.spaces:
            for r in state.board.spaces[q]:
                if chars[i] != '-':
                    state.board.spaces[q][r] = chars[i]
                i += 1

        return state

    def __repr__(self):
        return self.hfen


class HexachromixBoard():
    def __init__(self, radius=2):
        self.radius = radius
        self.spaces = defaultdict(dict)
        for q in range(-radius, radius+1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2+1):
                self.spaces[q][r] = ''

    def get_sides(self):
        radius = self.radius
        sides = [[],[],[],[],[],[]]
        for i in range(radius + 1):
            sides[0].append([-radius, i])
            sides[1].append([i-radius, radius])
            sides[2].append([i, radius-i])
            sides[3].append([radius, -i])
            sides[4].append([radius-i, -radius])
            sides[5].append([-i, i-radius])
        return sides
