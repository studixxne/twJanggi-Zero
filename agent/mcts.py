import torch
import numpy as np
from collections import deque

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
    def __init__(self, encoder, network, T):
        self.root = Node(None, None)
        self.encoder = encoder
        self.network = network
        self.T = T

    def traversal(self, env, history):
        env = env.copy()
        cur = self.root
        search_history = deque(history, maxlen=self.T)

        # Leaf Node를 찾도록 함
        while cur.is_expansion:
            action = cur.get_U()

            if not action in cur.childs:
                cur.childs[action] = Node(cur, action)

            state, reward, done, info = env.step(action)
            search_history.append(state)
            cur = cur.childs[action]

        # Terminal Node가 아닌 경우에는 Expansion을 진행
        if not done:            
            value = -self.expansion(cur, env, search_history)

        # Terminal Node인 경우에는 그냥 Reward 가져옴
        else:
            value = reward

        # 얻어낸 Value를 기반으로 Backpropagation 수행
        self.backpropagation(cur, value)

    def expansion(self, node, env, history):
        state_tensor = self.encoder.get_tensor(list(history))

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

    def step(self, action):
        if action in self.root.childs:
            self.root = self.root.childs[action]
            self.root.parent = None
        else:
            self.root = Node(None, None)

    def get_pi(self, env, history, alpha=0.3, epsilon=0.25, temperature=1, num_traversal=700):
        if not self.root.is_expansion:
            self.expansion(self.root, env, history)

        # dirichlet 노이즈 추가
        valid_actions = env.get_valid_actions()
        valid_actions_indices = np.where(valid_actions == 1)[0]
        noise = np.random.dirichlet([alpha] * np.sum(valid_actions, dtype=np.int8))

        for i, action in enumerate(valid_actions_indices):
            self.root.P[action] = self.root.P[action] * (1-epsilon) + epsilon * noise[i]

        # MCTS 확장
        for _ in range(num_traversal):
            self.traversal(env, history)

        # pi 반환
        if temperature > 1e-3:
            N = self.root.N ** (1.0 / temperature)
            pi = N / np.sum(N)
        
        else:
            pi = np.zeros(132, dtype=np.float32)
            pi[np.argmax(self.root.N)] = 1.0
        
        return pi