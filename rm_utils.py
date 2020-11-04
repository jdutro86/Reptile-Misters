"""rm_utils.py
Contains any utility objects/methods for our project.
"""

import time

class Stopwatch(object):
    """
    Allows easier tracking of time, instead of having a bunch of random variables.
    """

    def __init__(self, startTime=time.time()):
        """
        Initializer for the object.
        `startTime` is the time at which the Stopwatch started. Should usually be the time at which it was instantiated.
        """
        self.startTime = startTime
        self.running = False
        self.totalTime = 0

    def start(self):
        """
        Starts the stopwatch.
        """
        if not self.running:
            self.startTime = time.time()
            self.running = True

    def stop(self):
        """
        Stops the stopwatch, adding on elapsed time to the totalTime.
        """
        if self.running:
            self.totalTime += time.time() - self.startTime
            self.running = False

    def reset(self):
        """
        Resets the time of the stopwatch to 0.
        """
        self.totalTime = 0
        self.startTime = time.time()

    def value(self):
        """
        Returns the total time for which the stopwatch has been running.
        """
        if self.running:
            return self.totalTime + time.time() - self.startTime
        else:
            return self.totalTime

class TimeStampLog():
    """
    Keeps track of when the valve has been opened/closed.
    """

    def __init__(self):
        """
        Initializer for the object.
        """
        self.timeStampCount = 0
        self.openTimeList = [0]
        self.closeTimeList = [0]

    def open_time(self, openTime):
        """
        Appends one open time.
        `openTime` is the number value of the time.
        """
        self.timeStampCount += 1
        self.openTimeList.append(openTime)

    def close_time(self, closeTime):
        """
        Appends one close time.
        `closeTime` is the number value of the time.
        """
        self.closeTimeList.append(closeTime)

    def get_last_open(self):
        """
        Gets the last open time in displayable format.
        """
        return time.asctime(time.localtime(self.openTimeList[self.timeStampCount]))

    def get_last_close(self):
        """
        Gets the last close time in displayable format.
        """
        return time.asctime(time.localtime(self.closeTimeList[self.timeStampCount]))

    def get_time_open(self):
        """
        Gets the duration of the latest open/close time.
        """
        return str(round(self.closeTimeList[self.timeStampCount]-self.openTimeList[self.timeStampCount], 2))

    def times_open(self):
        """
        Gets the total number of times the valve has been opened.
        """
        return str(len(self.openTimeList) - 1)

    def times_closed(self):
        """
        Gets the total number of times the valve has been closed.
        """
        return str(len(self.closeTimeList) - 1)
