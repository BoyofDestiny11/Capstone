import time_unit
from micropython import const

_NUM_CONTAINERS = const(10)

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
    current_time=time_unit.now()
    doses=[0]
    for x in range(0, len(data['schedule']), _NUM_CONTAINERS+1):
        if (data['schedule'][x]==current_time):
            doses=data['schedule'][x+1:x+_NUM_CONTAINERS+1]
            break
    if (doses==[0]):
        return False    # It was not time to dispense.
    
    # It is time to dispense. All other dispense code. vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    

    # End other dispense code. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # Update the values based on the schedule for the current time.
    update_values(data['amounts'], doses)
    return True         # It was time to dispense.
    
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