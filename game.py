import numpy as np
from os import listdir
import sys
from utils import rotate_list, Hand, parse_argv, timeout#, BettingState
from player import Caller, SimpleRaiser
from move import Move, BettingState, BettingRound

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

    def get_high_card(self, best_cards: np.ndarray):
        hand_numbers = np.apply_along_axis(lambda x: int('' .join(x)), 1, np.apply_along_axis(lambda x: x == max(x), 0, best_cards).astype(int).astype(str))
        hand_rank = np.array([(hand_number > hand_numbers).sum() for hand_number in hand_numbers])
        return hand_rank

    def determine_hand_ranks(self, playing):
        hands = []
        for player in range(self.num_players):
            if not playing[player]:
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
                    hands_kind = [hand for hand, type in zip(hands, hand_types) if type == hand_type]
                    faces = np.array([hand.hand['face'] for hand in hands_kind])
                    num_kickers = 1 if hand_type == 7 else 2 if hand_type == 3 else 3
                    kickers = np.array([np.array([card for card in hand.sorted_cards if card != face])[:num_kickers] for hand, face in zip(hands_kind, faces)])
                    kicker_ranks = self.get_high_card(kickers)
                    hand_ranks[hand_type_mask] += np.array([(face > faces).sum() + (kicker_rank > kicker_ranks[faces == face]).sum() for face, kicker_rank in zip(faces, kicker_ranks)])
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
                    hands_kind = [hand for hand, type in zip(hands, hand_types) if type == hand_type]
                    high_faces = np.array([hand.hand['high face'] for hand in hands_kind])
                    low_faces = np.array([hand.hand['low face'] for hand in hands_kind])
                    kickers = np.array([np.array([card for card in hand.sorted_cards if card not in (high_face, low_face)]) for hand, high_face, low_face in zip(hands_kind, high_faces, low_faces)])
                    kicker_ranks = self.get_high_card(kickers[:, :1])
                    hand_ranks[hand_type_mask] += np.array([(high_face > high_faces).sum() + (low_face > low_faces[high_faces == high_face]).sum() + (kicker_rank > kicker_ranks[(high_faces == high_face) & (low_faces == low_face)]).sum() for high_face, low_face, kicker_rank in zip(high_faces, low_faces, kicker_ranks)])
                # high card
                else:
                    best_five_cards = np.array([np.array([hand.sorted_cards[card] for hand, type in zip(hands, hand_types) if type == hand_type]) for card in range(5)]).T # getting top 5 cards
                    high_card_ranks = self.get_high_card(best_five_cards)
                    hand_ranks[hand_type_mask] += high_card_ranks

        final_ranks = np.zeros(len(playing))
        final_ranks[playing] = hand_ranks + 1
        return final_ranks


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
        self.chip_stacks = np.append(self.chip_stacks, algo.get_chip_stack())
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
        """
        shares - number of chips player has contributed to pot
        playing - array of True if player is still playing in current hand and False otherwise 
        active - array of True if player is still active (playing and not all in) in current hand and False otherwise
        pot - current pot
        """
        self.shares = np.zeros(self.num_players)
        self.playing = self.chip_stacks > 0
        self.active = self.chip_stacks > 0
        self.reset_bets()
        self.pot = 0

    def bet_blinds(self, LB, BB):
        # little blind
        if LB < self.chip_stacks[0]:
            self.__players[0].update_stack(-LB)
            self.bets[0] = LB
            self.chip_stacks[0] -= LB
        else:
            self.__players[0].update_stack(-self.chip_stacks[0])
            self.bets[0] = self.chip_stacks[0]
            # self.shares[0] = self.chip_stacks[0]
            self.chip_stacks[0] = 0
            self.active[0] = False
            print("{} is little blind and is forced all in!".format(self.names[0]))
        # big blind
        if BB < self.chip_stacks[1]:
            self.__players[1].update_stack(-BB)
            self.bets[1] = BB
            self.chip_stacks[1] -= BB
        else:
            self.__players[1].update_stack(-self.chip_stacks[1])
            self.bets[1] = self.chip_stacks[1]
            # self.shares[1] = self.chip_stacks[1]
            self.chip_stacks[1] = 0
            self.active[1] = False
            print("{} is big blind and is forced all in!".format(self.names[1]))

    @timeout(5)
    def __get_move(self, seat):
        return self.__players[seat].make_move()

    def get_move(self, seat):
        try:
            return self.__get_move(seat)
        except TimeoutError:
            if self.bets[seat] == self.bets.max():
                return Move("check")
            else:
                return Move("fold")

    def update_stack(self, player, amount):
        self.chip_stacks[player] += amount
        self.__players[player].update_stack(amount)

    def get_betting_state(self, betting_round, move: Move):
        betting_state = BettingState(self.names, self.actor, self.playing, self.active, self.bets, self.pot, self.shares, betting_round, move, self.last_raiser)
        return betting_state

    def update_betting_states(self, start, betting_round, move: Move):
        betting_state = self.get_betting_state(betting_round, move)
        for j, name, player in zip(np.arange(self.num_players), self.names, self.__players):
            player.update_betting_state(betting_state.add_player_info(name, (j+start)%self.num_players))

    def round_of_betting(self, start=0, verbose=False):
        if self.active.sum() < 2:
            pass

        betting_round = BettingRound(self.names, self.playing, self.active, self.chip_stacks, self.shares, 0)
        max_bet = -1
        round = 0

        while not (self.bets[self.active] == max_bet).all():
            for i in range(self.num_players):
                actor = self.names[(i+start) % self.num_players]

                if not self.active[seat]:
                    continue
                if seat == self.last_raiser and betting_round > 0:
                    break
                if self.active.sum() <= 1:
                    break

                # proceeding with betting
                move = self.get_move(seat)
                max_bet = self.bets.max()

                if verbose:
                    print("\nseat: {:d}, pot: {:.2f}, highest bet: {:.2f}, last raiser: {:d}, betting round: {:d}, num active: {:d}".format(seat, self.pot + self.bets.sum(), max_bet, self.last_raiser, betting_round, self.active.sum()))
                    with np.printoptions(precision=3, suppress=True):
                        print("bets: ", end='')
                        print(self.bets)
                        print("shares: ", end='')
                        print(self.shares + self.bets)
                        print("chip stacks: ", end='')
                        print(self.chip_stacks)
                    self.show_stacks_according_to_players()


                

                # updating each player on current state of betting round
                self.update_betting_states(start, betting_round, move)

            # end of path around table 
            betting_round += 1
            max_bet = self.bets.max()
            if self.active.sum() <= 1:
                    break
        # self.shares = (self.shares + round_shares) * self.active
        self.shares += self.bets
        self.pot += self.bets.sum()
        self.reset_bets()

    def round_of_betting_OLD(self, start=0, verbose=False):
        if self.active.sum() < 2:
            pass

        max_bet = -1
        self.last_raiser = (start-1) % self.num_players
        betting_round = 0
        round_shares = np.zeros(self.num_players)

        while not (self.bets[self.active] == max_bet).all():
            for i in range(self.num_players):
                seat = (i+start) % self.num_players
                self.actor = self.names[seat]

                if not self.active[seat]:
                    continue
                if seat == self.last_raiser and betting_round > 0:
                    break
                if self.active.sum() <= 1:
                    break

                # proceeding with betting
                move = self.get_move(seat)
                max_bet = self.bets.max()

                if verbose:
                    print("\nseat: {:d}, pot: {:.2f}, highest bet: {:.2f}, last raiser: {:d}, betting round: {:d}, num active: {:d}".format(seat, self.pot + self.bets.sum(), max_bet, self.last_raiser, betting_round, self.active.sum()))
                    with np.printoptions(precision=3, suppress=True):
                        print("bets: ", end='')
                        print(self.bets)
                        print("shares: ", end='')
                        print(self.shares + self.bets)
                        print("chip stacks: ", end='')
                        print(self.chip_stacks)
                    self.show_stacks_according_to_players()

                if move.move == "fold":
                    if verbose:
                        print("{} (seat {}) folds!".format(self.names[seat], seat))
                    self.playing[seat] = self.active[seat] = False
                    round_shares[seat] = 0
                elif move.move == "call":
                    call_amount = max_bet-self.bets[seat]
                    if call_amount >= self.chip_stacks[seat]:
                        if verbose:
                            print("{} calls and is all in!".format(self.names[seat]))
                        round_shares[seat] = self.bets[seat] = self.chip_stacks[seat] + self.bets[seat]
                        self.update_stack(seat, -self.chip_stacks[seat])
                        self.active[seat] = False
                    else:
                        if verbose:
                            print("{} (seat {}) calls!".format(self.names[seat], seat))
                        # round_shares = max_bet
                        self.update_stack(seat, -call_amount)
                        self.bets[seat] = max_bet
                elif move.move == "check":
                    if self.bets[seat] < max_bet:
                        raise ValueError("{} attempted to check when they needed to bet {} more to match {}".format(self.names[seat], max_bet-self.bets[seat], max_bet))
                    if verbose:
                        print("{} (seat {}) checks!".format(self.names[seat], seat))
                else:
                    if move.amount > self.chip_stacks[seat]:
                        raise ValueError("{} attempted to bet {} when they only have {}!".format(self.names[seat], move.amount, self.chip_stacks[i]))
                    elif move.amount + self.bets[seat] <= max_bet:
                        raise ValueError("{} attempted to raise {} when they must raise at least {} to not call, check, or fold".format(self.names[seat], move.amount, max_bet-self.bets[seat]+1))
                    elif move.amount == self.chip_stacks[i]:
                        if verbose:
                            print("{} is all in!".format(self.names[seat]))
                        # round_shares[i] = self.bets[i] = self.chip_stacks[i] + self.bets[i]
                        self.update_stack(seat, -self.chip_stacks[seat])
                        self.active[seat] = False
                        self.last_raiser = seat
                    else:
                        if verbose:
                            print("{} (seat {}) raises by {}!".format(self.names[seat], seat, move.amount))
                        self.update_stack(seat, -move.amount)
                        self.bets[seat] += move.amount
                        # round_shares += self.bets[i]
                        self.last_raiser = seat

                # updating each player on current state of betting round
                self.update_betting_states(start, betting_round, move)

            # end of path around table 
            betting_round += 1
            max_bet = self.bets.max()
            if self.active.sum() <= 1:
                break
        # self.shares = (self.shares + round_shares) * self.active
        self.shares += self.bets
        self.pot += self.bets.sum()
        self.reset_bets()

    def showdown(self, hand_ranks, verbose=False):
        winning_hands = hand_ranks == hand_ranks.max()
        share_orders = np.argsort(self.shares[winning_hands])
        share_bits = np.diff(self.shares[winning_hands], prepend=0)
        num_winners = winning_hands.sum()
        payouts = np.zeros(num_winners)
        shares_left = self.shares.copy()

        while shares_left.sum() > 0:
            if verbose:
                print("winning hands:", end=' ')
                print(winning_hands)
                with np.printoptions(precision=3, suppress=True):
                    print("shares:", end=' ')
                    print(self.shares)
                    print("share orders:", end=' ')
                    print(share_orders)

            for share_bit, num_payed in zip(share_bits, np.arange(num_winners)):
                shares_diff = shares_left-share_bit
                payouts[share_orders[:(num_winners-num_payed)]] += (self.num_players*share_bit + (shares_diff*(shares_diff < 0)).sum()) / (num_winners-num_payed)
                shares_left = shares_diff * (shares_diff > 0)
                if verbose:
                    print("share bit: {:.2f}".format(share_bit))
                    with np.printoptions(precision=3, suppress=True):
                        print("shares left: ", end='')
                        print(shares_left)

            if shares_left.sum() > 0:
                shares_left[winning_hands] = 0
                hand_ranks[winning_hands] = -1
                winning_hands = hand_ranks == hand_ranks.max()
                num_winners = winning_hands.sum()
                share_bits = np.diff(shares_left[winning_hands], prepend=0)

        if verbose:
            with np.printoptions(precision=3, suppress=True):
                print("payouts: ", end='')
                print(payouts)
                print("chip stacks before: ", end='')
                print(self.chip_stacks)
            print("pot: {:.2f}".format(self.pot))

        if np.round(payouts.sum(), 2) != np.round(self.pot, 2):
            self.show_stacks_according_to_players()
            raise RuntimeError("total payouts ({:.8f}) are not equal to pot ({:.8f})!".format(payouts.sum(), self.pot))

        # updating chip stacks
        self.chip_stacks[winning_hands] += payouts
        for player, payout in zip([player for player, winning_hand in zip(self.__players, winning_hands) if winning_hand], payouts):
            player.update_stack(payout)
        if verbose:
            with np.printoptions(precision=3, suppress=True):
                print("chip stacks after: ", end='')
                print(self.chip_stacks)

    def round_end(self, hole_cards, hand_ranks):
        player_hands = {name: hand if playing else None for name, playing, hand in zip(self.names, self.playing, hole_cards)}
        player_hand_ranks = {name: hand_rank if playing else 0 for name, playing, hand_rank in zip(self.names, self.playing, hand_ranks)}
        for player, name in zip(self.__players, self.names):
            player_hands_copy, player_hand_ranks_copy = player_hands.copy(), player_hand_ranks.copy()
            player_hands_copy["me"] = player_hands_copy.pop(name)
            player_hand_ranks_copy["me"] = player_hand_ranks_copy.pop(name)
            player.round_end(player_hands_copy, player_hand_ranks_copy)

    def show_hands(self, hole_cards, community_cards):
        print("\nPlayers' hands:", end='')
        for name, cards in zip(self.names, hole_cards):
            print("\n{}:".format(name), end=' ')
            for card in cards:
                print(card, end=' ')
        print("\nCommunity cards:", end=' ')
        for card in community_cards:
            print(card, end=' ')
        print("\n")

    def show_stacks_according_to_players(self):
        chip_stacks = []
        for player in self.__players:
            chip_stacks.append(player.get_chip_stack())
        with np.printoptions(precision=3, suppress=True):
            print("chip stacks according to players: ", end='')
            print(np.array(chip_stacks))

    def move_blinds(self):
        self.__players = rotate_list(self.__players, 1)
        self.chip_stacks = np.array(rotate_list(self.chip_stacks.tolist(), 1))
        self.names = rotate_list(self.names, 1)

    def play_hand(self, LB, BB, verbose=False):
        if verbose:
            print("\n\n--- new hand ---")

        # init
        dealer = Dealer(self.num_players)
        self.init_hand()
        community_cards = []

        if verbose:
            print("\n\npre-flop")

        # deal hole cards
        hole_cards = dealer.deal_hole_cards()
        self.issue_hole_cards(hole_cards)
        self.bet_blinds(LB, BB)
        self.round_of_betting(start=2, verbose=verbose)

        # flop
        if verbose:
            print("\n\nflop")

        community_cards += dealer.deal_community_cards(3)
        self.share_community_cards(community_cards)
        self.round_of_betting(verbose=verbose)

        # turn card
        if verbose:
            print("\n\nturn")

        community_cards += dealer.deal_community_cards(1)
        self.round_of_betting(verbose=verbose)

        # river card
        if verbose:
            print("\n\nriver")

        community_cards += dealer.deal_community_cards(1)
        self.round_of_betting(verbose=verbose)

        if verbose:
            self.show_hands(hole_cards, community_cards)

        # showdown + distribute pot
        hand_ranks = dealer.determine_hand_ranks(self.playing)
        self.showdown(hand_ranks, verbose=verbose)

        if verbose:
            self.show_stacks_according_to_players()
        
        # giving end-of-round information to players
        self.round_end(hole_cards, hand_ranks)

        # setup for next game
        self.move_blinds()

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


