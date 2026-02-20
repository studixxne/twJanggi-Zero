import numpy as np

class Node:
    def __init__(self, env):
        self.state = env
        self.n = 0
        self.v = 0
        self.parent = None
        self.childs = []
        self.is_terminal = False
        self.action = None
        self.reward = 0

    def get_ucb(self):
        if self.n == 0:
            return float('inf')

        q = -self.v / self.n
        u = np.sqrt(2 * np.log(self.parent.n) / self.n)
        return q + u

class MCTS:
    def __init__(self, env):
        self.root = Node(env.copy())

    def traversal(self):
        cur = self.root

        # Leaf Node 찾기
        while cur.childs: 
            cur = self._select_node(cur)

        # Terminal Node에 도달 시 바로 Backpropagation
        if cur.is_terminal:
            reward = cur.reward

        # 처음 방문한 노드일 때 Rollout 수행
        elif cur.n == 0:
            reward = self.rollout(cur)

        # 이미 방문해본 노드일 때 Expansion 수행
        else:
            self.expansion(cur)
            cur = cur.childs[0]
            reward = cur.reward if cur.is_terminal else self.rollout(cur)

        self.backpropagation(cur, reward)

    def _select_node(self, cur):
        max_ucb = float('-inf')
        target = None

        for node in cur.childs:
            ucb = node.get_ucb()
            if ucb > max_ucb:
                target = node
                max_ucb = ucb

        return target

    def expansion(self, node):
        all_actions = node.state.get_valid_actions()
        all_action_indices = np.where(all_actions == 1)[0]

        for action in all_action_indices:
            state = node.state.copy()
            next_state, reward, done, info = state.step(action)
            new_node = Node(state.copy())
            new_node.action = action
            new_node.parent = node
            node.childs.append(new_node)

            # Expansion 도중 Terminal Node인 경우 바로 Backpropagation
            if done:
                new_node.is_terminal = True
                new_node.reward = -reward

    def rollout(self, node):
        env = node.state.copy()

        while not env.done:
            all_actions = env.get_valid_actions()
            random_action = np.random.choice(np.where(all_actions == 1)[0])
            next_state, reward, done, info = env.step(random_action)

        # Rollout을 시작한 시점의 Player를 기준으로 Reward를 갱신
        # 해당 수를 둔 플레이어가 승리할 시 1, 패배할 시 -1
        winner = env.winner
        player = node.state.current_player

        if winner == player:
            return 1
        elif winner == -player:
            return -1
        else:
            return 0

    def backpropagation(self, node, reward):
        cur = node
        while cur is not None:
            cur.v += reward
            cur.n += 1
            cur = cur.parent
            reward = -reward

    def get_action(self, num_simulations=1000):
        for _ in range(num_simulations):
            self.traversal()

        best_child = max(self.root.childs, key=lambda c: c.n)
        return best_child.action