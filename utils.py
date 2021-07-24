import time
import math


def calculate_fps(previous_time):
    current_time = time.time()
    try:
        fps = 1 / (current_time - previous_time)
    except:
        pass
    return fps, current_time


def convert_pos_to_cords(image, cords):
    height, width, _ = image.shape
    if len(cords) == 2:
        new_cords = (int(cords[0] * width), int(cords[1] * height))  # x and y
    return new_cords


def get_angle_between_three_points(a, b, c):
    # a = np.array(a)
    # b = np.array(b)
    # c = np.array(c)
    #
    # ba = a - b
    # bc = c - b
    #
    # cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    # angle = np.arccos(cosine_angle)
    #
    # return int(np.degrees(angle))
    ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
    if 180 < ang < 270:
        ang = ang - 360
    return int(ang)


def calculate_point_based_on_degrees(point, degrees, length=300):
    y = int(point[1] - length * math.cos(math.radians(degrees)))
    x = int(point[0] + length * math.sin(math.radians(degrees)))
    return x, y


class limitedList:
    def __init__(self, size):
        self.size = size
        self.list = []

    def insert(self, x):
        if len(self.list) == self.size:
            self.list = self.list[:self.size - 1]
        self.list.insert(0, x)

    def get(self):
        return self.list
