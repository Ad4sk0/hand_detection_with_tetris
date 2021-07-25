from utils import convert_pos_to_cords, get_angle_between_three_points, limitedList, calculate_point_based_on_degrees
import cv2.cv2 as cv2
import numpy as np
import time
import configparser

parser = configparser.ConfigParser()
parser.read("config.txt")


def determine_hand_position(landmarks, img):
    lms_to_count = [0, 9]  # wrist and middle_finger_mcp are count in order to determine the center of the hand
    cum_x_position_relative = sum(lm.x for i, lm in enumerate(landmarks[0].landmark) if i in lms_to_count) / len(
        lms_to_count)
    cum_y_position_relative = sum(lm.y for i, lm in enumerate(landmarks[0].landmark) if i in lms_to_count) / len(
        lms_to_count)
    cum_x_position_absolute, cum_y_position_absolute = convert_pos_to_cords(img, (cum_x_position_relative, cum_y_position_relative))
    return cum_x_position_absolute, cum_y_position_absolute


class movesDetector:
    def __init__(self, draw_rotation_helpers=False, draw_moves_helpers=False, default_angle_correction=0):
        self.draw_rotation_helpers = draw_rotation_helpers
        self.draw_moves_helpers = draw_moves_helpers
        self.default_angle_correction = default_angle_correction

        self.last_moves = limitedList(10)
        self.last_tip_writs_degrees = limitedList(10)
        self.last_x_positions = limitedList(10)
        self.last_y_positions = limitedList(10)
        self.last_hand_positions = limitedList(150)

        self.max_time_for_next_move_x = parser.getint("game", "max_time_for_next_move_x")  # if velocity == 0
        self.min_time_for_next_move_x = parser.getint("game", "min_time_for_next_move_x")  # if velocity == 100
        self.max_time_for_next_move_y = parser.getint("game", "max_time_for_next_move_y")  # if velocity == 0
        self.min_time_for_next_move_y = parser.getint("game", "min_time_for_next_move_y")  # if velocity == 100

        self.enable_rotation = True
        self.enable_x_move = True
        self.enable_y_move = True
        self.velocity_x = 0
        self.velocity_y = 0

        self.prev_time = round(time.time() * 1000)
        self.time_without_move_x = 0
        self.time_without_move_y = 0

    def detect_move(self, landmarks, img):
        if not landmarks:
            return False
        self.calculate_time()

        # detect if the user wants to rotate block
        rotation = self.is_move_rotate(landmarks, img, draw_helpers=self.draw_rotation_helpers)
        if rotation:
            return rotation

        # detect if the user wants to move block left, right or down
        move_x_y = self.is_move_x_y_axis(landmarks, img, draw_helpers=self.draw_moves_helpers)
        if move_x_y:
            return move_x_y

        return False

    def is_move_rotate(self, landmarks, img, draw_helpers=False):
        """
        The move is detected if degree between middle finger, wrist, and wrist y line is greater than threshold for
        this move. In order to detect move again the degree has to be smaller than enable move degree variable, which
        means that the hand is in starting position again

        returns False, string: rotate_clockwise or string: rotate_counterclockwise
        """
        # Thresholds
        enable_move_degrees_threshold = parser.getint("moves_detection", "enable_move_degrees_threshold")
        move_degrees_threshold = parser.getint("moves_detection", "move_degrees_threshold")

        # Point A = middle finger tip
        mf_id = 12
        mf_lm = landmarks[0].landmark[mf_id]
        mf = (mf_lm.x, mf_lm.y)
        middle_finger_tip = convert_pos_to_cords(img, mf)

        # Point B = wrist
        w_id = 0
        w_lm = landmarks[0].landmark[w_id]
        w = (w_lm.x, w_lm.y)
        wrist = convert_pos_to_cords(img, w)

        # Point C = point on wrist x axis and y=0
        wrist_line_vec = (wrist[0], 0)

        # the angle is equal to 0 when the wrist and middle finger tip are in the same y line.
        # degrees on the left are negative values and degrees on the right positive
        alpha = get_angle_between_three_points(wrist_line_vec, wrist, middle_finger_tip)

        # Move angles more to left or to right - the bending of the hand is not the same in both sides
        # Negative values move to left, positive to right
        # For right handed person it should be bended to right
        # Change this value if there will be problem with rotation detection only in one direction
        default_angle_correction = self.default_angle_correction

        # Angle should be  corrected accordingly to position of the hand (wrist position can be used here)
        # The more one hand goes into one direction the more bended it is. It could result in unintentional rotation if not corrected here
        # 60 degrees turned out to be natural hand bend when the hand is moved maximally to one side
        # BUT IT DEPENDS ON THE DISTANCE FROM CAMERA.
        # TODO make it dynamically based on distance
        max_degrees_correction = parser.getint("moves_detection", "max_degrees_correction")
        h, w, c = img.shape
        max_hand_reach = w // 2 - 20
        x1, y1 = (w // 2, h // 2)  # x1 and y2 are middle of the screen
        x2, y2 = wrist  # position of the hand based on wrist here
        x_dist = x2 - x1
        position_angle_correction = int(np.interp(x_dist, [-max_hand_reach, max_hand_reach], [-max_degrees_correction, max_degrees_correction]))

        # Determine final angles thresholds
        angle_correction = default_angle_correction + position_angle_correction
        left_corrected_move_angle = angle_correction-move_degrees_threshold
        right_corrected_move_angle = move_degrees_threshold + angle_correction
        left_corrected_enable_move_angle = angle_correction - enable_move_degrees_threshold
        right_corrected_enable_move_angle = angle_correction + enable_move_degrees_threshold

        # Draw triangle
        if draw_helpers:
            circle_color = (100, 255, 100)  # green
            if not self.enable_rotation:
                circle_color = (0, 0, 255)  # red
            cv2.circle(img, middle_finger_tip, 10, circle_color, cv2.FILLED)
            cv2.circle(img, wrist, 10, (255, 255, 0), cv2.FILLED)
            cv2.circle(img, wrist_line_vec, 10, (255, 255, 0), cv2.FILLED)
            cv2.line(img, middle_finger_tip, wrist, (255, 255, 0), 2)
            cv2.line(img, middle_finger_tip, wrist_line_vec, (255, 255, 0), 2)
            cv2.line(img, wrist_line_vec, wrist, (255, 255, 0), 2)

            # Degree threshold line for move
            move_threshold_point1 = calculate_point_based_on_degrees(wrist, right_corrected_move_angle)
            move_threshold_point2 = calculate_point_based_on_degrees(wrist, left_corrected_move_angle)
            cv2.line(img, wrist, move_threshold_point1, (0, 0, 255), 2)
            cv2.line(img, wrist, move_threshold_point2, (0, 0, 255), 2)

            # Degree threshold line for enable move again
            enable_move_threshold_point1 = calculate_point_based_on_degrees(wrist, right_corrected_enable_move_angle)
            enable_move_threshold_point2 = calculate_point_based_on_degrees(wrist, left_corrected_enable_move_angle)
            cv2.line(img, wrist, enable_move_threshold_point1, (0, 255, 0), 2)
            cv2.line(img, wrist, enable_move_threshold_point2, (0, 255, 0), 2)

            cv2.putText(img, str(alpha) + " deg", (wrist[0] + 2, wrist[1] - 40), cv2.FONT_HERSHEY_DUPLEX, .6, (0, 0, 0), 2)

        if self.enable_rotation and alpha < left_corrected_move_angle:
            self.enable_rotation = False
            return "rotate_counterclockwise"

        if self.enable_rotation and alpha > right_corrected_move_angle:
            self.enable_rotation = False
            return "rotate_clockwise"

        if not self.enable_rotation and left_corrected_enable_move_angle < alpha < right_corrected_enable_move_angle:
            self.enable_rotation = True
        return False

    def is_move_x_y_axis(self, landmarks, img, draw_helpers=False):
        """
        The move is detected if the hand is moved into one direction more than threshold defined here.
        The more it goes to one side the bigger the velocity of the move.

        returns False, string: move_left, string: move_right or string: move_down
        """
        h, w, c = img.shape

        # Thresholds for move - absolute value
        move_circle_radius = 90
        x1, y1 = (w // 2, h // 2)  # x1 and y2 are middle of the image

        # Determine hand center position - x2 and y2 are current hand position
        x2, y2 = determine_hand_position(landmarks, img)

        # Dynamic position should be better than static - if the user will not keep the hand in the middle of the screen
        # the length of the previous hand positions should be at least 150
        # TODO play with different prev positions lengths, max speed and min speed to make this most comfortable
        dynamic_center_position = parser.getboolean("moves_detection", "dynamic_center_position"),
        if dynamic_center_position:
            # Adding center position to this temp list will prevent the center point from being close to the border
            # It will also save memory in contrast to increasing the size of the list
            # Increase of this value will result in more static centroid point
            move_to_center_ratio = parser.getint("moves_detection", "move_to_center_ratio")
            for _ in range(move_to_center_ratio):
                self.last_hand_positions.insert((x1, y1))
            self.last_hand_positions.insert((x2, y2))

            if len(self.last_hand_positions.get()) > 10:
                x1 = int(sum(pos[0] for pos in self.last_hand_positions.get()) / len(self.last_hand_positions.get()))
                y1 = int(sum(pos[1] for pos in self.last_hand_positions.get()) / len(self.last_hand_positions.get()))

        # Determine if hand is inside move area
        hand_is_in_move_area = x1 - move_circle_radius > x2 or x2 > x1 + move_circle_radius or y2 > y1 + move_circle_radius

        # Calculate velocity - values from 0 to 100
        if hand_is_in_move_area:
            length_x = abs(x2 - x1)
            length_y = y2 - y1
            x_border_correction = 50 # hand won't go exactly to border, so it has to be corrected here
            y_border_correction = 10
            max_length_x = w // 2 - abs(w // 2 - x1) - x_border_correction
            max_length_y = h - y1 - y_border_correction
            self.velocity_x = int(np.interp(length_x, [move_circle_radius, max_length_x], [0, 100]))
            self.velocity_y = int(np.interp(length_y, [move_circle_radius, max_length_y], [0, 100]))

        # Draw circles in order to illustrate how the moves work
        if draw_helpers:
            circle_color = (100, 255, 100)  # green
            if hand_is_in_move_area:
                circle_color = (0, 0, 255)  # red
            cv2.circle(img, (x1, y1), 10, (0, 255, 255), cv2.FILLED)  # MIDDLE CIRCLE YELLOW
            cv2.circle(img, (x2, y2), 10, circle_color, cv2.FILLED)  # HAND POSITION CIRCLE
            cv2.line(img, (x1, y1), (x2, y2), (255, 255, 0), 1)
            cv2.circle(img, (x1, y1), move_circle_radius, (0, 0, 255), 3)  # MAKE MOVE AREA RED

            # Additional to circles there lines can be drawn which denote squares where moves are possible
            cv2.line(img, (x1 + move_circle_radius, 0), (x1 + move_circle_radius, h), (255, 255, 0), 2)
            cv2.line(img, (x1 - move_circle_radius, 0), (x1 - move_circle_radius, h), (255, 255, 0), 2)
            cv2.line(img, (0, y1 + move_circle_radius), (w, y1 + move_circle_radius), (255, 255, 0), 2)

            # Draw velocity
            if hand_is_in_move_area:
                cv2.putText(img, "Velocity x: " + str(self.velocity_x), (x2, y2 + 40), cv2.FONT_HERSHEY_DUPLEX, .6, (0, 0, 0), 2)
                cv2.putText(img, "Velocity y: " + str(self.velocity_y), (x2, y2 + 60), cv2.FONT_HERSHEY_DUPLEX, .6, (0, 0, 0), 2)

        # Interpolate velocity to time intervals between moves (change max and min time for change speed of the moves
        time_with_current_velocity_x = int(np.interp(self.velocity_x, [0, 100], [self.max_time_for_next_move_x, self.min_time_for_next_move_x]))
        time_with_current_velocity_y = int(np.interp(self.velocity_y, [0, 100], [self.max_time_for_next_move_y, self.min_time_for_next_move_y]))

        # MOVE LEFT
        if self.time_without_move_x > time_with_current_velocity_x and x2 < x1 - move_circle_radius:
            self.time_without_move_x = 0
            return "move_left"

        # MOVE RIGHT
        if self.time_without_move_x > time_with_current_velocity_x and x2 > x1 + move_circle_radius:
            self.time_without_move_x = 0
            return "move_right"

        # MOVE DOWN
        if self.time_without_move_y > time_with_current_velocity_y and y2 > y1 + move_circle_radius:
            self.time_without_move_y = 0
            return "move_down"

        return False

    def calculate_time(self):
        current_time = round(time.time() * 1000)
        diff = current_time - self.prev_time
        self.time_without_move_x += diff
        self.time_without_move_y += diff
        self.prev_time = current_time
