import torch
from torch.optim import Adam
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random

from src.env import TwJanggiEnv
from agent.encoder import TwJanggiEncoder
from agent.network import TwJanggiNet
from agent.mcts import MCTS
from collections import deque

class SelfPlay:
    def __init__(self, encoder, network):
        self.env = TwJanggiEnv()
        self.encoder = encoder
        self.network = network

    def run(self, dataset, num_play, num_traversal):
        self.network.eval()

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
    
class LossFunc(nn.Module):
    def __init__(self):
        super().__init__()
        self.mse = nn.MSELoss()

    def forward(self, v_target, v_pred, p_target, p_pred):
        v_loss = self.mse(v_pred, v_target)
        p_loss = (p_target * F.log_softmax(p_pred, dim=1)).sum(dim=1).mean()
        loss = v_loss - p_loss
        return loss
    
class Trainer:
    def __init__(self, num_play=100, num_traversal=100, T=4, hidden_ch=64, num_block=4, c_puct=2, alpha=0.3, epsilon=0.25, batch_size=8, c=1e-4):
        self.num_play = num_play
        self.num_traversal = num_traversal
        self.T = T
        self.hidden_ch = hidden_ch
        self.num_block = num_block
        self.c_puct = c_puct
        self.alpha = alpha
        self.epsilon = epsilon
        self.batch_size = batch_size
        self.c = c

        self.encoder = TwJanggiEncoder(self.T)
        self.network = TwJanggiNet(self.T*21+2, self.hidden_ch, self.num_block)
        self.player = SelfPlay(self.encoder, self.network)
        self.dataset = deque(maxlen=100000)

        self.optimizer = Adam(self.network.parameters(), weight_decay=self.c)
        self.loss_fn = LossFunc()

    def train(self, iter):
        loss_history = []

        for i in range(iter):
            self.player.run(self.dataset, self.num_play, self.num_traversal)
            self.network.train()
            total_loss = 0

            for _ in range(len(self.dataset) // self.batch_size):
                state, pi, z = self._get_mini_batch(self.dataset, self.batch_size)
                p, v = self.network(state)
                loss = self.loss_fn(z, v, pi, p)
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
            
            loss_history.append(total_loss / len(self.dataset // self.batch_size))
            print(f'[{i+1}번째 iteration] Loss: {loss_history[-1]}')

    def _get_mini_batch(self, dataset, batch_size):
        datas = random.sample(dataset, batch_size)

        state, pi, z = zip(*datas)

        state_tensor = self.encoder.get_tensor(state)
        pi_tensor = torch.FloatTensor(np.array(pi))
        z_tensor = torch.FloatTensor(np.array(z)).unsqueeze(1)

        return state_tensor, pi_tensor, z_tensor