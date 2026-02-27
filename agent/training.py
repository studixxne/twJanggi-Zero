import torch
import numpy as np
from src.env import TwJanggiEnv
from agent.mcts import MCTS
from collections import deque

class SelfPlay:
    def __init__(self, encoder, network):
        self.env = TwJanggiEnv()
        self.encoder = encoder
        self.network = network

    def run(self, num_play, num_traversal):
        dataset = deque()

        for episode in range(num_play):
            history = []
            state = self.env.reset()
            mcts = MCTS(self.encoder, self.network)

            while True:
                temperature = 1 if self.env.turn < 30 else 0
                pi = mcts.get_pi(self.env, num_traversal=num_traversal, temperature=temperature)
                history.append([state, pi])
                action = np.random.choice(np.arange(132), p=pi)
                mcts.next_node(action)
                state, reward, done, info = self.env.step(action)
                
                if done:
                    z = reward
                    break

            for h in history[::-1]:
                h.append(z)
                z *= -1

            dataset.extend(history)
        
        return dataset
    
class Trainer:
    def __init__(self):
        pass