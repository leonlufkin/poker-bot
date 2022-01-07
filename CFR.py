import numpy as np
from utils import abstract_hand_key, Move
from abc import ABC, abstractmethod

class OldAction:
    def __init__(self, action):
        self.action = action
        self.children = {}
        self.regret = 0
        self.iterations = 0

    def update_regret(self, regret):
        self.regret = (self.iterations * self.regret + regret) / (self.iterations + 1)
        self.iterations += 1

    def add_child(self, action):
        self.children.update({action: Action(action)})

class Node(ABC):
    """
    a node in the game tree
    """
    def __init__(self, pot: float, children: dict, child_probs: list) -> None:
        self.pot = pot
        self.children_dict = children
        self.child_probs = child_probs
        self.utility = 0
        self.iterations = 0

    def update_utility(self) -> None:
        probs = np.array(self.probs)
        utilities = np.array([child.utility for child in self.children.values()])
        self.utility = (probs * utilities).sum()

    def choose_child(self, child_key):
        return self.children[child_key]

    def select_child(self):
        child_key = np.random.choice(self.children.keys(), 1, self.probs)
        return self.children[child_key]


class Chance(Node):
    """
    a chance node - used when cards get dealt
    """
    def __init__(self, pot: float, buckets: list, plays: list):
        self.child_iterations = plays
        probs = list(np.array(plays) / self.iterations)
        super().__init__(pot, buckets, probs)

    def choose_child(self, hand: list, hand_to_bucket: dict):
        child_key = abstract_hand_key('-'.join(sorted(hand)))
        return super().choose_child(hand_to_bucket[child_key])


class Action(Node):
    """
    an action node - used when players make actions
    """
    def __init__(self, children: dict, probs: list) -> None:
        super().__init__(children, probs)
        self.regret = 0

    def choose_child(self, child_key):
        if isinstance(child_key, Move):
            move.actor
        else:
            return super().choose_child(child_key)

    def update_regret(self, regret):
        self.regret = (self.iterations * self.regret + regret) / (self.iterations + 1)
        self.iterations += 1

    def update_probs(self):
        regrets = np.array([child.regret for child in self.children])
        total_regret = np.maximum(regrets, 0).sum()
        if total_regret > 0:
            self.probs = np.maximum(regrets, 0) / total_regret
        else:
            self.probs = np.ones(regrets.shape[0]) / regrets.shape[0]


class Terminal(Node):
    def __init__(self, pot, outcome) -> None:
        self.pot = pot
        self.children = None
        self.probs = 1
        self.utility = 

    
class CFR_Tree:
    """
    the poker game tree, built up of chance, action, and terminal nodes
    """
    def __init__(self, preflop_buckets: dict, flop_buckets: dict, bet_buckets: dict):
        # head node, where the hole cards are dealt, is always a chance node
        self.head = self.node = Chance(0, preflop_buckets, preflop_probs)
    