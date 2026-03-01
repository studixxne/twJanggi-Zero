from src.utils import action_to_text

class Arena:
    def __init__(self, agent1, agent2, game):
        self.agent1 = agent1
        self.agent2 = agent2
        self.game = game

    def play(self, first=True):
        self.game.reset()
        self.game.render()
        current_agent = self.agent1 if first else self.agent2
        current_turn = 1

        while True:
            history = self.game.get_state_history(current_agent.encoder)
            action, win_rate = current_agent.get_best_action(self.game.env, history, mode='arena')
            print(f'[{current_turn}] {action_to_text(action)} | {win_rate:.2f}%')
            self.game.step(action)
            self.agent1.mcts.step(action)
            self.agent2.mcts.step(action)
            self.game.render()
            current_turn += 1

            done, winner = self.game.is_done()

            if done:
                print(f'{winner} Win!')
                return winner
            
            current_agent = self.agent1 if current_agent == self.agent2 else self.agent2

    def run(self, num_play):
        agent1_win = 0
        agent2_win = 0
        draws = 0

        play_games = num_play // 2

        print(f'⚔️ Arena Start!')

        for _ in range(play_games):
            result = self.play()
            if result == 1:
                agent1_win += 1
            elif result == -1:
                agent2_win += 1
            else:
                draws += 1

        for _ in range(play_games):
            result = self.play(False)
            if result == 1:
                agent2_win += 1
            elif result == -1:
                agent1_win += 1
            else:
                draws += 1

        print("========== Result ==========")
        print(f"Agent 1 Win: {agent1_win}")
        print(f"Agent 2 Win: {agent2_win}")
        print(f"Draw: {draws}")
        print(f"Agent 1 Win Rate: {(agent1_win) / (play_games*2 - draws + 1e-7) * 100:.1f}%")
        print(f"Agent 2 Win Rate: {(agent2_win) / (play_games*2 - draws + 1e-7) * 100:.1f}%")
        print("============================")
        return agent1_win, agent2_win, draws

