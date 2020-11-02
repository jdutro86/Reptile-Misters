from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import QTimer, QStateMachine, QState, pyqtSignal

from PyQt5 import uic
import time


GLOBAL_CONTEXT = {}

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("testUI.ui", self)

        # Find the widgets in the .ui file
 
        self.clockLabel = self.findChild(QLabel, "clockLabel")
        self.lastOpenLabel = self.findChild(QLabel, "lastOpenLabel")
        self.notificationLabel = self.findChild(QLabel, "notificationLabel")

        self.stopButton = self.findChild(QPushButton, "stopButton")
        self.timedSwitch = self.findChild(QPushButton, "timedSwitch")
        self.valveSwitch = self.findChild(QPushButton, "valveSwitch")
        self.sensorSwitch = self.findChild(QPushButton, "sensorSwitch")
        
        self.timerProgress = self.findChild(QProgressBar, "timerProgress")
        self.waterLabel = self.findChild(QLabel, "waterLabel")
        self.logLabel = self.findChild(QLabel, "logLabel")

        # Clock Label updates every half a second
        self.clockTimer = QTimer(self)
        self.clockTimer.timeout.connect(self.update_clock)
        self.clockTimer.start(500)

        self.showFullScreen()
        
        # This is the start of a state machine for the system. Using this we can change the states and text of buttons easily
        # Connecting the methods that will be moved to pin_devices I haven't figure out yet
        
        self.machine = QStateMachine()
        
        self.idle = QState()
        self.manualEnabled = QState()
        self.sensorEnabled = QState()
        self.timerEnabled = QState()
        self.timerRunning = QState(self.timerEnabled)
        self.timerFinished = QState(self.timerEnabled)

        self.idle.assignProperty(self.valveSwitch, "text", "Open Valve")
        self.idle.assignProperty(self.valveSwitch, "enabled", True)
        self.idle.assignProperty(self.sensorSwitch, "text", "Enable\n Water Sensor")
        self.idle.assignProperty(self.sensorSwitch, "enabled", True)
        self.idle.assignProperty(self.timedSwitch, "enabled", True)
        self.idle.addTransition(self.valveSwitch.clicked, self.manualEnabled)
        self.idle.addTransition(self.sensorSwitch.clicked, self.sensorEnabled)
        self.idle.addTransition(self.timedSwitch.clicked, self.timerEnabled)

        self.manualEnabled.assignProperty(self.valveSwitch, "text", "Close Valve")
        self.manualEnabled.assignProperty(self.sensorSwitch, "enabled", False)
        self.manualEnabled.assignProperty(self.timedSwitch, "enabled", False)
        self.manualEnabled.addTransition(self.valveSwitch.clicked, self.idle)
        self.manualEnabled.addTransition(self.stopButton.clicked, self.idle)

        self.sensorEnabled.assignProperty(self.valveSwitch, "enabled", False)
        self.sensorEnabled.assignProperty(self.sensorSwitch, "enabled", True)
        self.sensorEnabled.assignProperty(self.sensorSwitch, "text", "Disable\n Water Sensor")
        self.sensorEnabled.assignProperty(self.timedSwitch, "enabled", False)
        self.sensorEnabled.addTransition(self.sensorSwitch.clicked, self.idle)
        self.sensorEnabled.addTransition(self.stopButton.clicked, self.idle)

        self.timerEnabled.setInitialState(self.timerRunning)
        self.timerEnabled.assignProperty(self.valveSwitch, "enabled", False)
        self.timerEnabled.assignProperty(self.sensorSwitch, "enabled", False)
        self.timerEnabled.assignProperty(self.timedSwitch, "enabled", False)
        self.timerEnabled.addTransition(self.stopButton.clicked, self.idle)
        
        self.machine.addState(self.idle)
        self.machine.addState(self.manualEnabled)
        self.machine.addState(self.sensorEnabled)
        self.machine.addState(self.timerEnabled)
        self.machine.setInitialState(self.idle)
        self.machine.setErrorState(self.idle)
        self.machine.start()

    def print_info(self):
        print("POGU")

    def update_clock(self): # Updates Clock at top banner every 0.5 second (500 miliseconds)
        timeDate = time.asctime()
        self.clockLabel.setText(timeDate) 
