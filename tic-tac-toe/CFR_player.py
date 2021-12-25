from demo_players import Player
import numpy as np

class Subgame:
    def __init__(self, board, num_players, my_number, node_prob, node_player, node_move=None) -> None:
        self.board = board
        self.width = board.shape[0]
        self.num_players = num_players
        self.my_number = my_number
        self.node_prob = node_prob
        self.node_player = node_player
        self.node_move = node_move

        self.children = self.spawn_children()
        self.payoff = self.calculate_payoff()

    def add_move_to_board(self, move, player):
        board = self.board.copy()
        board[move] = player
        return board

    def generate_node_moves(self):
        """given the current board state, returns a list of Subgames for each possible move the given player could make"""
        rows, cols = (self.board < 0).nonzero()
        moves = [(row,col) for row,col in zip(rows,cols)]
        next_player = (self.node_player + 1) % self.num_players
        boards = [self.add_move_to_board(move=move, player=next_player) for move in moves]
        return [Subgame(board, self.num_players, self.my_number, 1, next_player, node_move=move) for board, move in zip(boards, moves)]

    def has_tictactoe(self):
        player_board = self.board == self.node_player
        # checking rows & columns
        for i in range(self.width):
            if player_board[i,:].all():
                return True
            if player_board[:,i].all():
                return True
        # checking diagonals
        if player_board.diagonal().all():
            return True
        if np.fliplr(player_board).diagonal().all():
            return True
        return False

    def is_terminal_node(self):
        # are enough squares filled?
        if (self.board >= 0).sum() < self.width:
            return False
        # are all squares filled?
        elif (self.board >= 0).all():
            return True
        return self.has_tictactoe()

    def calculate_terminal_payoff(self):
        """
        if game terminates after player's action, then either player has tic-tac-toe or board is full:
        - if player has tic-tac-toe, then node_player_won = 1, and the payoff is 1 if node_player == my_number and -1 otherwise
        - if player does not have tic-tac-toe, then board is full; since the board is full and there is no tic-tac-toe, it is a tie and payoff is 0
        """
        node_player_won = self.has_tictactoe()
        payoff = (2 * (self.node_player == self.my_number) - 1) * node_player_won
        return payoff

    def spawn_children(self):
        if self.is_terminal_node():
            self.payoff = self.calculate_terminal_payoff()
            return []
        return self.generate_node_moves()

    def calculate_payoff(self):
        """
        calculates payoff based on two types of nodes:
        1. we have complete control
        2. opponent has complete control
        (3. chance node - not relevant in this case, but is for poker!)
        """
        if len(self.children) == 0:
            return self.payoff

        # we are playing this node, so can always choose best option
        if self.children[0].node_player == self.my_number:
            payoff = max([child.payoff for child in self.children])
        # opponent is playing this node, so we assume the worst option is chosen
        else:
            payoff = min([child.payoff for child in self.children])
            # sum([child.payoff * child.node_prob for child in self.children]) / sum([child.node_prob for child in self.children])
        return payoff

    def get_best_move(self):
        best_move = None
        best_payoff = -2
        for child in self.children:
            if child.payoff > best_payoff:
                best_payoff = child.payoff
                best_move = child.node_move
        return best_move

    def display_board(self):
        print("Board ({:.3f}) - Player {}".format(self.payoff, self.node_player))
        print(self.board)
    
    def display_children(self):
        for child in self.children:
            child.display_board()

class CFRPlayer(Player):
    def __init__(self) -> None:
        super().__init__()

    def get_move(self, game_state):
        if game_state.turns_played == 0:
            valid_moves = self.get_valid_moves(game_state)
            return (1, 1) if (1, 1) in valid_moves else (0, 0)

        num_players = game_state.num_players
        prev_player = (self.my_number - 1) % num_players
        subgame = Subgame(game_state.board, num_players, self.my_number, 1, prev_player)
        return subgame.get_best_move()
