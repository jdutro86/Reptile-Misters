import RPi.GPIO as GPIO # import RPi.GPIO module
from time import sleep
GPIO.setmode(GPIO.BOARD)
GPIO.setup(40, GPIO.IN)
GPIO.setup(38, GPIO.OUT)

try:
  while True:
    if (GPIO.input(40)):
      GPIO.output(38, 1)
      print("Port on")
      
    else:
      GPIO.output(38,0)
      print("Port off")
      
    sleep(0.1)

finally: GPIO.cleanup()
