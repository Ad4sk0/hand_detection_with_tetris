import pygame
import random
import threading
import hand_tracking
import os
import configparser

parser = configparser.ConfigParser()
parser.read("config.txt")

pygame.font.init()

WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

ENABLE_HAND_DETECTION = parser.getboolean("key_game_options", "enable_hand_detection")

# Window
if ENABLE_HAND_DETECTION:
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (100, 200)
WIDTH = parser.getint("screen", "width")
HEIGHT = parser.getint("screen", "height")
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris")
TETRIS_AREA_X = WIDTH // 4
TETRIS_AREA_W = WIDTH // 2
MENU_W = (WIDTH - TETRIS_AREA_W) // 2

# Game
DIFFICULTY_LVL = parser.getint("key_game_options", "difficulty_lvl")  # 1 2 or 3

if DIFFICULTY_LVL == 3:
    FALLING_SPEED = 250
elif DIFFICULTY_LVL == 3:
    FALLING_SPEED = 350
else:
    FALLING_SPEED = 500

# Grid
ROWS_N = parser.getint("screen", "rows_n")
COLS_N = parser.getint("screen", "cols_n")
GRID_LINE_WIDTH = parser.getint("screen", "grid_line_width")

# Fonts
SCORE_FONT = pygame.font.SysFont('Arial', WIDTH // 30)
HAND_DETECTION_FONT = pygame.font.SysFont('Arial', WIDTH // 40)
LOADING_FONT = pygame.font.SysFont('Arial', WIDTH // 20)

SHAPES = {
    "I": [[1],
          [1],
          [1]],
    "J": [[0, 1],
          [0, 1],
          [1, 1]],
    "L": [[1, 0],
          [1, 0],
          [1, 1]],
    "O": [[1, 1],
          [1, 1]],
    "S": [[0, 1, 1],
          [1, 1, 0]],
    "T": [[1, 1, 1],
          [0, 1, 0]],
    "Z": [[1, 1, 0],
          [0, 1, 1]],
}
colors = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 000, 255),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (255, 255, 255),
    (0, 0, 0),
]


class Block:
    def __init__(self):
        rand = random.randint(0, len(SHAPES) - 1)  # same color for similar shapes
        self.color = colors[rand]
        self.shape = list(SHAPES.values())[rand]
        self.w = len(self.shape[0])
        self.h = len(self.shape)
        # init blocks in the middle above tetris area
        self.x = COLS_N // 2 - 1
        self.y = -1 * self.h

    def rotate(self, occupied_fields_set, direction="clockwise"):
        prev_shape = self.shape
        prev_w = self.w
        prev_h = self.h
        if direction == "clockwise":
            self.shape = list(zip(*self.shape[::-1]))  # rotate clockwise
        else:
            self.shape = list(zip(*self.shape))[::-1]  # rotate counterclockwise
        self.w = len(self.shape[0])
        self.h = len(self.shape)

        if not is_valid_move(self, occupied_fields_set):
            self.shape = prev_shape
            self.w = prev_w
            self.h = prev_h


events = {
    "move_left": pygame.event.Event(pygame.USEREVENT, key=pygame.K_LEFT),
    "move_right": pygame.event.Event(pygame.USEREVENT, key=pygame.K_RIGHT),
    "move_down": pygame.event.Event(pygame.USEREVENT, key=pygame.K_DOWN),
    "rotate_clockwise": pygame.event.Event(pygame.USEREVENT, key=pygame.K_UP, attr="clockwise"),
    "rotate_counterclockwise": pygame.event.Event(pygame.USEREVENT, key=pygame.K_UP, attr="counterclockwise"),
    "no_hand_detected": pygame.event.Event(pygame.USEREVENT, attr="no_hand"),
    "hand_detected": pygame.event.Event(pygame.USEREVENT, attr="hand"),
    "open_cv_initialized": pygame.event.Event(pygame.USEREVENT, attr="open_cv_ready"),
}


class HandDetectionThread(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        hand_tracking.main(events)


def draw_tetris_area():
    tetris_area_color = (0, 0, 0)
    tetris_area = pygame.Rect(TETRIS_AREA_X, 0, TETRIS_AREA_W, HEIGHT)
    pygame.draw.rect(WIN, tetris_area_color, tetris_area)
    return tetris_area


def create_grid():
    grid = [[BLACK for row in range(ROWS_N)] for col in range(COLS_N)]
    return grid


def draw_rectangles(tetris_area, grid):
    col_size = tetris_area.width / COLS_N
    row_size = tetris_area.height / ROWS_N
    for col in range(COLS_N):
        for row in range(ROWS_N):
            square = pygame.Rect(tetris_area.x + col * col_size, tetris_area.y + row * row_size, col_size, row_size)
            pygame.draw.rect(WIN, grid[col][row], square)


def draw_grid(area, rows, cols):
    col_size = area.width / cols
    row_size = area.height / rows

    for col in range(1, cols):
        # dont draw last line
        if col == cols:
            continue
        pygame.draw.line(WIN, WHITE, (area.x + col * col_size, area.y),
                         (area.x + col * col_size, area.y + area.height), GRID_LINE_WIDTH)

    for row in range(1, rows):
        # don't draw last line
        if row == rows:
            continue
        pygame.draw.line(WIN, WHITE, (area.x, area.y + row * row_size),
                         (area.x + area.width, area.y + row * row_size), GRID_LINE_WIDTH)


def update_grid(grid, current_shape_pos, occupied_fields, block):
    for field in current_shape_pos:
        grid[field[0]][field[1]] = block.color

    for field in occupied_fields.keys():
        grid[field[0]][field[1]] = occupied_fields[field]


def create_left_menu(WIN, score):
    score_text = SCORE_FONT.render("Score: " + str(score), True, WHITE)
    score_text_x = MENU_W // 2 - score_text.get_width() // 2  # center of left menu
    WIN.blit(score_text, (score_text_x, HEIGHT // 16))


def create_right_menu(WIN, tetris_area, next_block):
    col_size = tetris_area.width / COLS_N
    row_size = tetris_area.height / ROWS_N
    right_menu_x = tetris_area.x + tetris_area.width
    right_menu_y = tetris_area.y

    # display next block area (assuming max block len is 3)
    disp_cols_n = 3
    disp_rows_n = 3
    display_w = col_size * disp_cols_n
    display_h = row_size * disp_rows_n
    display_x = right_menu_x + MENU_W // 2 - display_w // 2
    display_y = HEIGHT // 16

    # create display area object
    disp_area_color = (0, 0, 0)
    disp_area = pygame.Rect(display_x, display_y, display_w, display_h)
    pygame.draw.rect(WIN, disp_area_color, disp_area)

    # Temporary change block x y to 0 in order to get correct current positions
    prev_x = next_block.x
    prev_y = next_block.y
    next_block.y = 0
    next_block.x = 0
    next_block_pos = calculate_current_block_positions(next_block)
    next_block.x = prev_x
    next_block.y = prev_y

    for col in range(disp_cols_n):
        for row in range(disp_rows_n):
            square = pygame.Rect(display_x + col * col_size, display_y + right_menu_y + row * row_size, col_size, row_size)
            if (col, row) in next_block_pos:
                pygame.draw.rect(WIN, next_block.color, square)

    draw_grid(disp_area, disp_cols_n, disp_rows_n)


def draw_window(block, current_shape_pos, occupied_fields, score, next_block, hand_detection_text):
    WIN.fill((200, 200, 200))

    grid = create_grid()
    update_grid(grid, current_shape_pos, occupied_fields, block)
    tetris_area = draw_tetris_area()
    draw_rectangles(tetris_area, grid)
    draw_grid(tetris_area, ROWS_N, COLS_N)

    create_left_menu(WIN, score)
    create_right_menu(WIN, tetris_area, next_block)

    print_message_from_hand_detector(hand_detection_text)

    pygame.display.update()


def remove_row(row, occupied_fields):
    new_dict = {}
    for key, value in occupied_fields.items():
        # move all rows above this row downwards
        if key[1] < row:
            new_key = (key[0], key[1] + 1)
            new_dict[new_key] = value
        # copy all rows below this row
        elif key[1] > row:
            new_dict[key] = value
        # ignore this row
    return new_dict


def calculate_current_block_positions(block):
    current_shape_pos = []
    i = 0
    for y in range(block.y, block.y + block.h):
        j = 0
        for x in range(block.x, block.x + block.w):
            if y >= 0 and block.shape[i][j] != 0:
                current_shape_pos.append((x, y))
            j += 1
        i += 1
    return current_shape_pos


def is_valid_move(block, occupied_fields_set):
    current_shape_pos = calculate_current_block_positions(block)

    # Touch left wall
    if block.x < 0:
        return False

    # Touch right wall:
    elif block.x + block.w > COLS_N:
        return False

    # Touch floor
    elif block.y + block.h >= ROWS_N:
        return False

    # Collision
    elif set(current_shape_pos).intersection(occupied_fields_set):
        return False

    # Allow move
    return True


def print_message_from_hand_detector(msg):
    hand_detected_text = HAND_DETECTION_FONT.render(msg, True, RED)
    hand_detected_text_x = MENU_W // 2 - hand_detected_text.get_width() // 2  # center of left menu
    WIN.blit(hand_detected_text, (hand_detected_text_x, HEIGHT // 2))


def draw_window_waiting_window(msg):
    WIN.fill((200, 200, 200))
    starting_text = LOADING_FONT.render(msg, True, RED)
    starting_text_x = WIDTH // 2 - starting_text.get_width() // 2
    WIN.blit(starting_text, (starting_text_x, HEIGHT // 2))
    pygame.display.update()


def main():
    clock = pygame.time.Clock()
    run = True
    pause = False
    initializing_opencv = True
    score = 0
    falling_time = 0
    hand_detected = False
    hand_detection_text = ""

    next_block = Block()
    block = Block()
    occupied_fields = {}  # dict key - occupied fields positions, value - color
    occupied_fields_set = set()  # set from occupied_fields keys() for convenience in use

    previous_shape_pos = []

    if ENABLE_HAND_DETECTION:
        hand_detection_thread = HandDetectionThread()
        hand_detection_thread.start()

    # Initializing open cv waiting window
    msg = "Loading..."
    while initializing_opencv:
        draw_window_waiting_window(msg)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                initializing_opencv = False
                pygame.quit()

            if event == events['hand_detected']:
                hand_detected = True
                initializing_opencv = False

            if event == events['open_cv_initialized']:
                msg = "Please move your hand to the camera"
    counter = 3
    while counter:
        msg = "Staring game in {}". format(counter)
        draw_window_waiting_window(msg)
        counter -= 1
        pygame.time.delay(500)

    while run:
        clock.tick()
        falling_time += clock.get_rawtime()

        for event in pygame.event.get():

            if hand_detected and event == events['no_hand_detected']:
                hand_detected = False
                hand_detection_text = "No hand detected"

            if not hand_detected and event == events['hand_detected']:
                hand_detected = True
                hand_detection_text = ""

            if event.type == pygame.QUIT:
                run = False
                pygame.quit()

            if hasattr(event, "key") and event.type in [pygame.KEYDOWN, pygame.USEREVENT]:
                # Move left
                if event.key == pygame.K_LEFT:
                    block.x -= 1
                    if not is_valid_move(block, occupied_fields_set):
                        block.x += 1

                # Move right
                if event.key == pygame.K_RIGHT:
                    block.x += 1
                    if not is_valid_move(block, occupied_fields_set):
                        block.x -= 1

                # Rotate block
                if event.key == pygame.K_UP:
                    direction = "clockwise"
                    if hasattr(event, "attr"):
                        direction = event.attr
                    block.rotate(occupied_fields_set, direction) # Rotation error handling in block class
                    clock.tick()

                # Move down
                if event.key == pygame.K_DOWN:
                    block.y += 1
                    if not is_valid_move(block, occupied_fields_set):
                        block.y -= 1

                # Pause
                if event.key == pygame.K_p:
                    pause = not pause

        if pause:
            pygame.time.delay(3000)
            continue

        # calculate current block positions
        current_shape_pos = calculate_current_block_positions(block)

        # Collision
        if set(current_shape_pos).intersection(occupied_fields_set):
            if block.y <= 0:
                # Game over
                run = False
            draw_window(block, previous_shape_pos, occupied_fields, score, next_block, hand_detection_text)
            for pos in previous_shape_pos:
                occupied_fields[pos] = block.color
            occupied_fields_set.update(occupied_fields.keys())
            previous_shape_pos = []
            block = next_block  # get new block
            next_block = Block()

        # Touch floor
        elif block.y + block.h >= ROWS_N:
            draw_window(block, current_shape_pos, occupied_fields, score, next_block, hand_detection_text)
            for pos in current_shape_pos:
                occupied_fields[pos] = block.color
            occupied_fields_set.update(occupied_fields.keys())
            block = next_block  # get new block
            next_block = Block()

        # Move block downwards
        else:
            draw_window(block, current_shape_pos, occupied_fields, score, next_block, hand_detection_text)
            if falling_time > FALLING_SPEED:
                falling_time = 0
                block.y += 1
            previous_shape_pos = current_shape_pos

        # Count number of block in rows
        rows = {}
        for pos in occupied_fields_set:
            row = pos[1]
            rows[row] = rows.get(row, 0) + 1
            if rows[row] == COLS_N:
                occupied_fields = remove_row(row, occupied_fields)
                occupied_fields_set = set(occupied_fields.keys())
                rows[row] = 0
                score += 100
    pygame.quit()


if __name__ == "__main__":
    main()
