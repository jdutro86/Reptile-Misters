"""rm_modes.py
Contains all the various modes of the main program.
"""

from PyQt5.QtCore import QTimer, pyqtSignal, QObject

from pin_devices import output_valve, water_detected, rpi_cleanup
from rm_utils import Stopwatch, TimeStampLog

import time
import math

class AbstractMode(QObject):
    def __init__(self, parent, UPDATE_MS):
        super(AbstractMode, self).__init__()
        self.parent = parent
        self.UPDATE_MS = UPDATE_MS
        self.timer = QTimer(parent)
        self.timer.setInterval(UPDATE_MS)
        self.timer.timeout.connect(self.update)

    def start(self):
        pass

    def stop(self):
        pass

    def update(self):
        pass

class SensorMode(AbstractMode):
    def __init__(self, parent, UPDATE_MS):
        super(SensorMode, self).__init__(parent, UPDATE_MS)

class TimedMode(AbstractMode):
    def __init__(self, parent, UPDATE_MS):
        super(TimedMode, self).__init__(parent, UPDATE_MS)

# Inherits QObject to allow for pyqtSignal usage
class EventLoop(QObject):
    # Custom signals for state transitions
    timerFinished = pyqtSignal()
    timeLimitReached = pyqtSignal()

    def __init__(self, ui, UPDATE_MS=10, SLOW_UPDATE_MS=500, MAX_OPEN_SECONDS=300):
        super(EventLoop, self).__init__()
        self.ui = ui
        self.UPDATE_MS = UPDATE_MS
        self.SLOW_UPDATE_MS = SLOW_UPDATE_MS
        self.MAX_OPEN_SECONDS = MAX_OPEN_SECONDS

        self.valveRecord = TimeStampLog()

        # QTimer for sensor mode
        self.waterCheckTimer = QTimer(self)
        self.waterCheckTimer.timeout.connect(self.sensor_mode)
        self.waterCheckTimer.setInterval(self.UPDATE_MS)

        # QTimer for timed mode
        self.timedValveWatch = Stopwatch()
        self.timedValveTimer = QTimer(self)
        self.timedValveTimer.timeout.connect(self.timed_mode)
        self.timedValveTimer.setInterval(self.UPDATE_MS)

        # QTimer for valve open time tracking
        self.valveWatch = Stopwatch()
        self.valveTimeShouldReset = False
        self.valveTimeOpenTimer = QTimer(self)
        self.valveTimeOpenTimer.timeout.connect(self.update_valve_time)
        self.valveTimeOpenTimer.setInterval(self.UPDATE_MS)
        self.valveTimeOpenTimer.start()

        # QTimer for clock updates
        self.clockTimer = QTimer(self)
        self.clockTimer.timeout.connect(self.update_clock)
        self.clockTimer.setInterval(self.SLOW_UPDATE_MS)
        self.clockTimer.start()

        # State machine-related transition logic
        ui.manualEnabled.entered.connect(self.open_valve)
        ui.manualEnabled.exited.connect(self.close_valve)
        ui.sensorEnabled.entered.connect(self.activate_sensor_mode)
        ui.sensorEnabled.exited.connect(self.deactivate_sensor_mode)
        ui.timerEnabled.entered.connect(self.activate_timed_mode)
        ui.timerEnabled.exited.connect(self.deactivate_timed_mode)

        # VERY IMPORTANT
        ui.idle.entered.connect(self.close_valve)

    def open_valve(self):
        # Logistical stuff only executes if valve is closed
        if not self.valveWatch.running:
            self.valveWatch.start()
            self.valveRecord.open_time(time.time())
            self.ui.lastOpenLabel.setText('Last open: ' + self.valveRecord.get_last_open())
            self.update_log()
        output_valve(1)
    
    def close_valve(self):
        # Logistical stuff only executes if valve is open
        if self.valveWatch.running:
            self.valveWatch.stop()
            self.valveRecord.close_time(time.time())
            self.ui.lastOpenLabel.setText('Last open: ' + self.valveRecord.get_last_open() + " for " + self.valveRecord.get_time_open() + " seconds")
            self.update_log()
        output_valve(0)

    def update_log(self):
        # Update the logging text
        self.ui.logLabel.setText('Open ' + self.valveRecord.times_open() + ' times(s) today\n' +
        'Closed ' + self.valveRecord.times_closed() + ' time(s) today')

    def activate_sensor_mode(self):
        # Activate the sensor mode
        self.waterCheckTimer.start()

    def deactivate_sensor_mode(self):
        # Deactivate the sensor mode
        self.waterCheckTimer.stop()

    def sensor_mode(self):
        # Loop method for sensor mode
        waterDetected = water_detected()

        if waterDetected and not self.valveWatch.running: # Water Detected and valve off
            self.open_valve()
            self.ui.waterLabel.setText("Water Detected\n Valve Open")
        elif not waterDetected and self.valveWatch.running: # No Water Detected and valve on
            self.close_valve()
            self.ui.waterLabel.setText("No Water Detected\n Valve Closed")

    def activate_timed_mode(self):
        # Activate the timed mode
        self.open_valve()
        self.timedValveWatch.start()
        self.timedValveTimer.start()

    def deactivate_timed_mode(self):
        # Deactivate the timed mode
        self.timedValveWatch.stop()
        self.timedValveWatch.reset()
        self.timedValveTimer.stop()

    def timed_mode(self):
        # Loop method for timed mode
        curTimeOpen = int(self.timedValveWatch.value())
        self.ui.timerProgress.setValue(curTimeOpen)
        # If timer exceeded maximum value, exit timed mode
        if curTimeOpen >= self.MAX_OPEN_SECONDS:
            self.timerFinished.emit()

    def update_valve_time(self):
        # Updates the valve's total time open

        # valveWatch should be reset at midnight
        if time.strftime("%H:%M:%S") == "00:00:00":
            self.valveTimeShouldReset = True

        # If valveTimer is running, the valve should be on, so update notificationLabel and check if time exceeded
        if self.valveWatch.running:
            curTimeOpen = self.valveWatch.value()
            self.ui.notificationLabel.setText(str(math.floor(curTimeOpen)) + ' seconds open')

            # Stop everything if exceeded maximum time for the day
            if curTimeOpen >= self.MAX_OPEN_SECONDS:
                self.timeLimitReached.emit()

        # Reset valveTimer if valve is shut off and it should reset
        elif self.valveTimeShouldReset:
            self.valveTimeShouldReset = False
            self.valveWatch.reset()

    def update_clock(self):
        # Updates clockLabel text with current time
        timeDate = time.asctime()
        self.ui.clockLabel.setText(timeDate)
