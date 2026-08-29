import math

class RadialEvent:
    def __init__(self, origin, start_time_s, speed_m_s, radius_max_m):
        self.origin = tuple(origin)
        self.start_time = start_time_s
        self.speed = speed_m_s
        self.radius_max = radius_max_m

    def distance(self, position):
        return math.dist(position, self.origin)

    def arrival_time(self, position):
        return self.start_time + self.distance(position) / self.speed

    def intensity(self, position, time):
        if time < self.start_time:
            return 0.0
        front = min((time - self.start_time) * self.speed, self.radius_max)
        d = self.distance(position)
        # señal máxima cerca/detrás del frente, con transición suave
        delta = front - d
        if delta < -8:
            return 0.0
        if delta > 8:
            return 1.0
        return (delta + 8.0) / 16.0
