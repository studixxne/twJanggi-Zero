import torch
from torch import nn
import numpy as np

class Node:
    def __init__(self, p, action):
        self.parent = p
        self.childs = {}
        self.action = action
        self.mask = None

        # Childs에 대한 Edge
        self.P = np.zeros(132)
        self.N = np.zeros(132)
        self.W = np.zeros(132)
        self.Q = np.zeros(132)

    def get_U(self, c_puct=2):
        U = c_puct * self.P * np.sqrt(np.sum(self.N)) / (1 + self.N)
        UCB = self.Q + U
        UCB[self.mask] = -np.inf
        return np.argmax(UCB)