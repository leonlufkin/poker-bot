from abc import ABC, abstractmethod
from utils import GameState
import numpy as np

class Player(ABC):
    def __init__(self) -> None:
        self.my_number = 0

    def assign_my_number(self, my_number):
        self.my_number = my_number

    def get_valid_moves(self, game_state):
        rows, cols = (game_state.board < 0).nonzero()
        valid_moves = [(rows[i], cols[i]) for i in range(len(rows))]
        return valid_moves

    @abstractmethod
    def get_move(self, game_state: GameState) -> tuple:
        pass

class BasicPlayer(Player):
    def __init__(self) -> None:
        super().__init__()
        self.num_moves = 0

    def test_information(self):
        self.num_moves += 1
        if self.num_moves % 500 == 0:
            print("BasicPlayer has made {} moves since first game!".format(self.num_moves))

    def get_move(self, game_state: GameState):
        # self.test_information()
        valid_moves = self.get_valid_moves(game_state)
        return valid_moves[0]

class RandomPlayer(Player):
    def get_move(self, game_state: GameState):
        valid_moves = self.get_valid_moves(game_state)
        return valid_moves[np.random.choice(len(valid_moves))]