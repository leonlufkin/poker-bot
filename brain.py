from abc import ABC, abstractmethod
import numpy as np

class GameState:
    """
    class for storing game state information that is accessible to all players (information they can use to make decisions)
    """
    def __init__(self, seats, little_blind, big_blind):
        self.LB = little_blind
        self.BB = big_blind
        self.num_players = seats
        self.current_dealer = 0

        self.chip_counts = np.zeros(self.num_players)
        self.active_players = np.arange(self.num_players)

    def count_players(self):
        return

    def rotate_dealer(self):
        self.num_players = self.count_players()
        self.current_dealer = (self.current_dealer+1) % self.num_players

class Player(ABC):
    def __init__(self, number_chips):
        self.chip_count = number_chips

    @abstractmethod
    def move(self, game_state):
        """given game_state, returns a move: fold, call, or raise"""
        pass
