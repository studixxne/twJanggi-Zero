import torch
import numpy as np

class Node:
    def __init__(self, p, action):
        self.parent = p
        self.childs = {}
        self.action = action
        self.mask = None
        self.is_expansion = False

        # Childs에 대한 Edge
        self.P = np.zeros(132, dtype=np.float32)
        self.N = np.zeros(132, dtype=np.float32)
        self.W = np.zeros(132, dtype=np.float32)
        self.Q = np.zeros(132, dtype=np.float32)

    def get_U(self, c_puct=2):
        U = c_puct * self.P * np.sqrt(np.sum(self.N) + 1) / (self.N + 1)
        UCB = self.Q + U
        UCB[self.mask] = -np.inf
        return np.argmax(UCB)
    
class MCTS:
    def __init__(self, encoder, network):
        self.root = Node(None, None)
        self.encoder = encoder
        self.network = network

    def traversal(self, env):
        env = env.copy()
        cur = self.root

        # Leaf Node를 찾도록 함
        while cur.is_expansion:
            action = cur.get_U()

            if not action in cur.childs:
                cur.childs[action] = Node(cur, action)

            state, reward, done, info = env.step(action)
            cur = cur.childs[action]

        # Terminal Node가 아닌 경우에는 Expansion을 진행
        if not done:            
            value = -self.expansion(cur, env, state)

        # Terminal Node인 경우에는 그냥 Reward 가져옴
        else:
            value = reward

        # 얻어낸 Value를 기반으로 Backpropagation 수행
        self.backpropagation(cur, value)

    def expansion(self, node, env, state):
        state_tensor = self.encoder.get_tensor(state)

        with torch.no_grad():
            policy_tensor, value_tensor = self.network(state_tensor)

        policy = policy_tensor.squeeze(0).cpu().numpy()
        value = value_tensor.item()

        valid_actions = env.get_valid_actions()
        mask = (valid_actions == 0)

        prob = policy.copy()
        prob[mask] = -np.inf
        prob -= np.max(prob)
        prob = np.exp(prob) / np.sum(np.exp(prob))

        node.P = prob
        node.mask = mask
        node.is_expansion = True

        return value

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