if __name__  == '__main__':
    args = parse_argv()
    player_files = [file for file in listdir(args.fpath) if file.startswith("player_")]
    names = [file.removeprefix("player_").removesuffix(".py") for file in player_files]
    stdout = sys.stdout
    if args.outfile is not None:
        sys.stdout = open(args.outfile, 'w')

    # registering players at table
    table = Table()
    table.register_player("Caller 1", Caller(args.buy_in))
    table.register_player("Caller 2", Caller(args.buy_in))
    table.register_player("Small Raiser 1", SimpleRaiser(args.buy_in))
    table.register_player("Small Raiser 2", SimpleRaiser(args.buy_in))
    table.register_player("Small Raiser 3", SimpleRaiser(args.buy_in))
    table.register_player("Caller 3", Caller(args.buy_in))

    # playing hands
    for hand in range(args.hands):
        if hand % int(args.hands/10) == 0:
            print("Played {} hands!".format(hand), file=stdout)
        table.play_hand(args.little_blind, args.big_blind, verbose=args.verbose)

        if (table.chip_stacks == 0).any():
            for name, chip_stack in zip(table.names, table.chip_stacks):
                if chip_stack == 0:
                    table.remove_player(name)
                    print("{} kicked out!".format(name), file=stdout)

        if table.num_players == 1:
            break
    
    # displaying final results
    print("\nFinal chip stacks:", file=stdout)
    for name, stack in zip(table.names, table.chip_stacks):
        print("{}: {:.2f}".format(name, stack), file=stdout)

    if args.outfile is not None:
        sys.stdout.close()