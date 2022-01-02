from abc import ABC, abstractmethod
import numpy as np
from utils import rotate_list
from collections import Counter

class OldHand:
    """
    class for storing information about current hand, this info is accessible to all players (information 
    they can use to make decisions)
    """
    def __init__(self, num_players, dealer_seat, little_blind, big_blind):
        self.num_players = num_players
        self.dealer_seat = dealer_seat
        self.LB_seat = (dealer_seat + 1) % num_players
        self.BB_seat = (dealer_seat + 2) % num_players

        self.LB = little_blind
        self.BB = big_blind

        self.chip_counts = np.zeros(self.num_players)
        self.active_players = np.ones(self.num_players, dtype=bool)
        self.community_cards = []

        self.bets = np.zeros(self.num_players)
        self.bet_blinds()
        self.pot = 0


    def fold_player(self, player):
        self.active_players[player] = False
        self.num_players -= 1


    def add_community_cards(self, cards):
        self.community_cards += cards
    

    def bet_blinds(self):
        self.bets[self.LB_seat] = self.LB
        self.bets[self.BB_seat] = self.BB

    def add_bet(self, player, bet):
        self.bets[player] = bet

    def reset_bets(self):
        self.bets = np.zeros(self.num_players)

    def combine_pot(self):
        self.pot += self.bets.sum()
        self.reset_bets()


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

class Hand:
    def __init__(self, cards):
        self.faces = {str(num+1): num for num in range(9)}
        self.faces.update({'A': 0, 't': 9, 'J': 10, 'Q': 11, 'K': 12})
        self.suits = {'H': 0, 'D': 1, 'S': 2, 'C': 3}

        self.cards = cards
        self.hand_type, self.hand, self.sorted_cards = self.get_hand(cards)

    def get_card_face(self, card):
        return self.faces[card[0]]

    def get_card_suit(self, card):
        return self.suits[card[1]]

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
        if set([3,2]) <= set(faces_counts.values()):
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
            return 3, {'hand': hand, 'face': face}, faces_sorted
        # two pair
        if (np.array(list(faces_counts.values())) == 2).sum() == 2:
            pair_faces = [face for face, count in faces_counts.items() if count == 2]
            hand = [card for card, f in zip(cards, faces) if f in faces]
            return 2, {'hand': hand, 'high face': max(pair_faces), 'low face': min(pair_faces)}, faces_sorted
        # one pair
        if 2 in faces_counts.values():
            face = [face for face, count in faces_counts.items() if count == 2][0]
            hand = [card for card, f in zip(cards, faces) if f == face]
            return 1, {'hand': hand, 'face': face}, faces_sorted
        # high card
        return 0, None, faces_sorted


