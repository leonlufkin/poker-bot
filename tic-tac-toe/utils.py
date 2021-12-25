import numpy as np

class GameState:
    def __init__(self, board, num_players, turns_played):
        self.board = board
        self.num_players = num_players
        self.turns_played = turns_played

class Config:
    def __init__(self, width):
        self.width = width
        self.num_players = 0
        self.players = []
        self.names = []

    def register_player(self, name, algo):
        self.names.append(name)
        algo.assign_my_number(self.num_players)
        self.players.append(algo)
        self.num_players += 1
    
    def get_players(self):
        return self.players

class TicTacToe:
    def __init__(self, width, num_players):
        self.width = width
        self.board = -np.ones((width, width))
        self.num_players = num_players
        self.moves_played = 0

    def validate_move(self, move, player):
        if not isinstance(move, tuple):
            raise TypeError("Player {}: move {} is not a tuple".format(player, move))
        elif len(move) != 2:
            raise ValueError("Player {}: move tuple is not 2-dimensions".format(player))
        elif not ((0 <= move[0] < self.width) and (0 <= move[1] < self.width)):
            raise ValueError("Player {}: move tuple is out of bounds".format(player))
        elif self.board[move] >= 0:
            raise ValueError("Player {}: invalid move, square is already filled".format(player))

    def add_move(self, move, player):
        self.validate_move(move, player)
        self.board[move] = player
        self.moves_played += 1
    
    def has_tictactoe(self, player):
        player_board = self.board == player
        # checking rows & columns
        for i in range(self.width):
            if player_board[i,:].sum() == self.width:
                return True
            if player_board[:,i].sum() == self.width:
                return True
        # checking diagonals
        if player_board.diagonal().sum() == self.width:
            return True
        if np.fliplr(player_board).diagonal().all():
            return True
        return False

    def is_game_over(self, player):
        # are all squares filled?
        if (self.board >= 0).all():
            return True
        # are enough squares filled?
        elif (self.board >= 0).sum() < self.width:
            return False
        return self.has_tictactoe(player)

    def get_game_state(self):
        return GameState(self.board, self.num_players, self.moves_played // 2)