from agent.encoder import TwJanggiEncoder
from agent.network import TwJanggiNet
from agent.inference import Agent
from src.game import TwJanggiGame

class Arena:
    def __init__(self, agent1, agent2, game, num_traversal):
        self.agent1 = agent1
        self.agent2 = agent2
        self.game = game
        self.num_traversal = num_traversal

    def play(self, first=True):
        self.game.reset()
        self.game.render()
        current_agent = self.agent1 if first else self.agent2
        current_turn = 1

        while True:
            history = self.game.get_state_history(current_agent.encoder)

            if current_agent.is_pure:
                action = current_agent.get_pure_mcts_action(self.game.env, self.num_traversal)
            else:
                action, win_rate = current_agent.get_best_action(self.game.env, history, mode='arena', num_traversal=self.num_traversal)

            self.game.step(action)
            self.agent1.step(action)
            self.agent2.step(action)
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
        print(f"Agent 1 Win Rate: {(agent1_win) / (play_games*2 - draws + 1e-7) * 100:.2f}%")
        print(f"Agent 2 Win Rate: {(agent2_win) / (play_games*2 - draws + 1e-7) * 100:.2f}%")
        print("============================")
        return agent1_win, agent2_win, draws
    
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="TwJanggi Arena (Model Performance Test)")

    parser.add_argument('--model1', type=str, default=None, help='Agent1 Model path ex) model/model1.pth, if model1 is None then PureMCTS')
    parser.add_argument('--model2', type=str, default=None, help='Agent2 Model path ex) model/model2.pth, if model2 is None then PureMCTS')

    parser.add_argument('--num_games', type=int, default=30, help='total games')
    parser.add_argument('--num_traversal', type=int, default=1000, help='MCTS traversal num')
    
    parser.add_argument('--T1', type=int, default=4, help='Model1 Time step')
    parser.add_argument('--hidden_ch1', type=int, default=128, help='Model1 Hidden ch')
    parser.add_argument('--num_block1', type=int, default=4, help='Model1 Residual block num')

    parser.add_argument('--T2', type=int, default=4, help='Model2 Time step')
    parser.add_argument('--hidden_ch2', type=int, default=128, help='Model2 Hidden ch')
    parser.add_argument('--num_block2', type=int, default=4, help='Model2 Residual block num')

    args = parser.parse_args()

    encoder1 = TwJanggiEncoder(args.T1)
    network1 = TwJanggiNet(args.T1*21+2, args.hidden_ch1, args.num_block1)
    agent1 = Agent(encoder1, network1, model_path=args.model1)

    encoder2 = TwJanggiEncoder(args.T2)
    network2 = TwJanggiNet(args.T2*21+2, args.hidden_ch2, args.num_block2)
    agent2 = Agent(encoder2, network2, model_path=args.model2)
    
    game = TwJanggiGame(mode='arena')
    arena = Arena(agent1, agent2, game, num_traversal=args.num_traversal)

    arena.run(args.num_games)