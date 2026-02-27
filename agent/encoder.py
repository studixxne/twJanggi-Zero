import torch
import numpy as np
import copy
from collections import deque

class TwJanggiEncoder:
    def __init__(self, T):
        self.M = 21
        self.L = 2
        self.T = T

    # (1, 4, 3, in_ch)의 Tensor로 변환
    def get_tensor(self, state_list):
        _, _, _, turn, _, player = state_list[-1]
        layers = []

        for state in state_list[::-1]:
            s_board, s_taken_piece, s_king_enter, s_turn, s_repeat, _ = self._get_flip_state(state, player)

            # 내 기물의 위치 / 상대 기물의 위치 (10개)            
            target_piece = np.array([1, 2, 3, 4, 5, -1, -2, -3, -4, -5]).reshape(10, 1, 1)
            layers.append((s_board == target_piece).astype(np.float32))

            # 내 포로 개수 / 상대 포로 개수 (6개)
            taken_array = np.array(s_taken_piece[1] + s_taken_piece[-1]).reshape(6, 1, 1)
            layers.append(np.broadcast_to(taken_array, (6, 4, 3)))

            repeat_array = np.zeros((3, 1, 1))
            repeat_array[s_repeat, 0, 0] = 1.0
            layers.append(np.broadcast_to(repeat_array, (3, 4, 3)))

            king_enter_array = np.array((s_king_enter[1], s_king_enter[-1]), dtype=np.float32).reshape(2, 1, 1)
            layers.append(np.broadcast_to(king_enter_array, (2, 4, 3)))

        layers.append(np.zeros((self.M*(self.T-len(state_list)), 4, 3)))

        # 누구의 턴 (레드(선공) 플레이어면 0, 초록(후공) 플레이어면 1)
        layers.append(np.zeros((1, 4, 3)) if player == 1 else np.ones((1, 4, 3)))
        # 총 이동 수
        layers.append(np.full((1, 4, 3), turn))
        
        # (1, M*T+L, 4, 3)의 텐서 반환
        x = torch.tensor(np.concatenate(layers, axis=0), dtype=torch.float32).unsqueeze(0)
        return x

    def _get_flip_state(self, state, player):
        if player == 1:
            return state
        
        board, taken_piece, king_enter, *remain = state

        flip_board = np.flip(board * -1)
        flip_taken_piece = {-1: copy.deepcopy(taken_piece[1]),
                            1: copy.deepcopy(taken_piece[-1])}
        flip_king_enter = {-1: king_enter[1],
                           1: king_enter[-1]}
        
        return [flip_board, flip_taken_piece, flip_king_enter] + remain