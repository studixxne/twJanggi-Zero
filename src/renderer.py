import pygame
from utils import Piece

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
        self.TAKEN_BOARD_WIDTH = self.TAKEN_CELL_SIZE * 3
        self.TAKEN_BOARD_HEIGHT = self.TAKEN_CELL_SIZE * 4

        self.BOARD_X = 400
        self.BOARD_Y = 150
        self.TAKEN_BOARD_X = 110
        self.TAKNE_BOARD_Y = 150

        self.BLACK_COLOR = (33, 33, 33, 97)
        self.WINDOW_COLOR = (74, 74, 74, 180)

        # 초기화
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.screen.fill(self.BLACK_COLOR)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption('twJanggi')

        self._load_images()
        self._load_fonts()
        self._load_sounds()
        self._create_etc()

    def _load_images(self):
        try:
            images = {
                'board': pygame.image.load('/assets/images/board_image.jpg'),
                'red_king': pygame.image.load('/assets/images/RED_KING.jpg'),
                'green_king': pygame.image.load('/assets/images/GREEN_KING.jpg'),
                'ja': pygame.image.load('/assets/images/JA.jpg'),
                'sang': pygame.image.load('/assets/images/SANG.jpg'),
                'jang': pygame.image.load('/assets/images/JANG.jpg'),
                'hu': pygame.image.load('/assets/images/HU.jpg')
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
            (-1, Piece.KING): pygame.transform.smoothscale(images["green_king"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.JA): pygame.transform.smoothscale(images["ja"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.SANG): pygame.transform.smoothscale(images["sang"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.JANG): pygame.transform.smoothscale(images["jang"], (self.PIECE_SIZE, self.PIECE_SIZE)),
            (-1, Piece.HU): pygame.transform.smoothscale(images["hu"], (self.PIECE_SIZE, self.PIECE_SIZE))
        }

        self.taken_piece_images = {
            (1, Piece.JA): pygame.transform.smoothscale(images["ja"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (1, Piece.SANG): pygame.transform.smoothscale(images["sang"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (1, Piece.JANG): pygame.transform.smoothscale(images["jang"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (-1, Piece.JA): pygame.transform.smoothscale(images["ja"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (-1, Piece.SANG): pygame.transform.smoothscale(images["sang"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE)),
            (-1, Piece.JANG): pygame.transform.smoothscale(images["jang"], (self.TAKEN_PIECE_SIZE, self.TAKEN_PIECE_SIZE))
        }

    def _load_fonts(self):
        try:
            self.ui_font = pygame.font.Font('/assets/fonts/font.ttf', 24)
            self.ui_sub_font = pygame.font.Font('/assets/fonts/font.ttf', 15)
            self.ui_history_font = pygame.font.Font('/assets/fonts/font.ttf', 14)

        except pygame.error as e:
            print(f'Font file load fail: {e}')
            pygame.quit()
            exit()

    def _load_sounds(self):
        try:
            sound_1 = pygame.mixer.Sound('/assets/sounds/place1.wav')
            sound_2 = pygame.mixer.Sound('/assets/sounds/place2.wav')
            sound_3 = pygame.mixer.Sound('/assets/sounds/place3.wav')
            sound_4 = pygame.mixer.Sound('/assets/sounds/place4.wav')

            self.sounds = [sound_1, sound_2, sound_3, sound_4]

        except pygame.error as e:
            print(f'Sound file load fail: {e}')
            pygame.quit()
            exit()

    def _create_etc(self):
        # Move Highlights Circle 생성
        self.highlights_move_circle = self._create_smooth_circle(15, 0, self.BLACK_COLOR)
        self.highlights_catch_circle = self._create_smooth_circle(70, 5, self.BLACK_COLOR)

        # Selected Highlights 생성
        self.highlight_selected = pygame.Surface((self.CELL_SIZE, self.CELL_SIZE), pygame.SRCALPHA)
        self.highlight_selected.fill((67, 116, 217, 100))
        self.highlight_pow_selected = pygame.Surface((self.TAKEN_CELL_SIZE, self.TAKEN_CELL_SIZE), pygame.SRCALPHA)
        self.highlight_pow_selected.fill((67, 116, 217, 100))

        # 상단 UI 배경 화면 생성
        self.background_text_surface = pygame.Surface((self.SCREEN_WIDTH, 100), pygame.SRCALPHA)
        self.background_text_surface.fill(self.WINDOW_COLOR)

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