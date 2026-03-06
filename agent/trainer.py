import torch
from torch.optim import Adam
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
import json
import concurrent.futures

from src.env import TwJanggiEnv
from agent.encoder import TwJanggiEncoder
from agent.network import TwJanggiNet
from agent.mcts import MCTS
from collections import deque

class SelfPlay:
    def __init__(self, T, encoder, network):
        self.encoder = encoder
        self.network = network
        self.T = T

    def play(self, num_traversal):
        torch.set_num_threads(1)
        rng = np.random.default_rng()

        local_env = TwJanggiEnv()
        history = deque(maxlen=self.T)
        state = local_env.get_state()
        history.append(state)

        mcts = MCTS(self.encoder, self.network, self.T)
        data = []

        while True:
            # 일정 턴수 이상부터 탐색 보너스 제거
            if local_env.turn < 20:
                temperature = 1
            else:
                temperature = 0

            # 현재 상태에서 MCTS를 통해 얻어 낸 pi 받아오기
            pi = mcts.get_pi(local_env, history, num_traversal=num_traversal, temperature=temperature)
            # Network는 항상 1번 플레이어 기준으로 학습함으로 학습용 데이터는 -1번 플레이어면 반전시켜준다
            target_pi = self.encoder.get_flip_policy(pi, local_env.current_player)

            # state_tensor와 pi를 Training Data에 저장
            state_tensor = self.encoder.get_tensor(list(history)).detach().cpu()
            data.append([state_tensor, target_pi])

            # 다음 Action 선택 및 Step 이후 History 기록
            action = rng.choice(np.arange(132), p=pi)
            state, reward, done, info = local_env.step(action)
            mcts.step(action)
            history.append(state)

            # 종료 시 reward 저장 후 Episode 종료
            if done:
                z = reward
                break

        # Episode 결과를 Data에 추가
        for h in data[::-1]:
            h.append(z)
            z *= -1

        return data
    
    def run(self, dataset, num_play, num_traversal):
        self.network.eval()
        self.network.to('cpu')

        episode = 0
        results = []

        print(f'=============== Self Playing ===============')
        with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.play, num_traversal) for _ in range(num_play)]

            for future in concurrent.futures.as_completed(futures):
                data = future.result()
                dataset.extend(data)

                result = data[-1][-1]
                turns = len(data)
                winner = 1 if (turns % 2 != 0 and result == 1) or (turns % 2 == 0 and result == -1) else -1
                if result == 0: 
                    winner = 0
                episode += 1
                results.append(winner)

        w1, w2, draw = results.count(1), results.count(-1), results.count(0)
        print(f'=========== Self Playing Results ===========')
        print(f'Red: {w1} Win | Green: {w2} Win | Draw: {draw}')
        print(f'Red Win Rate: {w1/(num_play-draw+1e-6)*100:.1f}% | Green Win Rate: {w2/(num_play-draw+1e-6)*100:.1f}% | Draw {draw/num_play*100+1e-6:.1f}%')
        print("=" * 44)

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
    def __init__(self, num_play=100, num_traversal=1000, T=4, hidden_ch=128, num_block=4, c_puct=2, alpha=0.6, epsilon=0.25, batch_size=128, c=1e-4, lr=1e-3):
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
        self.lr = lr

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.mps.is_available() else 'cpu')
        self.encoder = TwJanggiEncoder(self.T)
        self.network = TwJanggiNet(self.T*21+2, self.hidden_ch, self.num_block).to(self.device)
        self.player = SelfPlay(self.T, self.encoder, self.network)
        self.dataset = deque(maxlen=100000)

        self.optimizer = Adam(self.network.parameters(), lr=self.lr, weight_decay=self.c)
        self.loss_fn = LossFunc()

    def train(self, iter, load_model=None):
        loss_history = []
        if load_model is not None:
            try:
                state_dict = torch.load(load_model)
                self.network.load_state_dict(state_dict)
                print("Load Success!")
            except FileNotFoundError:
                print("Load Fail!")

        for i in range(iter):
            self.player.run(self.dataset, self.num_play, self.num_traversal)
            self.network.train()
            self.network.to(self.device)
            total_loss = 0

            for _ in range(len(self.dataset) // self.batch_size):
                state, pi, z = self._get_mini_batch(self.dataset, self.batch_size)
                p, v = self.network(state)
                loss = self.loss_fn(z, v, pi, p)
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
            
            loss_history.append(total_loss / (len(self.dataset) // self.batch_size))
            print(f'[{i+1}/{iter}] Loss: {loss_history[-1]}')

            if (i+1)% 10 == 0:
                checkpoint_path = f'data/model_iter{i+1}.pth'
                checkpoint_loss_path = f'data/loss_iter{i+1}.json'
                torch.save(self.network.state_dict(), checkpoint_path)
                print(f'Checkpoint Save: {checkpoint_path}')
                with open(checkpoint_loss_path, 'w') as f:
                    json.dump(loss_history, f)

    def _get_mini_batch(self, dataset, batch_size):
        datas = random.sample(dataset, batch_size)

        state, pi, z = map(np.array, zip(*datas))

        state_tensor = torch.FloatTensor(state.squeeze(1)).to(self.device) # (Batch, in_ch, Row, Col)
        pi_tensor = torch.FloatTensor(pi).to(self.device) # (Batch, Action_Size)
        z_tensor = torch.FloatTensor(z).unsqueeze(1).to(self.device) # (Batch, 1)

        return state_tensor, pi_tensor, z_tensor