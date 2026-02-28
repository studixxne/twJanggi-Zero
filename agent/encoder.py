import torch
import numpy as np
import copy
from collections import deque

FLIP_ACTION = np.array([
92, 93, 94, 95, 88, 89, 90, 91, 84, 85, 86, 87, 80, 81, 82, 83, 76, 77, 78, 79, 
72, 73, 74, 75, 68, 69, 70, 71, 64, 65, 66, 67, 60, 61, 62, 63, 56, 57, 58, 59, 
52, 53, 54, 55, 48, 49, 50, 51, 44, 45, 46, 47, 40, 41, 42, 43, 36, 37, 38, 39, 
32, 33, 34, 35, 28, 29, 30, 31, 24, 25, 26, 27, 20, 21, 22, 23, 16, 17, 18, 19, 
12, 13, 14, 15, 8, 9, 10, 11, 4, 5, 6, 7, 0, 1, 2, 3, 107, 106, 105, 104, 
103, 102, 101, 100, 99, 98, 97, 96, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 
131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 121, 120])

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
        layers.append(np.full((1, 4, 3), turn / 150.00))
        
        # (1, M*T+L, 4, 3)의 텐서 반환
        x = torch.tensor(np.concatenate(layers, axis=0), dtype=torch.float32).unsqueeze(0)
        return x

    def _get_flip_state(self, state, player):
        if player == 1:
            return state
        
        board, taken_piece, king_enter, *remain = state

        flip_board = np.flip(board * -1)
        flip_taken_piece = {-1: taken_piece[1][:],
                            1: taken_piece[-1][:]}
        flip_king_enter = {-1: king_enter[1],
                           1: king_enter[-1]}
        
        return [flip_board, flip_taken_piece, flip_king_enter] + remain
    
    def get_flip_policy(self, policy, player):
        if player == 1:
            return policy
        
        return policy[FLIP_ACTION]