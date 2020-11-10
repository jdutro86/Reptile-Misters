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
