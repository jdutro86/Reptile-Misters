from PyQt5.QtWidgets import QApplication
from pin_devices import rpi_cleanup
from ui import UI

# Constants
MAX_OPEN_SECONDS = 300 # maximum open time per day in actual seconds
SLOW_UPDATE_MS = 500 # time between slower updates in milliseconds
UPDATE_MS = 10 # time between updates in milliseconds

# Main
try:
    app = QApplication([])
    window = UI(UPDATE_MS, SLOW_UPDATE_MS, MAX_OPEN_SECONDS)
    app.exec_()
finally:
    rpi_cleanup()
