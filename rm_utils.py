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
