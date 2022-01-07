import numpy as np
from utils import abstract_hand_key
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
    def __init__(self, children: dict, probs: list) -> None:
        self.children = children
        self.probs = probs
        assert len(children) == len(probs)
        self.utility = 0
        self.iterations = 0

    def update_utility(self) -> None:
        probs = np.array(self.probs)
        utilities = np.array([child.utility for child in self.children.values()])
        self.utility = (probs * utilities).sum()
    
    @abstractmethod
    def update_probs(self, probs) -> None:
        pass

    def select_child(self):
        child_key = np.random.choice(self.children.keys(), 1, self.probs)
        return self.children[child_key]


class Chance(Node):
    def __init__(self, buckets: int, plays: list):
        self.plays = plays
        probs = [play/self.iterations for play in plays]
        super().__init__(np.arange(buckets), probs)


class Action(Node):
    def __init__(self, children: dict, probs: list) -> None:
        super().__init__(children, probs)
        self.regret = 0

    def update_regret(self, regret):
        self.regret = (self.iterations * self.regret + regret) / (self.iterations + 1)
        self.iterations += 1

    

class CFR_Tree:
    def __init__(self):
        self.head = Node("chance", 2)
    