class Dealer:
    def __init__(self, num_players):
        self.num_players = num_players
        self.hole_cards = np.array(['..', '..'] * num_players, dtype=object)
        self.community_cards = []
        self.available_cards = np.arange(52)

        self.faces = {num : str(num+1) for num in range(1,9)}
        self.faces.update({0: 'A', 9: 't', 10: 'J', 11: 'Q', 12: 'K'})
        self.suits = {0 : 'H', 1: 'D', 2: 'S', 3: 'C'}

    def display_card(self, card):
        face = card % 13
        suit = card // 13
        name = self.faces[face] + self.suits[suit]
        return name

    def draw_cards(self, num_cards):
        cards = np.random.choice(self.available_cards, size=num_cards, replace=False)
        for card in cards:
            self.available_cards = self.available_cards[self.available_cards != card]
        return [self.display_card(card) for card in cards]

    def deal_hole_cards(self):
        for player in range(self.num_players):
            self.hole_cards[player] = self.draw_cards(2)
        return self.hole_cards

    def deal_community_cards(self, num_cards):
        cards = self.draw_cards(num_cards)
        self.community_cards += cards
        return cards

    def determine_hand_ranks(self, active):
        hands = []
        for player in range(self.num_players):
            if not active[player]:
                continue
            hands.append(Hand(self.hole_cards[player] + self.community_cards))
        hand_types = np.array([hand.hand_type for hand in hands])
        hand_ranks = np.array([(hand_type > hand_types).sum() for hand_type in hand_types])

        for hand_type in np.unique(hand_types):
            if (hand_type_mask := (hand_type == hand_types)).sum() > 1:
                # straight (flush)
                if hand_type == 8 or hand_type == 4:
                    straight_highs = np.array([hand.hand['straight high'] for hand, type in zip(hands, hand_types) if type == hand_type])
                    hand_ranks[hand_type_mask] += np.array([(high > straight_highs).sum() for high in straight_highs])
                # four of a kind, three of a kind, one pair
                elif hand_type == 7 or hand_type == 3 or hand_type == 1:
                    faces = np.array([hand.hand['face'] for hand, type in zip(hands, hand_types) if type == hand_type])
                    hand_ranks[hand_type_mask] += np.array([(face > faces).sum() for face in faces])
                # full house
                elif hand_type == 6:
                    set_faces = np.array([hand.hand['set face'] for hand, type in zip(hands, hand_types) if type == hand_type])
                    pair_faces = np.array([hand.hand['pair face'] for hand, type in zip(hands, hand_types) if type == hand_type])
                    hand_ranks[hand_type_mask] += np.array([(set_face > set_faces).sum() + (pair_face > pair_faces[set_faces == set_face]).sum() for set_face, pair_face in zip(set_faces, pair_faces)])
                # flush
                elif hand_type == 5:
                    flush_highs = np.array([hand.hand['flush high'] for hand, type in zip(hands, hand_types) if type == hand_type])
                    hand_ranks[hand_type_mask] += np.array([(high > flush_highs).sum() for high in flush_highs])
                # two pair
                elif hand_type == 2:
                    high_faces = np.array([hand.hand['high face'] for hand, type in zip(hands, hand_types) if type == hand_type])
                    low_faces = np.array([hand.hand['low face'] for hand, type in zip(hands, hand_types) if type == hand_type])
                    hand_ranks[hand_type_mask] += np.array([(high_face > high_faces).sum() + (low_face > low_faces[high_faces == high_face]).sum() for high_face, low_face in zip(high_faces, low_faces)])
                # high card
                else:
                    best_five_cards = [np.array([hand.sorted_cards[card] for hand, type in zip(hands, hand_types) if type == hand_type]) for card in range(5)] # getting top 5 cards
                    hand_numbers = np.apply_along_axis(lambda x: int('' .join(x)), 0, np.array([(cards == cards.max()).astype(int).astype(str) for cards in best_five_cards]))
                    hand_ranks[hand_type_mask] += np.array([(hand_number > hand_numbers).sum() for hand_number in hand_numbers])

        final_ranks = np.zeros(len(active))
        final_ranks[active] = hand_ranks + 1
        return final_ranks, hand_types


