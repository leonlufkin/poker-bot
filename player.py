import numpy as np
from abc import ABC, abstractmethod
from utils import HandState, Move, Hand, abstract_hand_key

class Player(ABC):
    def __init__(self, number_chips):
        self.chip_stack = number_chips
        self.hole_cards = ['..', '..']
        self.community_cards = []
        self.wins = 0
        self.hands = 0
        self.hand_state = None
        self.prev_hand_state = None

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

    def infer_move(self) -> Move:
        """
        I think this function is useless now that I changed HandState but I'll leave it for now
        """
        hand_state = self.hand_state
        actor = hand_state.actor
        # first move
        if self.prev_hand_state is None:
            calling_bet = np.array([bet for player, bet in hand_state.bets.items() if player != actor]).max()
            # actor folded
            if (1 - np.array(list(hand_state.playing.values()), dtype=int)).sum() > 0:
                return actor, Move("fold")
            # actor called
            if hand_state.bets[actor] == calling_bet:
                return actor, Move("call")
            # actor raised
            return actor, Move("raise", hand_state.bets[actor])
        
        # not first move
        prev_hand_state = self.prev_hand_state
        calling_bet = np.array(list(prev_hand_state.bets.values())).max()

        # actor folded
        playing = np.array(list(hand_state.playing.values())) - np.array(list(prev_hand_state.playing.values()))
        if (playing < 0).sum() > 0:
            return actor, Move("fold")
        # actor checked
        if prev_hand_state.bets[actor] == hand_state.bets[actor] == calling_bet:
            return actor, Move("check")
        # actor called
        if hand_state.bets[actor] == calling_bet:
            return actor, Move("call")
        # actor raised
        return actor, Move("raise", hand_state.bets[actor])

    def update_hand_state(self, hand_state: HandState) -> None:
        if self.prev_hand_state is not None:
            self.prev_hand_state = self.hand_state
            self.hand_state = hand_state

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

from CFR import Action, Chance, Terminal, CFR_Tree
from utils import load_zipped_pickle
preflop_hand_to_bucket = load_zipped_pickle("results/hand strength/preflop_hand_to_bucket.pkl")
flop_hand_to_bucket = load_zipped_pickle("results/hand strength/flop_hand_to_bucket.pkl")

class CFR(Player):
    def __init__(self, chip_stack, CFR_tree: CFR_Tree, my_name, hand_strength_path="results/hand strength") -> None:
        super().__init__(chip_stack)
        self.CFR_tree = CFR_tree
        self.my_name = my_name
        self.preflop_hand_to_bucket = load_zipped_pickle(f"{hand_strength_path}/preflop_hand_to_bucket.pkl")
        self.flop_hand_to_bucket = load_zipped_pickle(f"{hand_strength_path}/flop_hand_to_bucket.pkl")

    def get_abstract_hand_key(self, hand):
        return abstract_hand_key('-'.join(sorted(hand)))

    def get_hole_cards(self, hole_cards):
        super().get_hole_cards(hole_cards)
        self.move_node_preflop()

    def get_preflop_bucket(self):
        abstract_key = self.get_abstract_hand_key(self.hole_cards)
        return self.preflop_hand_to_bucket[abstract_key]

    def move_node_preflop(self):
        """
        move down the game tree based on chance's preflop action (which hole cards are dealt)
        hole cards are bucketed based on hand strength
        """
        preflop_bucket = self.get_preflop_bucket()
        self.node = self.CFR_tree.head.get_child(preflop_bucket)

    def get_community_cards(self, community_cards):
        super().get_community_cards(community_cards)
        if len(community_cards) == 3:
            self.move_node_flop()
        elif len(community_cards) == 4:
            self.move_node_turn()
        else:
            self.move_node_river()

    def get_flop_bucket(self):
        abstract_key = self.get_abstract_hand_key(self.hole_cards + self.community_cards)
        return self.flop_hand_to_bucket[abstract_key]

    def move_node_flop(self):
        """
        move down the game tree based on chance's flop action (which cards are dealt on the flop)
        flop card sequences are bucketed based on hand strength
        """
        flop_bucket = self.get_flop_bucket()
        self.node = self.node.get_child(flop_bucket)

    def move_node_turn(self):
        """
        move down the game tree based on chance's turn action (which turn card is dealt)
        turn card sequences are bucketed based on their abstract hand key
        """
        abstract_key = self.get_abstract_hand_key(self.hole_cards + self.community_cards)
        self.node = self.node.get_child(abstract_key)

    def move_node_river(self):
        """
        move down the game tree based on chance's river action (which river card is dealt)
        river card sequences are bucketed based on their abstract hand key
        """
        self.move_node_turn()

    def move_node_player(self):
        """
        move down the game tree based on an opponent's action
        I think I could (should?) also use this for the player
        """
        move_key = f"{self.hand_state.actor}-{self.hand_state.move.move}"
        if self.hand_state.move.move == "raise":
            move_key += f"-{self.hand_state.move.amount}"
        self.node = self.node.get_child(move_key)

    def update_hand_state(self, hand_state: HandState) -> None:
        super().update_hand_state(hand_state)
        self.move_node_player()

    def get_node_strategy(self, node: Action):
        """
        given regrets for actions, returns strategy according to regret matching
        """
        actions = list(node.children.keys())
        regrets = np.array([child.regret for child in node.children.values()])
        pos_regrets = np.maximum(regrets, 0)
        if pos_regrets.sum() > 0:
            strategy_probs = pos_regrets/pos_regrets.sum()
        else:
            strategy_probs = np.ones(len(actions))/len(actions)
        strategy = {action: prob for action, prob in zip(node.children.keys(), strategy_probs)}
        return strategy

    def traverse(self, node, traverser, t):
        """
        CFR traversal with external sampling
        logic comes straight from Brown, et al. (2019)
        """
        if isinstance(node, Terminal):
            return node.get_player_utility(traverser)
        if isinstance(node, Chance):
            child = node.sample_child()
            return self.traverse(child, traverser, t)
        # node must be an action node
        # old strategy
        strategy = node.child_probs
        if node.player == traverser:
            expected_utilities = {}
            for action in strategy.keys():
                expected_utilities.update({action: self.traverse(node.get_child(action), traverser, t)})
            avg_utility = sum([strategy[action] * expected_utilities[action] for action in strategy.keys()])
            for key, action in node.children:
                action_advantage = expected_utilities[key] - avg_utility
                action.regret = (t * action.regret + strategy[action] * action_advantage) / (t+1) # assuming probability that other player plays to reach action is given by traverser's old strategy for that node (works for 2-player, not sure about 3+)
            # updating strategy
            node.child_probs = self.get_node_strategy(node)
        else:
            child = node.sample_child()
            return self.traverse(child, traverser, t)

    def make_move(self):
        # I need to fix the below line so it only includes valid actions
        self.traverse(self.node, self.hand_state.seat, self.hands)
        actions = np.array(list(self.node.child_probs.keys()))
        strategy = np.array(list(self.node.child_probs.values()))
        action = np.random.choice(actions, 1, strategy)
        return action

    def update_strategy(self):
        pass

    def round_end(self, player_hands, player_hand_ranks):
        super().round_end(player_hands, player_hand_ranks)
        self.update_strategy()
