from machine import Pin
from time import sleep

# Pin Setup
susan_dir = Pin(12, Pin.OUT)                 #direction pin for susan
susan_step = Pin(10, Pin.OUT)                #step pin for susan
susan_slp = Pin(14, Pin.OUT)                 #slp pin for susan

_cal = Pin(0, Pin.IN)                         #calibration pin CHANGE THIS

arm_dir = Pin(12, Pin.OUT)                    #direction pin for arm CHANGE THIS
arm_step = Pin(10, Pin.OUT)                   #step pin for arm CHANGE THIS
arm_slp = Pin(14, Pin.OUT)                    #sleep pin for arm CHANGE THIS

containers = [0, 36, 72, 108, 144, 180, 216, 252, 288, 324] #update the container with location of that container in degrees.

#PARAMETERS
step_degree = 1.8/4                       # number of degrees per step.
susan_delay = 0.01                      #1/2 susan_delay between steps
arm_delay = 0.01                        #1/2 of arm delay
steps_to_opening = 20                   #10 x microstep value

def step(n, dir = 0):                   #function that performs n steps in dir direction (0 = forward, 1 = backwards.) Default is forwards.
    global susan_step
    global susan_dir
    global susan_pos
    global susan_slp
    susan_slp.value(1)
    susan_dir.value(dir)
    sleep(0.25)
    susan_step.value(0)
    for i in range(2 * n):              # 2 * n because each step needs 1 on pulse and 1 off pulse.
        susan_step.value(not susan_step.value())
        if i % 2 == 0 :                 #every positive step signal, increment position by however far in degrees the motor has moved
            # if dir == 0: susan_pos += step_degree
            # if dir == 1: susan_pos -= step_degree
            # if susan_pos == 360: susan_pos = 0      #position cycles 360 degrees.
            # if susan_pos == -1: susan_pos = 359
            print(f"step {i/2 + 1} completed")
        sleep(susan_delay)
    sleep(.25)
    susan_slp.value(0)

def calibrate():
    while _cal.value() == 0:            #step until calibrated
        step(1) 
    print("calibrated.\n")

def fullRot():                          #executes 1 full rotation of the motor
    step(360/step_degree)

def calcstep(current, destination):
    cur_deg = containers[current]
    dst_deg = containers[destination]
    delta = dst_deg - cur_deg

    if destination >= current:
        direction = 0                   # forward (increasing degrees)
        degrees = abs(delta)
    else:
        direction = 1                   # backward (decreasing degrees)
        degrees = abs(delta)

    steps = degrees / step_degree
    return int(round(steps)), direction


def rotate_to_container(current, destination):
    steps, direction = calcstep(current, destination)
    # print(f'Stepping {steps} steps in {direction} direction to move from container at position {containers.index(current)} to container at position {containers.index(destination)}')
    step(steps, direction)

def rotate_to_opening():
    step(steps_to_opening, 1)

def rotate_back_to_container():
    step(steps_to_opening, 0)

def Sleeptoggle(motor, value):      #'susan', 0 sleeps susan etc..
    if motor == 'susan':
        susan_slp.value(value)
    if motor == 'arm':
        arm_slp.value(value)
def step_arm(): #increments Arm by 1 step.

    arm_step.value(not arm_step.value())
    sleep(arm_delay)
    arm_step.value(not arm_step.value())
    return 0
