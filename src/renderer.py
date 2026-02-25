import pygame
import random
import os
from .utils import Piece


class GameRenderer:
    def __init__(self):
        self.SCREEN_WIDTH = 1440
        self.SCREEN_HEIGHT = 780

        self.CELL_SIZE = 150
        self.TAKEN_CELL_SIZE = 90
        self.PIECE_SIZE = 140
        self.TAKEN_PIECE_SIZE = 80

        self.BOARD_WIDTH = self.CELL_SIZE * 3
        self.BOARD_HEIGHT = self.CELL_SIZE * 4
        self.TAKEN_BOARD_WIDTH = self.TAKEN_CELL_SIZE * 2
        self.TAKEN_BOARD_HEIGHT = self.TAKEN_CELL_SIZE * 3

        self.BOARD_X = 400
        self.BOARD_Y = 150
        self.TAKEN_BOARD_X = 110
        self.TAKEN_BOARD_Y = 150
        self.TAKEN_BOARD_POS = {
            1: (self.TAKEN_BOARD_X, self.TAKEN_BOARD_Y + self.BOARD_HEIGHT - self.TAKEN_CELL_SIZE * 3),
            -1: (self.TAKEN_BOARD_X, self.TAKEN_BOARD_Y)
        }

        self.BLACK_COLOR = (33, 33, 33, 97)
        self.WINDOW_COLOR = (74, 74, 74, 180)
        self.LINE_COLOR = (240, 234, 214, 100)

        self.TEAM_COLOR = {1: (204, 61, 61), -1: (65, 175, 57)}

        # 초기화
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.screen.fill(self.BLACK_COLOR)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption('twJanggi')


        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self._load_images()
        self._load_fonts()
        self._load_sounds()
        self._create_components()

    def render(self, env, info):
        self.screen.fill(self.BLACK_COLOR)
        self._draw_board()
        self._draw_select_piece(env, info)
        self._draw_pieces(env)
        self._draw_highlights(env, info)
        self._draw_ui(env)

        pygame.display.update()
    
    def _draw_board(self):
        # 보드판 표시
        self.screen.blit(self.board_images['board'], (self.BOARD_X, self.BOARD_Y))

        # 진영 색 표시
        self.screen.blit(self.red_team_surface, (self.BOARD_X, self.BOARD_Y + self.BOARD_HEIGHT - self.CELL_SIZE))
        self.screen.blit(self.green_team_surface, (self.BOARD_X, self.BOARD_Y))

        # 격자 표시
        for row in range(5):
            pygame.draw.line(self.screen, self.BLACK_COLOR, (self.BOARD_X, self.BOARD_Y + row * self.CELL_SIZE),
                             (self.BOARD_X + 3 * self.CELL_SIZE, self.BOARD_Y + row * self.CELL_SIZE),
                             3 if row == 0 or row == 4 else 2)

        for col in range(4):
            pygame.draw.line(self.screen, self.BLACK_COLOR, (self.BOARD_X + col * self.CELL_SIZE, self.BOARD_Y),
                             (self.BOARD_X + col * self.CELL_SIZE, self.BOARD_Y + 4 * self.CELL_SIZE),
                             3 if col == 0 or col == 3 else 2)

        # 잡힌 기물 보드판 표시
        self.screen.blit(self.board_images['red'], self.red_taken_board_rect)
        self.screen.blit(self.board_images['green'], self.green_taken_board_rect)
        pygame.draw.rect(self.screen, self.TEAM_COLOR[1], self.red_taken_board_rect, 3)
        pygame.draw.rect(self.screen, self.TEAM_COLOR[-1], self.green_taken_board_rect, 3)

        # 보드판 좌표 표시
        for row in range(4):
            self.screen.blit(self.row_coord_surface[row], (self.BOARD_X - 20, self.BOARD_Y + row * self.CELL_SIZE + 70))

        for col in range(3):
            self.screen.blit(self.col_coord_surface[col], (self.BOARD_X + col * self.CELL_SIZE + 70, self.BOARD_Y + self.BOARD_HEIGHT + 7))


    def _draw_select_piece(self, env, info):
        # 선택된 말 표시
        selected_taken_piece = info['selected_taken_piece']
        selected_pos = info['selected_pos']

        if not selected_pos:
            return

        if selected_taken_piece == Piece.EMPTY:
            self.screen.blit(self.highlight_selected, (self.BOARD_X + selected_pos[1] * self.CELL_SIZE, self.BOARD_Y + selected_pos[0] * self.CELL_SIZE))
        elif selected_taken_piece != Piece.EMPTY:
            self.screen.blit(self.highlight_taken_selected, 
                             (self.TAKEN_BOARD_POS[env.current_player][0] + selected_pos[1] * self.TAKEN_CELL_SIZE,
                              self.TAKEN_BOARD_POS[env.current_player][1] + selected_pos[0] * self.TAKEN_CELL_SIZE))

    def _draw_pieces(self, env):
        for row in range(env.rows):
            for col in range(env.cols):
                piece = env.board[row][col]
                if piece != Piece.EMPTY:
                    t = abs(piece)
                    p = piece // t
                    rect = self.piece_images[(p, t)].get_rect()
                    rect.center = (self.BOARD_X + col * self.CELL_SIZE + self.CELL_SIZE // 2, self.BOARD_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2)

                    self.screen.blit(self.piece_images[(p, t)], rect)

                    if t != Piece.KING:
                        pygame.draw.rect(self.screen, self.TEAM_COLOR[p], rect, 3)

        for p, v_list in env.taken_piece.items():
            cur = 0
            for t, v in enumerate(v_list):
                for _ in range(v):
                    rect = self.taken_piece_images[(p, (t+1))].get_rect()
                    rect.center = (self.TAKEN_BOARD_POS[p][0] + (cur % 2) * self.TAKEN_CELL_SIZE + self.TAKEN_CELL_SIZE // 2,
                                   self.TAKEN_BOARD_POS[p][1] + (cur // 2) * self.TAKEN_CELL_SIZE + self.TAKEN_CELL_SIZE // 2)
                    self.screen.blit(self.taken_piece_images[(p, t+1)], rect)
                    cur += 1

    def _draw_highlights(self, env, info):
        highlight_moves = info['highlights_moves']

        if highlight_moves:
            for row, col, next_row, next_col in highlight_moves:
                hx, hy = (self.BOARD_X + next_col * self.CELL_SIZE + self.CELL_SIZE // 2, self.BOARD_Y + next_row * self.CELL_SIZE + self.CELL_SIZE // 2)

                if env.board[next_row][next_col] == Piece.EMPTY:
                    t_rect = self.highlights_move_circle.get_rect(center=(hx, hy))
                    self.screen.blit(self.highlights_move_circle, t_rect)

                else:
                    t_rect = self.highlights_catch_circle.get_rect(center=(hx, hy))
                    self.screen.blit(self.highlights_catch_circle, t_rect)

    def _draw_ui(self, env):
        pygame.draw.line(self.screen, self.LINE_COLOR, (0, 100), (self.SCREEN_WIDTH, 100), 2)
        self.screen.blit(self.background_text_surface, (0, 0))

        # 텍스트 생성
        round_text = f'{(env.turn + 1) // 2} moves'
        turn_text = ''
        add_text = ''

        if env.done:
            if env.winner == 1:
                turn_text = 'Red Win!'
            elif env.winner == -1:
                turn_text = 'Green Win!'
            else:
                turn_text = 'Draw!'

            if env.winner != 0:
                if env.king_enter[env.winner]:
                    add_text = "The player's king stayed in the enemy's territory for a round"
                else:
                    add_text = "The player captures the enemy's king"

            elif env.winner == 0:
                if env.repeat >= 3:
                    add_text = "Threefold Repetition"
                else:
                    add_text = "Exceed limited moves"

        else:
            # 누구의 턴인지 표시
            if env.current_player == 1:
                turn_text = 'Red Turn'
            else:
                turn_text = 'Green Turn'

        # 턴 설명
        turn_text_surface = self.ui_font.render(turn_text, True, (255, 255, 255))
        turn_text_rect = turn_text_surface.get_rect()
        turn_text_rect.center = (self.SCREEN_WIDTH // 2, 40)
        self.screen.blit(turn_text_surface, turn_text_rect)

        # 추가 상황 설명
        add_text_surface = self.ui_sub_font.render(add_text, True, (255, 255, 255))
        add_text_rect = add_text_surface.get_rect()
        add_text_rect.center = (self.SCREEN_WIDTH // 2, 70)
        self.screen.blit(add_text_surface, add_text_rect)

        round_text_surface = self.ui_sub_font.render(round_text, True, (255, 255, 255))
        round_rect = round_text_surface.get_rect()
        round_rect.center = (60, 80)
        self.screen.blit(round_text_surface, round_rect)

    def play_move_sound(self):
        self.sounds[random.randint(0, 3)].play()

    def _load_images(self):
        image_path = os.path.join(self.base_path, '..', 'assets', 'images')
        try:
            images = {
                'board': pygame.image.load(os.path.join(image_path, 'board_image.jpg')),
                'red_king': pygame.image.load(os.path.join(image_path, 'RED_KING.jpg')),
                'green_king': pygame.image.load(os.path.join(image_path, 'GREEN_KING.jpg')),
                'ja': pygame.image.load(os.path.join(image_path, 'JA.jpg')),
                'sang': pygame.image.load(os.path.join(image_path, 'SANG.jpg')),
                'jang': pygame.image.load(os.path.join(image_path, 'JANG.jpg')),
                'hu': pygame.image.load(os.path.join(image_path, 'HU.jpg'))
            }

        except pygame.error as e:
            print(f'Image file load fail: {e}')
            pygame.quit()
            exit()
        
        for key, val in images.items():
            images[key] = val.convert()

        self.board_images = {
            'board': pygame.transform.smoothscale(pygame.transform.rotate(images["board"], 90), (self.BOARD_WIDTH, self.BOARD_HEIGHT)),
            "red": pygame.transform.smoothscale(pygame.transform.rotate(images["board"], 270), (self.TAKEN_BOARD_WIDTH, self.TAKEN_BOARD_HEIGHT)),
            "green": pygame.transform.smoothscale(pygame.transform.rotate(images["board"], 90), (self.TAKEN_BOARD_WIDTH, self.TAKEN_BOARD_HEIGHT))
        }

        self.piece_images = {
            (1, Piece.KING): pygame.transform.smoothscale(images["red_king"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (1, Piece.JA): pygame.transform.smoothscale(images["ja"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (1, Piece.SANG): pygame.transform.smoothscale(images["sang"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (1, Piece.JANG): pygame.transform.smoothscale(images["jang"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (1, Piece.HU): pygame.transform.smoothscale(images["hu"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.KING): pygame.transform.smoothscale(pygame.transform.rotate(images["green_king"], 180), (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.JA): pygame.transform.smoothscale(pygame.transform.rotate(images["ja"], 180), (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.SANG): pygame.transform.smoothscale(pygame.transform.rotate(images["sang"], 180), (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.JANG): pygame.transform.smoothscale(pygame.transform.rotate(images["jang"], 180), (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.HU): pygame.transform.smoothscale(pygame.transform.rotate(images["hu"], 180), (self.PIECE_SIZE, self.PIECE_SIZE))
        }

        self.taken_piece_images = {
            (1, Piece.JA): pygame.transform.smoothscale(images["ja"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (1, Piece.SANG): pygame.transform.smoothscale(images["sang"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (1, Piece.JANG): pygame.transform.smoothscale(images["jang"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (-1, Piece.JA): pygame.transform.smoothscale(pygame.transform.rotate(images["ja"], 180), (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (-1, Piece.SANG): pygame.transform.smoothscale(pygame.transform.rotate(images["sang"], 180), (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (-1, Piece.JANG): pygame.transform.smoothscale(pygame.transform.rotate(images["jang"], 180), (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE))
        }

    def _load_fonts(self):
        font_path = os.path.join(self.base_path, '..', 'assets', 'fonts')
        try:
            self.ui_font = pygame.font.Font(os.path.join(font_path, 'font.ttf'), 24)
            self.ui_sub_font = pygame.font.Font(os.path.join(font_path, 'font.ttf'), 15)

        except pygame.error as e:
            print(f'Font file load fail: {e}')
            pygame.quit()
            exit()

    def _load_sounds(self):
        sound_path = os.path.join(self.base_path, '..', 'assets', 'sounds')
        try:
            sound_1 = pygame.mixer.Sound(os.path.join(sound_path, 'place1.wav'))
            sound_2 = pygame.mixer.Sound(os.path.join(sound_path, 'place2.wav'))
            sound_3 = pygame.mixer.Sound(os.path.join(sound_path, 'place3.wav'))
            sound_4 = pygame.mixer.Sound(os.path.join(sound_path, 'place4.wav'))

            self.sounds = [sound_1, sound_2, sound_3, sound_4]

        except pygame.error as e:
            print(f'Sound file load fail: {e}')
            pygame.quit()
            exit()

    def _create_components(self):
        # Move Highlights Circle 생성
        self.highlights_move_circle = self._create_smooth_circle(15, 0, self.BLACK_COLOR)
        self.highlights_catch_circle = self._create_smooth_circle(70, 5, self.BLACK_COLOR)

        # Selected Highlights 생성
        self.highlight_selected = pygame.Surface((self.CELL_SIZE, self.CELL_SIZE), pygame.SRCALPHA)
        self.highlight_selected.fill((67, 116, 217, 100))
        self.highlight_taken_selected = pygame.Surface((self.TAKEN_CELL_SIZE, self.TAKEN_CELL_SIZE), pygame.SRCALPHA)
        self.highlight_taken_selected.fill((67, 116, 217, 100))

        # 상단 UI 배경 화면 생성
        self.background_text_surface = pygame.Surface((self.SCREEN_WIDTH, 100), pygame.SRCALPHA)
        self.background_text_surface.fill(self.WINDOW_COLOR)

        # 진영 색 표시 생성
        self.red_team_surface = pygame.Surface((self.BOARD_WIDTH, self.CELL_SIZE), pygame.SRCALPHA)
        self.red_team_surface.fill((self.TEAM_COLOR[1][0], self.TEAM_COLOR[1][1], self.TEAM_COLOR[1][2], 150))
        self.green_team_surface = pygame.Surface((self.BOARD_WIDTH, self.CELL_SIZE), pygame.SRCALPHA)
        self.green_team_surface.fill((self.TEAM_COLOR[-1][0], self.TEAM_COLOR[-1][1], self.TEAM_COLOR[-1][2], 150))

        # 포로 기물판 표시 생성
        self.red_taken_board_rect = pygame.Rect(self.TAKEN_BOARD_POS[1][0], self.TAKEN_BOARD_POS[1][1], self.TAKEN_BOARD_WIDTH, self.TAKEN_BOARD_HEIGHT)
        self.green_taken_board_rect = pygame.Rect(self.TAKEN_BOARD_POS[-1][0], self.TAKEN_BOARD_POS[-1][1], self.TAKEN_BOARD_WIDTH, self.TAKEN_BOARD_HEIGHT)

        # 좌표 Text 생성
        self.row_coord_surface = []
        for row in range(4):
            self.row_coord_surface.append(self.ui_sub_font.render(str(4 - row), True, (255, 255, 255, 255)))

        self.col_coord_surface = []
        for col in range(3):
            self.col_coord_surface.append(self.ui_sub_font.render(str(chr(col + ord('a'))), True, (255, 255, 255, 255)))

        # 보드판 영역 생성
        self.BOARD_AREA = pygame.Rect(self.BOARD_X, self.BOARD_Y, self.BOARD_WIDTH, self.BOARD_HEIGHT)
        self.TAKEN_BOARD_AREA = {
            1: pygame.Rect(self.TAKEN_BOARD_POS[1][0], self.TAKEN_BOARD_POS[1][1], self.TAKEN_BOARD_WIDTH, self.TAKEN_BOARD_HEIGHT),
            -1: pygame.Rect(self.TAKEN_BOARD_POS[-1][0], self.TAKEN_BOARD_POS[-1][1], self.TAKEN_BOARD_WIDTH, self.TAKEN_BOARD_HEIGHT)
        }

        
    def _create_smooth_circle(self, radius, width, color):
        scale_multiple = 4
        large_radius = radius * scale_multiple
        large_width = width * scale_multiple

        if large_width == 0:
            large_width = large_radius

        diameter = 2 * large_radius
        t_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)

        pygame.draw.circle(t_surface, color, (large_radius, large_radius), large_radius, large_width)

        result = pygame.transform.smoothscale(t_surface, (2*radius, 2*radius))
        return result