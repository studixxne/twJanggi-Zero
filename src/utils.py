from enum import IntEnum

MOVE_DIRECTION = [
    (-1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, -1)
]

class Piece(IntEnum):
    EMPTY = 0
    JA = 1
    SANG = 2
    JANG = 3
    HU = 4
    KING = 5

def next_location(row, col, direction):
    d_row, d_col = MOVE_DIRECTION[direction]
    next_row, next_col = row+d_row, col+d_col
    return next_row, next_col

def action_to_move(action):
    # 보드판 위에 있는 말을 이동시키는 Action
    if action < 96:
        pos, direction = divmod(action, 8)
        row, col = divmod(pos, 3)

        next_row, next_col = next_location(row, col, direction)
        return (row, col, next_row, next_col)

    # 포로 말을 배치하는 Action
    else:
        piece_type, pos = divmod(action-96, 12)
        next_row, next_col = divmod(pos, 3)
        return (-1, piece_type+1, next_row, next_col)


def move_to_action(move):
    if move[0] != -1:
        row, col, next_row, next_col = move
        direction = MOVE_DIRECTION.index((next_row-row, next_col-col))

        pos = row * 3 + col
        action = pos * 8 + direction

        return action

    else:
        _, piece_type, next_row, next_col = move

        pos = next_row * 3 + next_col
        action = 96 + ((piece_type-1) * 12 + pos)

        return action