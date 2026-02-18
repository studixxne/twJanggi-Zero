import pygame

from .env import TwJanggiEnv
from .renderer import GameRenderer
from .utils import move_to_action, Piece


class TwJanggiGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.env = TwJanggiEnv()
        self.renderer = GameRenderer()
        self.running = True

        self.info = {
                'highlights_moves': [],
                'selected_taken_piece': Piece.EMPTY,
                'selected_pos': ()
        }

    def run(self):
        while self.running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 0
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.reset()

                    elif event.key == pygame.K_LEFT:
                        pass

                    elif event.key == pygame.K_RIGHT:
                        pass

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_click()

            self.renderer.render(self.env, self.info)
            self.renderer.clock.tick(60)

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
                _, reward, done, info = self.env.step(action)
                self._commit_action()

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

    def _commit_action(self):
        self._reset_selection()
        self.renderer.play_move_sound()