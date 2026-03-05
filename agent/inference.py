import torch
import numpy as np
from agent.mcts import MCTS

class Agent:
    def __init__(self, encoder, network, model_path=None):
        self.encoder = encoder
        self.network = network
        self.mcts = MCTS(self.encoder, self.network, self.encoder.T)

        if model_path is not None:
            self.network.load_state_dict(torch.load(model_path, weights_only=True))

        network.eval()

    def reset(self):
        self.mcts = MCTS(self.encoder, self.network, self.encoder.T)

    def get_best_action(self, env, history, mode, num_traversal=1000):
        if mode == 'battle':
            if env.turn <= 4:
                pi = self.mcts.get_pi(env, history, alpha=0, epsilon=0, temperature=1, num_traversal=num_traversal)
                best_action = np.random.choice(len(pi), p=pi)

            else:
                pi = self.mcts.get_pi(env, history, alpha=0, epsilon=0, temperature=0, num_traversal=num_traversal)
                best_action = np.argmax(pi)

            win_rate = (self.mcts.root.Q[best_action] + 1.0) / 2.0

        elif mode == 'analyze':
            analyze_mcts = MCTS(self.encoder, self.network, self.encoder.T)
            analyze_mcts.get_pi(env, history, alpha=0, epsilon=0, temperature=0, num_traversal=num_traversal)
            counts = analyze_mcts.root.N
            sorted_indices = np.argsort(counts)[::-1]
            best_actions = [action for action in sorted_indices[:3] if counts[action] > 0]
            win_rates = list((analyze_mcts.root.Q[best_actions] + 1.0) / 2.0)
            return best_actions, win_rates

        elif mode == 'arena':
            temperature = 1 if env.turn < 6 else 0
            pi = self.mcts.get_pi(env, history, alpha=0, epsilon=0, temperature=temperature, num_traversal=num_traversal)
            best_action = np.random.choice(len(pi), p=pi)
            win_rate = (self.mcts.root.Q[best_action] + 1.0) / 2.0

        return best_action, win_rate

    # 플레이어가 수를 두었을 때 Step으로 해당 Action의 노드로 넘어감
    def step(self, action):
        self.mcts.step(action)