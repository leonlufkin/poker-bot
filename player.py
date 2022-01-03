import numpy as np
from abc import ABC, abstractmethod
from utils import HandState, Move, Hand

class Player(ABC):
    def __init__(self, number_chips):
        self.chip_stack = number_chips
        self.__hole_cards = ['..', '..']
        self.community_cards = []

    def update_stack(self, amount):
        if -amount > self.chip_stack:
            raise ValueError("cannot remove {:.2f} chips, only have {:.2f}".format(-amount, self.chip_stack))
        self.chip_stack += amount

    def get_chip_stack(self):
        return self.chip_stack

    def get_hole_cards(self, hole_cards):
        self.__hole_cards = hole_cards

    def get_community_cards(self, community_cards):
        self.community_cards = community_cards

    @abstractmethod
    def update_hand_state(self, hand_state: HandState) -> None:
        pass

    @abstractmethod
    def make_move(self, seat: int, playing: np.ndarray, bets: np.ndarray, pot: float, shares: np.ndarray, betting_round: int) -> Move:
        """given game state, returns a move: fold, call, or raise"""
        pass

class Caller(Player):
    def update_hand_state(self, hand_state: HandState) -> None:
        pass 

    def make_move(self, seat: int, playing: np.ndarray, bets: np.ndarray, pot: float, shares: np.ndarray, betting_round: int) -> Move:
        my_last_bet = bets[seat]
        calling_bet = bets.max()
        # not enough chips to call -> fold
        if calling_bet > self.chip_stack:
            return Move("fold")
        elif my_last_bet == calling_bet:
            return Move("check")
        else:
            return Move("call")

class SmallRaiser(Player):
    def update_hand_state(self, hand_state: HandState) -> None:
        pass 

    def make_move(self, seat: int, playing: np.ndarray, bets: np.ndarray, pot: float, shares: np.ndarray, betting_round: int) -> Move:
        my_last_bet = bets[seat]
        calling_bet = bets.max()
        my_new_bet = 0.5 * calling_bet + 1
        # not enough chips to call -> fold
        if calling_bet > self.chip_stack:
            return Move("fold")
        elif my_last_bet == calling_bet and my_new_bet <= self.chip_stack:
            return Move("raise", amount=my_new_bet)
        elif calling_bet > my_last_bet and calling_bet <= self.chip_stack:
            return Move("call")
        else:
            return Move("check")