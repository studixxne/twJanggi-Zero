import numpy as np
import copy
from collections import Counter
from .utils import *

class TwJanggiEnv:
    def __init__(self):
        self.rows = 4
        self.cols = 3
        # 0~95: (4, 3) 장기판에서 8가지 방향으로 이동하는 경우의 수
        # 96~131: 자, 장, 상 세 가지 말을 (4, 3) 장기판에 배치하는 경우의 수
        self.action_size = 132
        self.state_counts = Counter()
        self.reset()

    def reset(self):
        self.board = self._get_init_board()
        self.current_player = 1
        self.turn = 0
        self.king_enter = {1:False, -1:False}
        # 자, 상, 장 포로 보유 개수
        self.taken_piece = {1:[0, 0, 0], -1:[0, 0, 0]}
        self.done = False
        self.winner = 0
        self.repeat = 0
        self.state_counts.clear()
        self.state_counts[self._get_hashable_state()] += 1

    def step(self, action):
        self.turn += 1
        move = action_to_move(action)

        # 기물 이동
        if move[0] != -1:
            row, col, next_row, next_col = move
            piece = self.board[row][col]
            next_loc_piece = self.board[next_row][next_col]
            
            # 기물 잡기
            if next_loc_piece != Piece.EMPTY:
                captured = 1 if abs(next_loc_piece) == Piece.HU else abs(next_loc_piece)
                
                # 왕이 잡힌 경우 체크
                if captured == Piece.KING:
                    self.done = True
                else:
                    self.taken_piece[self.current_player][captured-1] += 1

            # 기물 최종 이동
            self.board[next_row][next_col] = piece
            self.board[row][col] = Piece.EMPTY

            # 상대 진영에 들어갔을 때 승진 및 승리 조건 체크
            if self._is_enemy_location(next_row):
                if abs(piece) == Piece.JA:
                    self.board[next_row][next_col] = piece * 4
                elif abs(piece) == Piece.KING:
                    self.king_enter[self.current_player] = True

        # 포로 기물 배치
        else:
            _, piece, next_row, next_col = move
            self.board[next_row][next_col] = piece * self.current_player
            self.taken_piece[self.current_player][piece-1] -= 1

        self.current_player *= -1
        current_hash = self._get_hashable_state()
        self.state_counts[current_hash] += 1
        self.repeat = max(self.repeat, self.state_counts[current_hash] - 1)

        reward = 0
        # 왕을 잡는 것에 성공한 경우 승리
        if self.done:
            reward = 1
            self.winner = -self.current_player
        elif not self.done:
            # 상대가 왕의 기지에서 1턴 버틴 경우 패배
            if self.king_enter[self.current_player]:
                self.done = True
                self.winner = self.current_player
                reward = -1
            # 계속된 수 혹은 천일수 무승부 처리
            elif self.turn >= 150 or self.repeat >= 3:
                self.done = True
                reward = 0

        next_state = self._get_next_state()
        info = {}

        return next_state, reward, self.done, info

    def get_valid_actions(self):
        valid_actions = np.zeros(self.action_size)
        valid_moves = self._get_valid_moves()

        for move in valid_moves:
            action = move_to_action(move)
            valid_actions[action] = 1

        return valid_actions

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
    
    def get_valid_move(self, r, c):
        all_moves = self._get_valid_moves()
        return [m for m in all_moves if m[0] == r and m[1] == c]
    
    def get_valid_place(self, piece):
        all_moves = self._get_valid_moves()
        return [m for m in all_moves if m[0] == -1 and m[1] == piece]

    def _is_enemy_location(self, row):
        if self.current_player == 1 and row == 0: return True
        if self.current_player == -1 and row == 3: return True
        return False
       
    def _get_init_board(self):
        board = np.array(
            [[-Piece.JANG, -Piece.KING, -Piece.SANG],
             [Piece.EMPTY, -Piece.JA, Piece.EMPTY],
             [Piece.EMPTY, Piece.JA, Piece.EMPTY],
             [Piece.SANG, Piece.KING, Piece.JANG]], dtype=np.int8)

        return board
    
    def _get_hashable_state(self):
        board_bytes = self.board.tobytes()
        king_enter = tuple(self.king_enter)
        taken_piece = tuple(self.taken_piece)
        return hash((board_bytes, self.current_player, king_enter, taken_piece))
    
    def copy(self):
        return copy.deepcopy(self)

    def _get_next_state(self):
        # TODO: 다음 상태에 대한 반전된 정보를 전달 (Training)
        pass