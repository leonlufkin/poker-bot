from abc import ABC, abstractmethod
import numpy as np
from utils import rotate_list

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


class Dealer:
    def __init__(self, num_players):
        self.num_players = num_players
        self.hole_cards = np.array(['..', '..'] * num_players, dtype=object)
        self.community_cards = []
        self.available_cards = np.arange(52)

        self.faces = {num : str(num+1) for num in range(1,8)}
        self.faces.update({0: 'A', 9: 't', 10: 'J', 11: 'Q', 12: 'K'})
        self.suits = {0 : 'H', 1: 'D', 2: 'S', 3: 'C'}

    def display_card(self, card):
        face = card % 13
        suit = card // 4
        name = self.faces[face] + self.suits[suit]
        return name

    def draw_cards(self, num_cards):
        cards = np.random.choice(self.available_cards, size=num_cards)
        self.available_cards = self.available_cards.delete(cards)
        return [self.display_card(card) for card in cards]

    def deal_hole_cards(self):
        for player in range(self.num_players):
            self.hole_cards[player] = self.draw_cards(2)
        return self.hole_cards

    def deal_community_cards(self, num_cards):
        cards = self.draw_cards(num_cards)
        self.community_cards += cards
        return cards

    def get_hand_type(self, hand):
        if self.is_straight_flush(hand):
            return 8 # "straight flush"
        if self.is_four_kind(hand):
            return 7 # "four of a kind"
        if self.is_full_house(hand):
            return 6 # "full house"
        if self.is_flush(hand):
            return 5 # "flush"
        if self.is_straight(hand):
            return 4 # "straight"
        if self.is_three_kind(hand):
            return 3 # "three of a kind"
        if self.is_two_pair(hand):
            return 2 # "two pair"
        if self.is_one_pair(hand):
            return 1 # "one pair"
        return 0 # "high card"

    def break_tie(self)


    def determine_hand_ranks(self, active):
        hand_types = np.zeros(self.num_players)
        for player in range(self.num_players):
            if not active[player]:
                continue
            hand = self.hole_cards[player] + self.community_cards
            hand_types[player] = self.get_hand_type()
        
        if (hand_types==best_hand).sum() > 1:
        else:
            
            self.
            


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
