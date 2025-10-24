from micropython import const
from machine import Pin
from time import sleep

# --------------------
# Parameters
# --------------------
_STEP_DEGREE = const(1.8 / 4)       # degrees per step /x where x = microstep value.
_DELAY       = const(0.0025)        # half-period _DELAY between step toggles
_STEPS_TO_OPENING = const(40)       #10 * microstep value
_NUM_CONTAINERS = const(10)

_CRANE_DIR_LOWER = const(1)         # Define which dir lowers/raises *your* arm; flip 0/1 here if needed.
_CRANE_DIR_RAISE = const(0)

CONTAINERS = [0, 36, 72, 108, 144, 180, 216, 252, 288, 324] # Disc container locations (degrees)

_cal = Pin(18, Pin.IN)              # Static calibration input (unchanged for both motors)

# --------------------
# Minimal Stepper class
# --------------------
class Stepper:
    """
    Only shared method is `step(n, dir=0)`.
    Each instance carries its own pins and position.
    dir: 0 = forward (increasing degrees), 1 = backward (decreasing)
    """
    def __init__(self, name, dir_pin, step_pin, slp_pin, _STEP_DEGREE=_STEP_DEGREE, _DELAY=_DELAY):
        self.name         = name
        self._dir         = Pin(dir_pin,  Pin.OUT)
        self._step        = Pin(step_pin, Pin.OUT)
        self._slp         = Pin(slp_pin,  Pin.OUT)
        self._STEP_DEGREE  = float(_STEP_DEGREE)
        self._DELAY        = float(_DELAY)
        # self.pos_deg      = 0.0  # tracked 0..360

    # def _bump_pos(self, dir_):
    #     # Update logical position each full step (on every "rising" toggle)
    #     if dir_ == 0:
    #         self.pos_deg += self._STEP_DEGREE
    #     else:
    #         self.pos_deg -= self._STEP_DEGREE
    #     # normalize to [0, 360)
    #     while self.pos_deg >= 360.0: self.pos_deg -= 360.0
    #     while self.pos_deg <   0.0: self.pos_deg += 360.0

    def step(self, n, dir=0):
        # n counts full steps; we toggle pin twice per step
        n = int(round(n))
        if n <= 0:
            return

        self._slp.value(1)            # wake
        self._dir.value(dir)
        sleep(0.25)                    # driver settle
        self._step.value(0)

        for i in range(2 * n):         # on/off toggles
            self._step.value(1 - self._step.value())
            # if (i % 2) == 0:           # count once per full step
            #     self._bump_pos(dir)
            sleep(self._DELAY)

        sleep(0.25)
        self._slp.value(0)             # sleep


# --------------------
# Motor instances
# --------------------
# Motor 1: Susan
Susan = Stepper(
    name="Susan",
    dir_pin=12,   # required
    step_pin=10,  # required
    slp_pin=14,   # required
)

# Motor 2: Crane (arm)
Crane = Stepper(
    name="Crane",
    dir_pin=12,
    step_pin=10,
    slp_pin=14,
)

# --------------------
# Helpers for Susan
# --------------------
def calcstep(current_idx, destination_idx):
    """
    current_idx, destination_idx are container indices (0..9).
    Strategy: never wrap across 0/360 to avoid limit switch; choose straight shot.
    Returns: (steps, direction)
    """
    cur_deg = CONTAINERS[current_idx]
    dst_deg = CONTAINERS[destination_idx]
    delta   = dst_deg - cur_deg

    direction = 0 if destination_idx >= current_idx else 1
    degrees   = abs(delta)
    steps     = int(round(degrees / _STEP_DEGREE))
    return steps, direction

def rotate_to_container(current_idx, destination_idx):
    steps, direction = calcstep(current_idx, destination_idx)
    Susan.step(steps, direction)

def rotate_to_opening():
    Susan.step(_STEPS_TO_OPENING, 1)

def rotate_back_to_container():
    Susan.step(_STEPS_TO_OPENING, 0)

def calibrate_disc():
    # Step Susan until the calibration switch trips, then zero Susan's logical position
    while _cal.value() == 0:
        Susan.step(1, 0)
    Susan.pos_deg = 0.0

def fullRot_susan():
    Susan.step(int(round(360.0 / _STEP_DEGREE)), 0)

# --------------------
# Helpers that use CRANE (arm only)
# --------------------
def Lower_arm():
    #Code for lowering arm
    return True

def Raise_arm():
    #code for Raising Arm
    return True

# --------------------
# Main dispense sequence (Susan for disc; Crane for arm)
# --------------------
def dispensePill(currentpos, destinationpos, amount):
    """
    currentpos/destinationpos are container indices (0..9).
    amount = number of pills to dispense.
    arm_*_steps let you tune the arm travel without touching the helpers.
    """
    rotate_to_container(currentpos, destinationpos)

    for _ in range(amount):
        #Pickup_Pill()
        #Detect_Pill()
        Raise_arm()
        #Detect_Pill()
        rotate_to_opening()
        #Detect_Pill()
        #Drop_Pill()
        rotate_back_to_container()

    return True

# Code to update amounts if pills are dispensed.
def update_values(amounts, doses):
    for x in range(len(amounts)):
        amounts[x]=amounts[x]-doses[x]

# Top-level dispenser function
def dispenser(data):
    '''
    returns False: not time, True: was time
        If it was time,
            - updates data['last_dose_taken'] with whether the dose was dispensed.
            - updates amounts
    '''
    # Get the schedule that corresponds to the current time or return if there is no match.
    current_time=time_unit.now()    # Wrong now because time_unit was done differently.

    doses=[0]
    for x in range(0, len(data['schedule']), _NUM_CONTAINERS+1):
        if (data['schedule'][x]==current_time):
            doses=data['schedule'][x+1:x+_NUM_CONTAINERS+1]
            break
    if (doses==[0]):
        return False    # It was not time to dispense.
    
    # It is time to dispense. All other dispense code. vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    
    # Trigger Alert

    # Wait for button

    # Dispense Pills
    dispensePill()
    # End other dispense code. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # Update the values based on the schedule for the current time.
    update_values(data['amounts'], doses)
    return True         # It was time to dispense.


# Test Code
def test_dispenser():
    data={"schedule": [2, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0,
                       5, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0,
                       8, 10, 0, 0, 0, 0, 0, 0, 0, 0, 9],
            "amounts": [10, 0, 3, 0, 0, 0, 0, 3, 0, 9],
            "last_dose_taken": True,
            "init_time": 0}
    
    while(True):
        wasTime=dispenser(data)
        print(data)
        if (wasTime):
            return
