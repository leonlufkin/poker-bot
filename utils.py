import numpy as np
from collections import Counter

def rotate_list(l, n):
    return l[-n:] + l[:-n]

class Move:
    def __init__(self, move, amount=0):
        self.validate_move(move, amount)
        self.move = move
        self.amount = amount
    
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

class HandState:
    def __init__(self, active, bets, pot, shares, betting_round):
        self.active = active
        self.bets = bets
        self.pot = pot
        self.shares = shares
        self.betting_round = betting_round
        self.seat = None

    def add_player_seat(self, seat):
        self.seat = seat
        return self