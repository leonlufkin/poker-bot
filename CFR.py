import numpy as np
from utils import abstract_hand_key, Move, BettingState
from abc import ABC, abstractmethod
from copy import deepcopy

class Node(ABC):
    def __init__(self, node_prob, betting_state: BettingState, cards_seen = []):
        self.children = {}
        self.child_probs = {}
        self.node_prob = node_prob
        self.expected_utility = 0
        self.betting_state = betting_state
        self.cards_seen = cards_seen

    def add_child(self, key, node, prob):
        """
        adds a child node to the dictionary of children
        """
        self.children.update({key: node})
        self.child_probs.update({key: prob})

    @abstractmethod
    def spawn_child(self, key):
        """
        spawn a child node (of class Node) given its key
        """
        pass

    def get_child(self, key):
        """
        obtain a child node from set of child nodes given its key
        """
        if self.children[key] is None:
            return self.spawn_child(key)
        else:
            return self.children[key]

    def sample_child(self):
        """
        select a child node according to their selection probabilities (child_probs)
        """
        child_key = np.random.choice(np.array(list(self.children.keys())), 1, np.array(list(self.child_probs.values())))
        return self.get_child(child_key)
 

class Chance(Node):
    def __init__(self, node_prob, betting_state: BettingState, cards_seen=[]):
        super().__init__(node_prob, betting_state, cards_seen)

class Terminal(Node):
    def __init__(self, node_prob, betting_state):
        super().__init__(node_prob, betting_state)

    def spawn_child(self, key):
        pass
    
    def get_player_utility(self, player):
        if self.playing[player]:
            return sum([share for p, share in self.shares.items() if p != player])
        else:
            return -self.shares[player]

class Action(Node):
    def __init__(self, node_prob, betting_state, cards_seen, raise_buckets: np.ndarray, player):
        super().__init__(node_prob, betting_state, cards_seen)
        self.regret = 0
        self.player = player
        self.num_players = len(betting_state.playing)
        self.children_explored = 0 # counts child and each of its children
        self.raise_buckets = raise_buckets
        num_children = 3 + self.raise_buckets.shape[0]
        for action in ["fold", "call", "check"] + self.raise_buckets.tolist():
            self.children.update({action: None})
            self.child_probs.update({action: 1/num_children})

    def abstract_raise(self, amount):
        closest_bucket_ind = np.argmin(np.absolute(self.raise_buckets - amount))
        return int(self.raise_buckets[closest_bucket_ind])

    def spawn_child(self, key):
        betting_state = deepcopy(self.betting_state)
        if key == "fold":
            betting_state.playing[self.player] = False
            # one player left
            if sum(list(betting_state.playing.values())) == 1:
                child = Terminal(1, betting_state)
            else:
                # player was last to act
                if betting_state.last_raiser == (betting_state.actor+1)%self.num_players:
                    # was river
                    if len(self.cards_seen) == 7:
                        
                    # was preflop, flop, or turn
                    else:
                        child = Chance(cards, card_probs):


        elif key == "call":
            
        else:
            pass

        self.children[key] = child
        return child



    def get_child(self, key):
        if "raise" in key:
            amount = float(key.split('-')[-1])
            key = self.abstract_raise(amount)
        super().get_child(key)


class CFR_Tree:
    def __init__(self, num_preflop_buckets, names: np.ndarray, chip_stacks: np.ndarray, raise_buckets) -> None:
        self.names = names
        self.num_players = chip_stacks.shape[0]
        self.raise_buckets = raise_buckets

        self.head = Chance(1, 0, chip_stacks)
        self.head.children.update({i: Action(1/num_preflop_buckets, 0, chip_stacks, raise_buckets, names[0]) for i in range(num_preflop_buckets)})