class Table:
    def __init__(self) -> None:
        self.num_players = 0
        self.__players = []
        self.names = []
        self.chip_stacks = np.zeros(self.num_players)
        self.init_hand()

    def register_player(self, name, algo):
        if name in self.names:
            raise ValueError("player with name {} already exists, please pick a new name".format(name))
        self.names.append(name)
        self.__players.append(algo)
        self.chip_stacks = self.chip_stacks.append(0)
        self.num_players += 1

    def remove_player(self, name):
        player_num = [num for num, nom in enumerate(self.names) if nom == name]
        if len(player_num) == 0:
            raise ValueError("failed to remove player, no such player with name {}".format(name))
        self.names.pop(player_num[0])
        self.__players.pop(player_num[0])
        self.chip_stacks = np.delete(self.chip_stacks, player_num[0])
        self.num_players -= 1

    def issue_hole_cards(self, hole_cards):
        for player in range(self.num_players):
            self.__players[player].get_hole_cards(hole_cards[player])

    def share_community_cards(self, community_cards):
        for player in range(self.num_players):
            self.__players[player].get_community_cards(community_cards)

    def reset_bets(self):
        self.bets = np.zeros(self.num_players)

    def init_hand(self):
        self.shares = np.zeros(self.num_players)
        self.active = np.ones(self.num_players, dtype=bool)
        self.reset_bets()
        self.pot = 0

    def play_hand(self, LB, BB):
        # init
        dealer = Dealer(self.num_players)
        self.init_hand()
        community_cards = []

        # deal hole cards
        hole_cards = dealer.deal_hole_cards()
        self.issue_hole_cards(hole_cards)
        self.bet_blinds(LB, BB)
        self.round_of_betting(start=2)

        # flop
        community_cards += dealer.deal_community_cards(3)
        self.share_community_cards(community_cards)
        self.round_of_betting()

        # turn card
        community_cards += dealer.deal_community_cards(1)
        self.round_of_betting()

        # river card
        dealer.deal_community_cards(1)
        self.round_of_betting()

        # showdown + distribute pot
        self.showdown()
        
        # setup for next game
        self.move_blinds()

    def bet_blinds(self, LB, BB):
        self.__players[0].update_stack(-LB)
        self.bets[0] = LB
        self.__players[1].update_stack(-BB)
        self.bets[1] = BB
        self.pot = LB + BB

    def update_stack(self, player, amount):
        self.chip_stacks += amount
        self.__players[player].update_stack(amount)

    def get_hand_state(self, betting_round):
        hand_state = HandState(self.active, self.bets, self.pot, self.shares, betting_round)
        return hand_state

    def round_of_betting(self, start=0):
        if self.active.sum() < 2:
            pass

        max_bet = -1
        betting_round = 0

        while not (self.bets[self.active] == max_bet).all():
            for i in range(self.num_players):
                if not self.active[i]:
                    continue

                # updating each player on current state of hand
                hand_state = self.get_hand_state(betting_round)
                for j in range(self.num_players):
                    self.__players[j].update_hand_state(hand_state.add_player_seat((j+start) % self.num_players))

                # proceeding with betting
                seat = (i+start) % self.num_players
                move = self.__players[seat].make_move(seat, self.active, self.bets, self.pot, self.shares, betting_round)
                max_bet = self.bets.max()

                if move.move == "fold":
                    self.active[i] = False
                    self.shares[i] = 0
                elif move.move == "call":
                    call_amount = max_bet-self.bets[i]
                    if call_amount >= self.chip_stacks[i]:
                        print("Player {} is all in!".format(self.names[i]))
                        self.shares[i] = self.bets[i] = self.chip_stacks[i] + self.bets[i]
                        self.update_stack(i, -self.chip_stacks[i])
                        self.active[i] = False
                    else:
                        self.shares[i] = max_bet
                        self.update_stack(i, -call_amount)
                        self.bets[i] = max_bet
                elif move.move == "check":
                    if self.bets[i] < max_bet:
                        raise ValueError("Player {} attempted to check when they needed to bet {} more to match {}".format(self.names[i], max_bet-self.bets[i], max_bet))
                else:
                    if move.amount > self.chip_stacks[i]:
                        raise ValueError("Player {} attempted to bet {} when they only have {}!".format(self.names[i], move.amount, self.chip_stacks[i]))
                    elif move.amount + self.bets[i] <= max_bet:
                        raise ValueError("Player {} attempted to raise {} when they must raise at least {} to not call, check, or fold".format(self.names[i], move.amount, max_bet-self.bets[i]+1))
                    elif move.amount == self.chip_stacks[i]:
                        print("Player {} is all in!".format(self.names[i]))
                        self.shares[i] = self.bets[i] = self.chip_stacks[i] + self.bets[i]
                        self.update_stack(i, -self.chip_stacks[i])
                        self.active[i] = False
                    else:
                        self.update_stack(i, -move.amount)
                        self.bets[i] += move.amount
                        self.shares[i] = self.bets[i]
            betting_round += 1
            max_bet = self.bets.max()
        self.pot += self.bets.sum()
        self.reset_bets()

    def showdown(self):
        # one player left, gets whole pot
        if self.active.sum() == 1:
            self.update_stack(np.where(self.active)[0][0], self.pot)

        

        



    def move_blinds(self):
        self.__players = rotate_list(self.__players)
        self.names = rotate_list(self.names)


class Poker:
    def __init__(self, table: Table, little_blind, big_blind) -> None:
        self.num_players = table.num_players
        self.table = table
        self.little_blind = little_blind
        self.big_blind = big_blind
        self.chip_counts = np.zeros(self.num_players)

    

    def validate_move(self, move, player):
        player_stack = self.chip_counts[player]

    def add_move(self, move, player):
        self.players

    def add_chips(self, player, amount):
        self.chip_counts[player] = self.chip_counts[player] + amount

    def add_chips_all(self, amount):
        self.chip_counts += amount

    def update_blinds(self, little_blind, big_blind):
        self.little_blind = little_blind
        self.big_blind = big_blind

class Player(ABC):
    def __init__(self, number_chips):
        self.chip_count = number_chips

    @abstractmethod
    def move(self, game_state):
        """given game_state, returns a move: fold, call, or raise"""
        pass
