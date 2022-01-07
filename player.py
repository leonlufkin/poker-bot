import numpy as np
from abc import ABC, abstractmethod
from utils import HandState, Move, Hand

class Player(ABC):
    def __init__(self, number_chips):
        self.chip_stack = number_chips
        self.hole_cards = ['..', '..']
        self.community_cards = []
        self.wins = 0
        self.hands = 0

    def update_stack(self, amount):
        if -amount > self.chip_stack:
            raise ValueError("cannot remove {:.2f} chips, only have {:.2f}".format(-amount, self.chip_stack))
        self.chip_stack += amount

    def get_chip_stack(self):
        return self.chip_stack

    def get_hole_cards(self, hole_cards):
        self.hole_cards = hole_cards

    def get_community_cards(self, community_cards):
        self.community_cards = community_cards

    @abstractmethod
    def update_hand_state(self, hand_state: HandState) -> None:
        pass

    @abstractmethod
    def make_move(self) -> Move:
        """given game state, returns a move: fold, call, or raise"""
        pass

    def round_end(self, player_hands, player_hand_ranks):
        self.hands += 1
        if player_hand_ranks["me"] == max(player_hand_ranks.values()):
            self.wins += 1

        # resetting hand
        self.hole_cards = ['..', '..']
        self.community_cards = []


class BasicPlayer(Player):
    def update_hand_state(self, hand_state: HandState) -> None:
        self.seat = hand_state.seat
        self.playing = hand_state.playing
        self.active = hand_state.active
        self.bets = hand_state.bets
        self.pot = hand_state.pot
        self.shares = hand_state.shares
        self.betting_round = hand_state.betting_round

class Caller(BasicPlayer):
    def make_move(self) -> Move:
        my_last_bet = self.bets["me"]
        calling_bet = max(self.bets.values())
        # not enough chips to call -> fold
        if calling_bet > self.chip_stack:
            return Move("fold")
        elif my_last_bet == calling_bet:
            return Move("check")
        else:
            return Move("call")

class SimpleRaiser(BasicPlayer):
    def make_move_given_raise_size(self, raise_size) -> None:
        my_last_bet = self.bets["me"]
        calling_bet = max(self.bets.values())
        my_new_bet = raise_size * calling_bet + 1
        # not enough chips to call -> fold
        if calling_bet > self.chip_stack:
            return Move("fold")
        elif my_last_bet == calling_bet and my_new_bet <= self.chip_stack:
            return Move("raise", amount=my_new_bet)
        elif calling_bet > my_last_bet and calling_bet <= self.chip_stack:
            return Move("call")
        else:
            return Move("check")

    def make_move(self) -> Move:
        return self.make_move_given_raise_size(2)

class Ryan(SimpleRaiser):
    def make_move(self) -> Move:
        return self.make_move_given_raise_size(0)

class Bill(SimpleRaiser):
    def get_hole_cards(self, hole_cards) -> None:
        super().get_hole_cards(hole_cards)
        if any([set(hole_cards) == set(pair) for pair in [['QH', 'QD'], ['QH', 'QS'], ['QH', 'QC'], ['QD', 'QS'], ['QD', 'QC'], ['QS', 'QC']]]):
            self.yesssss = True
        else:
            self.yesssss = False
    
    def make_move(self) -> Move:
        if self.yesssss:
            return Move("raise", amount=self.chip_stack)
        else:
            return Move("fold")

class HandTracker(Caller):
    def __init__(self, number_chips):
        super().__init__(number_chips)
        self.preflop_hands = {}
        self.flop_hands = {}
        self.preflop_hand_key = None
        self.flop_hand_key = None

    def add_preflop_hand(self, hole_cards):
        self.preflop_hand_key = '-'.join(sorted(hole_cards))
        if self.preflop_hand_key in self.preflop_hands.keys():
            self.preflop_hands[self.preflop_hand_key] += np.array([0.0,1])
        else:
            self.preflop_hands[self.preflop_hand_key] = np.array([0.0,1])

    def add_flop_hand(self, hand):
        self.flop_hand_key = '-'.join(sorted(hand))
        if self.flop_hand_key in self.flop_hands.keys():
            self.flop_hands[self.flop_hand_key] += np.array([0.0,1])
        else:
            self.flop_hands[self.flop_hand_key] = np.array([0.0,1])

    def get_hole_cards(self, hole_cards):
        super().get_hole_cards(hole_cards)
        self.add_preflop_hand(hole_cards)

    def get_community_cards(self, community_cards):
        super().get_community_cards(community_cards)
        # exactly after flop
        if len(self.community_cards) == 3:
            self.add_flop_hand(self.hole_cards + self.community_cards)

    def round_end(self, player_hands, player_hand_ranks):
        super().round_end(player_hands, player_hand_ranks)
        if player_hand_ranks["me"] == max(player_hand_ranks.values()):
            if sum(list(player_hand_ranks.values()) == max(player_hand_ranks.values())) > 1:
                self.preflop_hands[self.preflop_hand_key] += np.array([0.5,0])
                self.flop_hands[self.flop_hand_key] += np.array([0.5,0])
            else:
                self.preflop_hands[self.preflop_hand_key] += np.array([1.0,0])
                self.flop_hands[self.flop_hand_key] += np.array([1.0,0])
        else:
            winners = [player for rank, player in player_hand_ranks.items() if rank == max(player_hand_ranks.values())]
            # one winner
            if len(winners) == 1:
                if player_hands[winners[0]] is not None:
                    self.add_preflop_hand(player_hands[winners[0]])
                    self.preflop_hands[self.preflop_hand_key] += np.array([1.0,0])
                    self.add_flop_hand(player_hands[winners[0]])
                    self.flop_hands[self.flop_hand_key] += np.array([1.0,0])
            # tie among opponents
            else:
                for winner in winners:
                    self.add_preflop_hand(player_hands[winner])
                    self.preflop_hands[self.preflop_hand_key] += np.array([0.5,0])
                    self.add_flop_hand(player_hands[winner])
                    self.flop_hands[self.flop_hand_key] += np.array([0.5,0])

from CFR import Node, CFR_Tree

class CFR(Player):
    def __init__(self, chip_stack, CFR_tree: CFR_Tree) -> None:
        super().__init__(chip_stack)
        self.node = Node()
        
    def get_hole_cards(self, hole_cards):
        super().get_hole_cards(hole_cards)
        self.game_tree[abstract_hand_key('-'.join(hole_cards))]

    def traverse_game_tree(self, player, action):
        self.node = self.node.traverse_game_tree(player, action)

    def update_hand_state(self, hand_state: HandState) -> None:
        pass

    def make_move(self):
        # pre-flop
        if len(self.community_cards) == 0:
            self.game_tree[""]
