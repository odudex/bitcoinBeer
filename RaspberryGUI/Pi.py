
"""Pi.py: Pi and connected devices Hardware API"""

__author__      = "Eduardo Schoenknecht"
__credits__ = ["Eduardo Schoenknecht", "Felipe Borges Alves", "Paulo Eduardo Alves"]

use_rPi = False
try:
    import RPi.GPIO as GPIO
    use_rPi = True
except ImportError:
    print("This is not a raspberry Pi")

valve = 40  # pin number
FlowSensor = 11
flow_counter = 0
valve_opened = False

def init_hardware():
    if use_rPi:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(valve, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(FlowSensor, GPIO.IN)
        GPIO.add_event_detect(FlowSensor, GPIO.BOTH, handleFlow)

def handleFlow(pin):
    global flow_counter
    if pin == FlowSensor:
        flow_counter += 1

def open_valve():
    global valve_opened
    if use_rPi:
        GPIO.output(valve, GPIO.HIGH)
    valve_opened = True

def close_valve():
    global valve_opened
    if use_rPi:
        GPIO.output(valve, GPIO.LOW)
    valve_opened = False

def cleanIO():
    if use_rPi:
        GPIO.cleanup()
