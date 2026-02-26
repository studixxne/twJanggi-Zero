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
    
class MCTS:
    def __init__(self, root, encoder, network):
        self.root = root
        self.encoder = encoder
        self.network = network

    def traversal(self, env):
        env = env.copy()
        cur = self.root

        # Leaf Node를 찾도록 함
        while len(cur.childs):
            action = cur.get_U()
            state, reward, done, info = env.step(action)
            cur = cur.childs[action]

        # Terminal Node가 아닌 경우에는 Expansion을 진행
        if not done:
            state_tensor = self.encoder.get_tensor(state)

            with torch.no_grad():
                policy_tensor, value_tensor = self.network(state_tensor)

            policy = policy_tensor.squeeze(0).cpu().numpy()
            value = value_tensor.item()
            
            self.expansion(cur, env, policy)

        # Terminal Node인 경우에는 그냥 Reward 가져옴
        else:
            value = reward

        # 얻어낸 Value를 기반으로 Backpropagation 수행
        self.backpropagation(cur, value)

    def expansion(self, node, env, policy):
        valid_actions = env.get_valid_actions()
        valid_actions_indices = np.where(valid_actions == 1)[0]
        mask = (valid_actions == 0)

        prob = policy.copy()
        prob[mask] = -np.inf
        prob -= np.max(prob)
        prob = np.exp(prob) / np.sum(np.exp(prob))

        node.P = prob
        node.mask = mask

        for i in valid_actions_indices:
            node.childs[i] = Node(node, i)

    def backpropagation(self, node, v):
        if node == self.root:
            return
        
        cur = node
        while True:
            action = cur.action
            cur = cur.parent
            cur.N[action] += 1
            cur.W[action] += v
            cur.Q[action] = cur.W[action] / cur.N[action]
            v *= -1

            if cur == self.root:
                break