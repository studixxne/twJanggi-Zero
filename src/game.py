import pygame
import threading

from .env import TwJanggiEnv
from .renderer import GameRenderer
from .utils import move_to_action, action_to_text, action_to_move, Piece

class TwJanggiGame:
    def __init__(self, agent=None, mode='battle', agent_turn=1, num_traversal=1000, num_deep_traversal=10000):
        self.renderer = GameRenderer()
        self.agent = agent
        self.mode = mode
        self.num_traversal = num_traversal
        self.num_deep_traversal = num_deep_traversal
        self.agent_turn = agent_turn
        self.reset()

    def reset(self):
        self.env = TwJanggiEnv()
        self.running = True

        self.history = [self.env.copy()]
        self.history_cursor = 0
        self.win_rate_history = []
        self.is_evaluating = False

        self.info = {
                'highlights_moves': [],
                'selected_taken_piece': Piece.EMPTY,
                'selected_pos': (),
                'best_action': None,
                'win_rate': 0.5 if self.mode == 'analyze' else None
        }

        if self.agent is not None:
            self.agent.reset()

        if self.mode == 'analyze':
            self._agent_eval(num_traversal=self.num_traversal)

    def run(self):
        while self.running:
            self.renderer.render(self.env, self.info)
            self.renderer.clock.tick(60)

            if self.mode == 'battle' and self.agent_turn == self.env.current_player and not self.env.done:
                best_action, win_rate = self._agent_eval(num_traversal=self.num_traversal)
                self.step(best_action)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 0
                
                if event.type == pygame.KEYDOWN and not self.is_evaluating:
                    if event.key == pygame.K_ESCAPE:
                        self.reset()

                    elif event.key == pygame.K_LEFT and self.mode == 'analyze':
                        self._shift_history(-1)

                    elif event.key == pygame.K_RIGHT and self.mode == 'analyze':
                        self._shift_history(1)

                    # 더 깊은 탐색
                    elif event.key == pygame.K_SPACE and self.mode == 'analyze':
                        self._agent_eval(num_traversal=self.num_deep_traversal)

                if event.type == pygame.MOUSEBUTTONDOWN and not self.env.done and not self.is_evaluating:
                    self._handle_mouse_click()

    def _handle_mouse_click(self):
        m_pos = pygame.mouse.get_pos()
        handle = self._get_handle_mouse(m_pos)

        if handle is None:
            self._reset_selection()
            return
        
        pos, t = handle

        # 보드판를 눌렀을 때
        if t == 'board':
            self._handle_board_click(pos)

        # 포로 보드판을 눌렀을 때
        elif t == 'taken_board':
            self._handle_taken_board_click(pos)
        
        # 선택 초기화
        else:
            self._reset_selection()

    # 말 이동 및 배치 수행
    def _handle_board_click(self, pos):
        target_move = None
        for move in self.info['highlights_moves']:
            if pos == (move[2], move[3]):
                target_move = move

        # 실제 이동하는 경우
        if target_move is not None:
                action = move_to_action(target_move)
                self.step(action)

        # 말을 선택하는 경우
        else:
            row, col = pos
            piece = self.env.board[row][col]
            if self.env.current_player * piece > 0:
                self.info['highlights_moves'] = self.env.get_valid_move(row, col)
                self.info['selected_taken_piece'] = Piece.EMPTY
                self.info['selected_pos'] = pos

            else:
                self._reset_selection()
                
    # 어떤 포로를 설치할 지 설정
    def _handle_taken_board_click(self, pos):
        row, col = pos
        current_player = self.env.current_player
        idx = row*2 + col
        acc = 0
        for i, v in enumerate(self.env.taken_piece[current_player]):
            acc += v
            if idx < acc:
                self.info['selected_taken_piece'] = i+1
                self.info['highlights_moves'] = self.env.get_valid_place(self.info['selected_taken_piece'])
                self.info['selected_pos'] = pos
                break

    def _get_handle_mouse(self, m_pos):
        current_player = self.env.current_player
        board_area = self.renderer.BOARD_AREA
        taken_board_area = self.renderer.TAKEN_BOARD_AREA[current_player]
        cell_size = self.renderer.CELL_SIZE
        taken_cell_size = self.renderer.TAKEN_CELL_SIZE

        if board_area.collidepoint(m_pos):
            row = (m_pos[1] - board_area.y) // cell_size
            col = (m_pos[0] - board_area.x) // cell_size
            return (row, col), 'board'
        
        if taken_board_area.collidepoint(m_pos):
            row = (m_pos[1] - taken_board_area.y) // taken_cell_size
            col = (m_pos[0] - taken_board_area.x) // taken_cell_size
            return (row, col), 'taken_board'
        
        return None
    
    def _reset_selection(self):
        self.info['highlights_moves'] = []
        self.info['selected_taken_piece'] = Piece.EMPTY
        self.info['selected_pos'] = ()

    def _shift_history(self, direction):
        if direction == -1 and self.history_cursor == 0:
            return
        
        if direction == 1 and self.history_cursor == len(self.history)-1:
            return
        
        self.history_cursor += direction
        self.env = self.history[self.history_cursor].copy()
        self._reset_selection()
        self.renderer.play_move_sound()
        self.info['best_action'] = None
        self.info['win_rate'] = self.win_rate_history[self.history_cursor]

    def _commit_action(self):
        self._reset_selection()
        self.renderer.play_move_sound()
        self.info['best_action'] = None

        if self.history_cursor != len(self.history)-1:
            self.history = self.history[:self.history_cursor+1]
            self.win_rate_history = self.win_rate_history[:self.history_cursor+1]
        
        self.history.append(self.env.copy())
        self.history_cursor += 1

        if self.mode == 'analyze':
            self._agent_eval(num_traversal=self.num_traversal)

    def is_done(self):
        if self.env.done:
            return (True, self.env.winner)
        
        else:
            return (False, None)
        
    def step(self, action):
        self.env.step(action)
        print(f"[{self.env.turn}] {action_to_text(action)}")

        if self.mode == 'battle' and self.agent is not None:
            self.agent.step(action)

        self._commit_action()

    def get_state_history(self, encoder):
        return [h.get_state() for h in self.history[max(0, self.history_cursor-encoder.T+1):self.history_cursor+1]]
    
    def render(self):
        self.renderer.render(self.env, self.info)

    def _agent_eval(self, num_traversal=1000):
        if self.agent is None:
            return
        
        if self.env.done:
            self.info['win_rate'] = 1 if self.env.winner == -1 else 0
            self.win_rate_history.append(self.info['win_rate'])
            return
        
        self.is_evaluating = True
        result = []

        def eval():
            state_history = self.get_state_history(self.agent.encoder)
            best_action, win_rate = self.agent.get_best_action(self.env, state_history, self.mode, num_traversal)
            result.append((best_action, win_rate))

        thread = threading.Thread(target=eval)
        thread.start()

        while thread.is_alive():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            self.renderer.render(self.env, self.info)
            self.renderer.clock.tick(60)

        self.is_evaluating = False
        best_action, win_rate = result[0]

        if self.mode == 'battle':
            print(f"\n=============== [{self.env.turn+1}] Moves Best Action ================")
            print(f"Action: {action_to_text(best_action)} | (Win Rate: {win_rate * 100:.2f}%)")
            print(f"======================================================")

        elif self.mode == 'analyze':
            print(f"\n=============== [{self.env.turn+1}] Moves Best Action ================")
            for i in range(1, len(best_action)+1):
                print(f"Top {i}: {action_to_text(best_action[i-1])} | Win Rate: {win_rate[i-1] * 100:.2f}%")
            print(f"======================================================")
            self.info['best_action'] = action_to_move(best_action[0])
            self.info['win_rate'] = win_rate[0] if self.env.current_player == -1 else 1-win_rate[0]
            self.win_rate_history.append(self.info['win_rate'])

        return best_action, win_rate