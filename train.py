from agent.trainer import Trainer

if __name__ == '__main__':
    import multiprocessing
    import argparse

    multiprocessing.set_start_method('spawn', force=True)

    parser = argparse.ArgumentParser(description="AlphaZero TwJanggi train code")

    parser.add_argument('--iter', type=int, default=300, help='total training iteration num')
    parser.add_argument('--num_play', type=int, default=30, help='self play games num per iter')
    parser.add_argument('--num_traversal', type=int, default=1000, help='MCTS traversal num')

    parser.add_argument('--T', type=int, default=4, help='Time step')
    parser.add_argument('--hidden_ch', type=int, default=128, help='hidden chanal num')
    parser.add_argument('--num_block', type=int, default=4, help='residual block num')
    
    parser.add_argument('--c_puct', type=float, default=2.0, help='c_puct')
    parser.add_argument('--alpha', type=float, default=0.6, help='Noise alpha')
    parser.add_argument('--epsilon', type=float, default=0.25, help='Noise epsilon')
    
    parser.add_argument('--batch_size', type=int, default=128, help='batch size')
    parser.add_argument('--c', type=float, default=1e-4, help='weight decay')
    parser.add_argument('--load_model', type=str, default=None, help='load_model path')

    args = parser.parse_args()

    print("=" * 30)
    print("Training Setting")
    print("=" * 30)
    for key, value in vars(args).items():
        print(f"[{key}]: {value}")
    print("=" * 30)

    trainer = Trainer(
        num_play=args.num_play,
        num_traversal=args.num_traversal,
        T=args.T,
        hidden_ch=args.hidden_ch,
        num_block=args.num_block,
        c_puct=args.c_puct,
        alpha=args.alpha,
        epsilon=args.epsilon,
        batch_size=args.batch_size,
        c=args.c
    )

    trainer.train(iter=args.iter, load_model=args.load_model)