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

POSSIBLE_MOVE_DIRECTION = {
    Piece.JA: [0],
    Piece.SANG: [1, 3, 5, 7],
    Piece.JANG: [0, 2, 4, 6],
    Piece.HU: [0, 1, 2, 4, 6, 7],
    Piece.KING: [0, 1, 2, 3, 4, 5, 6, 7]
}

def next_location(row, col, direction, player):
    d_row, d_col = MOVE_DIRECTION[direction]
    next_row, next_col = row + d_row*player, col + d_col*player
    return next_row, next_col

def get_possible_piece_moves(piece_type, row, col, player):
    possible_direction = POSSIBLE_MOVE_DIRECTION[piece_type]
    possible_piece_moves = []

    for dir in possible_direction:
        next_row, next_col = next_location(row, col, dir, player)
        possible_piece_moves.append((row, col, next_row, next_col))

    return possible_piece_moves

def action_to_move(action):
    # 보드판 위에 있는 말을 이동시키는 Action
    if action < 96:
        pos, direction = divmod(action, 8)
        row, col = divmod(pos, 3)
        d_row, d_col = MOVE_DIRECTION[direction]

        next_row, next_col = row+d_row, col+d_col
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
    
def action_to_text(action):
    if action < 96:
        move = action_to_move(action)
        return (f"({4-move[0]}, {chr(ord('a') + int(move[1]))}) to ({4-move[2]}, {chr(ord('a') + int(move[3]))})")
        
    else:
        move = action_to_move(action)
        if move[1] == 1:
            return f"자 ({4-move[2]}, {chr(ord('a') + int(move[3]))}) 배치"
        if move[1] == 2:
            return f"상 ({4-move[2]}, {chr(ord('a') + int(move[3]))}) 배치"
        if move[1] == 3:
            return f"장 ({4-move[2]}, {chr(ord('a') + int(move[3]))}) 배치"