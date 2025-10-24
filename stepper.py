from machine import Pin
from time import sleep


# Pin Setup
_dir = Pin(12, Pin.OUT)                 #direction pin
_step = Pin(10, Pin.OUT)                #step pin.
_cal = Pin(18, Pin.IN)                  #this should be an input signal that triggers when the disc reaches a zero location to calibrate the stepper motor
_slp = Pin(14, Pin.OUT)
_rst = Pin(13, Pin.OUT)

#Global Variables
pos = 0                                 #position of the disc in degrees
containers = [0, 36, 72, 108, 144, 180, 216, 252, 288, 324] #update the container with location of that container in degrees.
testcur = 0
testnext = 0

#PARAMETERS
step_degree = 1.8/                      # number of degrees per step.
delay = 0.01                            #1/2 delay between steps
steps_to_opening = 40

def step(n, dir = 0):                   #function that performs n steps in dir direction (0 = forward, 1 = backwards.) Default is forwards.
    global _step
    global _dir
    global pos
    global _slp
    _slp.value(1)
    _dir.value(dir)
    sleep(0.25)
    _step.value(0)
    for i in range(2 * n):              # 2 * n because each step needs 1 on pulse and 1 off pulse.
        _step.value(not _step.value())
        if i % 2 == 0 :                 #every positive step signal, increment position by however far in degrees the motor has moved
            if dir == 0: pos += step_degree
            if dir == 1: pos -= step_degree
            if pos == 360: pos = 0      #position cycles 360 degrees.
            if pos == -1: pos = 359
        sleep(delay)
    sleep(.25)
    _slp.value(0)
def calibrate():
    while _cal.value() == 0:            #step until calibrated
        step(1)
    pos = 0                             #position reset to 0 when calibrated   

def fullRot():                          #executes 1 full rotation of the motor
    step(360/step_degree)
    
def step1(n, dir=0):
    """
    Perform n steps with short acceleration and deceleration phases
    using global `delay` as the base timing (default = 0.01 s).
    """
    global _step, _dir, _slp, pos, step_degree, delay

    # parameters for ramp profile
    accel_steps = max(1, min(20, n // 4))    # use up to 1/4 of steps for accel/decel
    slow_factor = 2.0                        # start ~2× slower than base delay

    # create per-step delay list (half-cycle timing per edge)
    delays = []
    for i in range(n):
        if i < accel_steps:  # acceleration phase
            scale = slow_factor - (slow_factor - 1.0) * (i / accel_steps)
        elif i >= n - accel_steps:  # deceleration phase
            scale = slow_factor - (slow_factor - 1.0) * ((n - i) / accel_steps)
        else:  # cruise
            scale = 1.0
        delays.append(delay * scale / 2.0)   # half-period delay

    # enable driver and set direction
    _slp.value(1)
    sleep(0.02)
    _dir.value(dir)
    _step.value(0)

    # main stepping loop
    for i in range(n):
        half = delays[i]
        _step.value(1)
        sleep(half)

        # update position on rising edge
        if dir == 0:
            pos += step_degree
        else:
            pos -= step_degree

        if pos >= 360:
            pos -= 360
        elif pos < 0:
            pos += 360

        _step.value(0)
        sleep(half)

    sleep(0.02)
    _slp.value(0)

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

def rst():
    _slp.value(1)
    _rst.value(0)
    sleep(0.75)
    _rst.value(1)
    _slp.value(0)

if __name__ == "__main__":                          #code to test for proper behavior
    _slp.value(0)
    _rst.value(1)
    rotate_to_container(0, 5)
    
