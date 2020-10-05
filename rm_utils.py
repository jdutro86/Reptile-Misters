"""rm_utils.py
Contains any utility objects/methods for our project.
"""

import time

# Allows simplified tracking of time
class Stopwatch(object):
    def __init__(self):
        self.startTime = time.time()
        self.running = False
        self.totalTime = 0

    def start(self):
        if not self.running:
            self.startTime = time.time()
            self.running = True

    def stop(self):
        if self.running:
            self.totalTime += time.time() - self.startTime
            self.running = False

    def reset(self):
        self.totalTime = 0
        self.startTime = time.time()

    def value(self):
        if self.running:
            return self.totalTime + time.time() - self.startTime
        else:
            return self.totalTime

class TimeStampLog():
    def __init__(self):
        self.timeStampCount = 0
        self.openTimeList = [0]
        self.closeTimeList = [0]

    def open_time(self, openTime):
        self.timeStampCount += 1
        self.openTimeList.append(openTime)

    def close_time(self, closeTime):
        self.closeTimeList.append(closeTime)

    def get_last_open(self):
        return time.asctime(time.localtime(self.openTimeList[self.timeStampCount]))

    def get_last_close(self):
        return time.asctime(time.localtime(self.closeTimeList[self.timeStampCount]))

    def get_time_open(self):
        return str(round(self.closeTimeList[self.timeStampCount]-self.openTimeList[self.timeStampCount], 2))

    def times_open(self):
        return str(len(self.openTimeList) - 1)

    def times_closed(self):
        return str(len(self.closeTimeList) - 1)

# Contains information for a single lizard tank
class Tank(object):
    # FLOW_RATE should be in volume per second
    FLOW_RATE = 0

    @staticmethod
    def set_flow_rate(val):
        Tank.FLOW_RATE = val

    def __init__(self, tankVolume=1, expectedWater=1, lizards={}):
        self.tankVolume = tankVolume
        self.expectedWater = expectedWater
        self.currentWater = 0
        self.lizards = lizards

    def species(self):
        return self.lizards.keys()

    # species is the key, gender should be 0 or 1, 0 for males, 1 for females
    def add_lizard(self, species, gender, n=1):
        if species not in self.lizards:
            self.lizards[species] = [0, 0]
        self.lizards[species][gender] += n

    def remove_lizard(self, species, gender, n=1):
        if species in self.lizards and self.lizards[species][gender] >= n:
            self.lizards[species][gender] -= n

            if self.lizards[species][0] == 0 and self.lizards[species][1] == 0:
                self.lizards.pop(species)

    def update(self, dt):
        self.currentWater += Tank.FLOW_RATE * dt

    def drain(self):
        self.currentWater = 0

    def get_fraction(self):
        return self.currentWater / self.expectedWater