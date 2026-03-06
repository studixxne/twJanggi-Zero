from agent.encoder import TwJanggiEncoder
from agent.network import TwJanggiNet
from agent.inference import Agent

from src.game import TwJanggiGame

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="TwJanggi Analyze")

    parser.add_argument('--model', type=str, default='model/master_model.pth', help='Model path ex) model/model.pth')
    parser.add_argument('--T', type=int, default=4, help='Model Time step')
    parser.add_argument('--hidden_ch', type=int, default=128, help='Model Hidden ch')
    parser.add_argument('--num_block', type=int, default=4, help='Model Residual block num')

    parser.add_argument('--num_deep_traversal', type=int, default=5000, help='Hint MCTS Deep Traversal num')
    parser.add_argument('--num_traversal', type=int, default=1000, help='Hint MCTS Traversal num')

    args = parser.parse_args()

    encoder = TwJanggiEncoder(args.T)
    network = TwJanggiNet(args.T*21+2, args.hidden_ch, args.num_block)
    agent = Agent(encoder, network, model_path=args.model)
    
    game = TwJanggiGame(agent=agent, mode='analyze', num_traversal=args.num_traversal, num_deep_traversal=args.num_deep_traversal)
    game.run()