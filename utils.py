import numpy as np
from collections import Counter


def rotate_list(l, n):
    return l[-n:] + l[:-n]

class Move:
    def __init__(self, move, amount=0, actor=None):
        self.validate_move(move, amount)
        self.move = move
        self.amount = amount
        self.actor = actor
    
    def validate_move(self, move, amount):
        if move not in ["fold", "call", "check", "raise"]:
            raise ValueError("invalid move type {}, must be one of 'fold', 'call', 'check', or 'raise'".format(move))
        if move == "raise":
            if amount <= 0:
                raise ValueError("cannot raise {}, must raise a strictly positive amount".format(amount))

class Hand:
    def __init__(self, cards):
        self.faces_dict = {str(num+1): num for num in range(9)}
        self.faces_dict.update({'A': 0, 't': 9, 'J': 10, 'Q': 11, 'K': 12})
        self.suits_dict = {'H': 0, 'D': 1, 'S': 2, 'C': 3}

        self.cards = cards
        self.hand_type, self.hand, self.sorted_cards = self.get_hand(cards)

    def get_card_face(self, card):
        return self.faces_dict[card[0]]

    def get_card_suit(self, card):
        return self.suits_dict[card[1]]

    def get_straight_high(self, faces):
        straight_high_max = -1
        # accounting for ace high
        if 0 in faces:
            faces.append(13)
        for shift in range(13):
            faces_shifted = [f-shift for f in faces]
            if set([0,1,2,3,4]) <= set(faces_shifted):
                straight_high = 4+shift
                if straight_high > straight_high_max:
                    straight_high_max = straight_high
        return straight_high_max

    def get_hand(self, cards):
        faces = [self.get_card_face(card) for card in cards]
        suits = [self.get_card_suit(card) for card in cards]
        faces_sorted = sorted(([13] * (np.array(faces) == 0).sum()) + [face for face in faces if face != 0], reverse=True)
        
        faces_counts = Counter(faces)
        suits_counts = Counter(suits)

        # straight flush
        if 5 in suits_counts.values() and (straight_high := self.get_straight_high(faces)) > 0:
            hand = [[card for card, face in zip(cards, faces) if face == (straight_high-i)%13][0] for i in range(5)]
            # royal flush
            if straight_high == 13:
                return 9, {'hand': hand}, faces_sorted
            else:
                return 8, {'hand': hand, 'straight high': straight_high}, faces_sorted
        # four of a kind
        if 4 in faces_counts.values():
            face = [face for face, count in faces_counts.items() if count == 4][0]
            hand = [card for card, f in zip(cards, faces) if f == face]
            return 7, {'hand': hand, 'face': face}, faces_sorted
        # full house
        if set([3, 2]) <= set(faces_counts.values()):
            set_face = [face for face, count in faces_counts.items() if count == 3][0]
            pair_face = max([face for face, count in faces_counts.items() if count == 2])
            hand = [card for card, f in zip(cards, faces) if (f == set_face) or (f == pair_face)]
            return 6, {'hand': hand, 'set face': 13 if set_face == 0 else set_face, 'pair face': pair_face}, faces_sorted
        # flush
        if 5 in suits_counts.values():
            suit = [suit for suit, count in suits_counts.items() if count == 5][0]
            flush_faces = [face for face, s in zip(faces, suits) if s == suit]
            hand = [card for card, s in zip(cards, suits) if s == suit]
            return 5, {'hand': hand, 'flush high': max(flush_faces)}, faces_sorted
        # straight
        if (straight_high := self.get_straight_high(faces)) > 0:
            hand = [[card for card, face in zip(cards, faces) if face == (straight_high-i)%13][0] for i in range(5)]
            return 4, {'hand': hand, 'straight high': straight_high}, faces_sorted
        # three of a kind
        if 3 in faces_counts.values():
            face = [face for face, count in faces_counts.items() if count == 3][0]
            hand = [card for card, f in zip(cards, faces) if f == face]
            return 3, {'hand': hand, 'face': 13 if face == 0 else face}, faces_sorted
        # two pair
        if (np.array(list(faces_counts.values())) == 2).sum() == 2:
            pair_faces = [face for face, count in faces_counts.items() if count == 2]
            pair_faces = [13 if face == 0 else face for face in pair_faces]
            hand = [card for card, f in zip(cards, faces) if f in faces]
            return 2, {'hand': hand, 'high face': max(pair_faces), 'low face': min(pair_faces)}, faces_sorted
        # one pair
        if 2 in faces_counts.values():
            face = [face for face, count in faces_counts.items() if count == 2][0]
            hand = [card for card, f in zip(cards, faces) if f == face]
            return 1, {'hand': hand, 'face': 13 if face == 0 else face}, faces_sorted
        # high card
        return 0, None, faces_sorted

def abstract_hand_key(hand_key: str):
    hand = hand_key.split('-')
    suits = [card[1] for card in hand]
    suit_key = {}
    abstract_suits = ['A', 'B', 'C', 'D']
    for suit in suits:
        if suit not in suit_key.keys():
            suit_key.update({suit: abstract_suits.pop(0)})
    for suit in suits:
        hand_key = hand_key.replace(suit, suit_key[suit])
    return hand_key

from copy import deepcopy
class HandState:
    def __init__(self, names, actor, playing, active, bets, pot, shares, betting_round, move: Move):
        self.playing = {name: is_playing for name, is_playing in zip(names, playing)}
        self.active = {name: is_active for name, is_active in zip(names, active)}
        self.bets = {name: bet for name, bet in zip(names, bets)}
        self.pot = pot
        self.shares = {name: share for name, share in zip(names, shares)}
        self.betting_round = betting_round
        self.seat = None
        self.actor = actor
        self.move = move
        self.move.actor = actor

    def add_player_info(self, name, seat) -> None:
        c = deepcopy(self)
        for dic in [c.playing, c.active, c.bets, c.shares]:
            dic["me"] = dic.pop(name)
        c.seat = seat
        return c

import argparse
def parse_argv():
    parser = argparse.ArgumentParser(prog = 'nwave')

    players = parser.add_argument_group("players")
    game_config = parser.add_argument_group("game")
    debug = parser.add_argument_group("debug")

    players.add_argument("--fpath", type=str, nargs='?', default='.')

    game_config.add_argument("--buy_in", type=int, nargs='?', default=200)
    game_config.add_argument("--little_blind", type=int, nargs='?', default=1)
    game_config.add_argument("--big_blind", type=int, nargs='?', default=2)
    game_config.add_argument("--hands", type=int, nargs='?', default=100)

    debug.add_argument("--verbose", action="store_true")
    debug.add_argument("--outfile", type=str, default=None)

    args = parser.parse_args()
    return args

import sys
def load_player_from_path(dir, name, buy_in):
    """
    from https://appdividend.com/2021/03/31/how-to-import-class-from-another-file-in-python/
    """
    sys.path.append(dir)
    exec("from {} import MyPlayer".format(name.removesuffix(".py")))
    return MyPlayer(buy_in)


import contextlib
@contextlib.contextmanager
def smart_open(filename=None):
    """
    from https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely
    """
    if filename and filename != '-':
        fh = open(filename, 'w')
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()

# timeout code is from https://stackoverflow.com/questions/2281850/timeout-function-if-it-takes-too-long-to-finish
import errno
import os
import signal
import functools

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator