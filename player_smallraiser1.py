import numpy as np
from player import Player
from utils import HandState, Move

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