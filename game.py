from abc import ABC, abstractmethod
import numpy as np

class Hand:
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
        if move not in ["fold", "call", "raise"]:
            return ValueError("invalid move type {}, must be one of 'fold', 'call', or 'raise'".format(move))
        if move == "raise":
            if amount <= 0:
                return ValueError("cannot raise {}, must be strictly positive amount".format(amount))


class Table:
    def __init__(self) -> None:
        self.num_players = 0
        self.players = []
        self.names = []

    def register_player(self, name, algo):
        if name in self.names:
            raise ValueError("player with name {} already exists, please pick a new name".format(name))
        self.names.append(name)
        self.players.append(algo)
        self.num_players += 1

    def remove_player(self, name):
        player_num = [num for num, nom in enumerate(self.names) if nom == name]
        if len(player_num) == 0:
            raise ValueError("failed to remove player, no such player with name {}".format(name))
        self.names.pop(player_num[0])
        self.players.pop(player_num[0])
        self.num_players -= 1

    def get_players(self):
        return self.players


class Dealer:
    def __init__(self, num_players):
        self.num_players = num_players
        self.hole_cards = np.array(['..','..'] * num_players, dtype=object)
        self.community_cards = []
        self.available_cards = np.arange(52)

        self.faces = {num : str(num+1) for num in range(1,8)}
        self.faces.update({0: 'A', 9: 't', 10: 'J', 11: 'Q', 11: 'K'})
        self.suits = {0 : 'H', 1: 'D', 2: 'S', 3: 'C'}

    def display_card(self, card):
        face = card % 13
        suit = card // 4
        name = self.faces[face] + self.suits[suit]
        return name

    def draw_cards(self, num_cards):
        cards = np.random.choice(self.available_cards, size=num_cards)
        self.available_cards = self.available_cards.delete(cards)
        return [self.display_card(card) for card in cards.tolist()]

    def deal_hole_cards(self):
        for player in range(self.num_players):
            self.hole_cards[player] = self.draw_cards(2)

    def deal_community_cards(self, num_cards):
        self.community_cards += self.draw_cards(num_cards)

    def get_community_cards(self):
        return self.community_cards


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
