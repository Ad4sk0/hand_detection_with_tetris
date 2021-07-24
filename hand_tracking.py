import pygame
import cv2.cv2 as cv2
from hand_detector import handDetector
from moves_detector import movesDetector
import mediapipe as mp
import numpy as np
from utils import calculate_fps
import configparser

# TODO make the detection work better in bad light conditions

parser = configparser.ConfigParser()
parser.read("config.txt")

WIDTH = parser.getint("screen", "width")
HEIGHT = parser.getint("screen", "height")


def draw_landmarks_on_img(img, landmarks):
    mpDraw = mp.solutions.drawing_utils
    mpHands = mp.solutions.hands
    for handLms in landmarks:
        mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)


def main(events=None):
    hand_detector = handDetector(
        detection_con=parser.getfloat("detection", "detection_con"),
        track_con=parser.getfloat("detection", "track_con")
    )
    moves_detector = movesDetector(
        draw_rotation_helpers=parser.getboolean("detection", "draw_rotation_helpers"),
        draw_moves_helpers=parser.getboolean("detection", "draw_moves_helpers"),
        default_angle_correction=parser.getint("detection", "default_angle_correction")
    )

    draw_landmarks = parser.getboolean("detection", "draw_landmarks")
    show_fps = parser.getboolean("detection", "show_fps"),
    draw_on_white_card = parser.getboolean("detection", "draw_on_white_card"),

    p_time = 0
    cap = cv2.VideoCapture(0)
    game_started = False

    while True:
        success, img = cap.read()
        img = cv2.flip(img, 1)

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
            if move:
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
