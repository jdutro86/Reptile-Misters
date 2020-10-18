from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import QTimer, QStateMachine, QState

from PyQt5 import uic
import time


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
        self.waterSwitch = self.findChild(QPushButton, "waterSwitch")
        
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
        self.idle.assignProperty(self.valveSwitch, "text", "Open Valve")
        self.idle.assignProperty(self.valveSwitch, "enabled", True)
        self.idle.assignProperty(self.waterSwitch, "text", "Enable Water Sensor")
        self.demo = QState()
        self.demo.assignProperty(self.valveSwitch, "text", "Sate")
        self.demo.assignProperty(self.waterSwitch, "enabled", False)
        self.sensorEnabled = QState()
        self.waterDetectd = QState()
        self.timedOpen = QState()
        self.timeLimit = QState()
        self.idle.addTransition(self.valveSwitch.clicked, self.demo)
        
        self.machine.addState(self.idle)
        self.machine.setInitialState(self.idle)
        self.machine.start()

    def update_clock(self): # Updates Clock at top banner every 0.5 second (500 miliseconds)
        timeDate = time.asctime()
        self.clockLabel.setText(timeDate) 
