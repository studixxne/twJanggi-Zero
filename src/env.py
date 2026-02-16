import numpy as np
from utils import *

class TwJanggiEnv:
    def __init__(self):
        self.rows = 4
        self.cols = 3
        # 0~95: (4, 3) 장기판에서 8가지 방향으로 이동하는 경우의 수
        # 96~131: 자, 장, 상 세 가지 말을 (4, 3) 장기판에 배치하는 경우의 수
        self.action_size = 132
        self.reset()

    def reset(self):
        # TODO: 현재 상태를 초기 상태로 변환
        self.board = self._get_init_board()
        self.current_player = 1

        # 자, 상, 장 포로 보유 개수
        self.taken_piece = {1:[0, 0, 0], -1:[0, 0, 0]}

    def step(self, action):
        # TODO: Action을 수행하고 (next_state, reward, done, info) 반환
        pass

    def get_valid_actions(self):
        # TODO: 현재 상태에서 가능한 Action을 반환
        valid_actions = np.zeros(self.action_size)

    def _get_valid_moves(self):
        # 이동할 수 있는 경우의 수
        valid_moves = []

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] * self.current_player > 0:
                    possible_moves = get_possible_piece_moves(abs(self.board[r][c]), r, c, self.current_player)

                    for row, col, next_row, next_col in possible_moves:
                        if next_row >= self.rows or next_col >= self.cols or next_row < 0 or next_col < 0: 
                            continue
                        
                        if self.board[next_row][next_col] * self.current_player <= 0:
                            valid_moves.append((row, col, next_row, next_col))

                if not self._is_enemy_location(r) and self.board[r][c] == Piece.EMPTY:
                    for piece_type in range(3):
                        if self.taken_piece[self.current_player][piece_type] > 0:
                            valid_moves.append((-1, piece_type+1, r, c))

        return valid_moves

    def _is_enemy_location(self, row):
        if self.current_player == 1 and row == 0: return True
        if self.current_player == -1 and row == 3: return True
        return False
       
    def _get_init_board(self):
        # TODO: 새로운 Board 생성 후 반환
        board = np.array(
            [[-Piece.JANG, -Piece.KING, -Piece.SANG],
             [Piece.EMPTY, -Piece.JA, Piece.EMPTY],
             [Piece.EMPTY, Piece.JA, Piece.EMPTY],
             [Piece.SANG, Piece.KING, Piece.JANG]], dtype=np.int8)

        return board

    def _get_canonical_board():
        # TODO: 반전된 표준 보드 반환
        pass

    def _get_state(self):
        # TODO: 현재 상태를 반환
        pass

    def _get_reward(self):
        # TODO: 현재 상태에서 보상을 계산 및 반환
        pass

    def render(self):
        # TODO: 현재 상태를 출력
        pass