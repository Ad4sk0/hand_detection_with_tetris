import pygame
import cv2.cv2 as cv2
from hand_detector import handDetector
from moves_detector import movesDetector
import mediapipe as mp
import numpy as np
from utils import calculate_fps
import configparser
import time

# TODO make the detection work better in bad light conditions

parser = configparser.ConfigParser()
parser.read("config.txt")

WIDTH = parser.getint("screen", "width")
HEIGHT = parser.getint("screen", "height")

WAIT_DELAY = False
PREV_TIME = 0


def draw_landmarks_on_img(img, landmarks):
    mpDraw = mp.solutions.drawing_utils
    mpHands = mp.solutions.hands
    for handLms in landmarks:
        mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)


def set_wait_delay():
    global WAIT_DELAY
    global PREV_TIME
    WAIT_DELAY = True
    PREV_TIME = round(time.time() * 1000)


def main(events=None):
    global WAIT_DELAY
    global PREV_TIME
    time_waited = 0
    time_delay_after_floor_hit = parser.getint("moves_detection", "time_delay_after_floor_hit")

    hand_detector = handDetector(
        detection_con=parser.getfloat("hand_detection", "detection_con"),
        track_con=parser.getfloat("hand_detection", "track_con")
    )
    moves_detector = movesDetector(
        draw_rotation_helpers=parser.getboolean("detection_gui", "draw_rotation_helpers"),
        draw_moves_helpers=parser.getboolean("detection_gui", "draw_moves_helpers"),
        default_angle_correction=parser.getint("moves_detection", "default_angle_correction")
    )

    draw_landmarks = parser.getboolean("detection_gui", "draw_landmarks")
    show_fps = parser.getboolean("detection_gui", "show_fps")
    draw_on_white_card = parser.getboolean("detection_gui", "draw_on_white_card")

    p_time = 0
    cap = cv2.VideoCapture(0)
    game_started = False

    while True:
        success, img = cap.read()
        img = cv2.flip(img, 1)

        # Add small delay after block hits the floor or another block in order to avoid unintentional moves
        if WAIT_DELAY:
            current_time = round(time.time() * 1000)
            diff = current_time - PREV_TIME
            time_waited += diff
            PREV_TIME = current_time
            if time_waited >= time_delay_after_floor_hit:
                time_waited = 0
                WAIT_DELAY = False

        # For bad light conditions - experiment with it
        # alpha = 1.05  # Contrast control (1.0-3.0)
        # beta = 0  # Brightness control (0-100)
        # img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

        # Detect hand
        landmarks = hand_detector.findHands(img)

        # change background to white
        if draw_on_white_card:
            img = np.zeros(img.shape, dtype=np.uint8)
            img[:] = 255

        # Add landmarks to image
        if draw_landmarks and landmarks:
            draw_landmarks_on_img(img, landmarks)

        # Detect moves
        move = moves_detector.detect_move(landmarks, img)
        if move:
            print("MOVE DETECTED: " + move)

        # Create pygame events here
        if events:
            if not landmarks:
                pygame.event.post(events["no_hand_detected"])
            else:
                pygame.event.post(events["hand_detected"])
            if move and not WAIT_DELAY:
                pygame.event.post(events[move])

        # Calculate fps
        if show_fps:
            fps, p_time = calculate_fps(p_time)
            cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_DUPLEX, 3, (255, 0, 0), 3)

        # Show hands
        win_name = "Hand detection"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(win_name, 1000, 200)
        cv2.resizeWindow(win_name, WIDTH, HEIGHT)
        cv2.imshow(win_name, img)

        # q or esc for quit
        if cv2.waitKey(1) in [27, 113]:
            cv2.destroyAllWindows()
            break

        if not game_started:
            pygame.event.post(events["open_cv_initialized"])
            game_started = True


if __name__ == '__main__':
    main()
