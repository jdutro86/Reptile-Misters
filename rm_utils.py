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

