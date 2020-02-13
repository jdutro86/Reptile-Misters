import RPi.GPIO as GPIO # import RPi.GPIO module
import threading
from time import sleep
GPIO.setmode(GPIO.BOARD)
GPIO.setup(40, GPIO.IN)
GPIO.setup(38, GPIO.OUT)

def flowStart():
    print("Random")
  ##  timer = time.time()
    #3while timer < 20:
      ##  print (timer)
    ##return
    

try:
    while True:
        if (GPIO.input(40)):
            GPIO.output(38, 1)
            ##call flowrate, start a timer for it
            ##flow = flowStart()
            ##flow.flowStart()
            timer = threading.Timer(2.0, flowStart)
            timer.start()
            while timer < 20:
                print(timer)
                
            ##print ("Port on")
            
        else:
            GPIO.output(38, 0)
            print ("Port off")
            
        sleep(0.1)
        
finally: GPIO.cleanup()        
 

