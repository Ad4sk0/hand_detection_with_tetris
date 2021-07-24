import cv2.cv2 as cv2
import mediapipe as mp


class handDetector:
    def __init__(self, mode=False, maxHands=1, detection_con=0.8, track_con=0.8):
        self.mode = mode
        self.maxHand = maxHands
        self.detectionCon = detection_con
        self.trackCon = track_con
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(mode, maxHands, detection_con, track_con)

    def findHands(self, img, show_hand_label=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(imgRGB)

        # # DETERMINE HOW MANY HANDS ARE PRESENT AND ACCURACY HERE - not used as for now
        # if results.multi_handedness:
        #     hands_count = len(results.multi_handedness)
        #     if show_hand_label:
        #         for hand_class in results.multi_handedness:
        #             hand_index = hand_class.classification[0].index
        #             accuracy = hand_class.classification[0].score
        #             hand_label = hand_class.classification[0].label # right or left

        return results.multi_hand_landmarks
