from machine import Pin, PWM, I2C
from time import sleep
import time_unit
import vacuumtest
import steppertest
import adctest


"-----------------Initialization-----------------"

_NUM_CONTAINERS = const(10)             #num containers
# adc = adctest.adcpinsetup(0,1,0)          #DO WE NEED THIS?

#endregion
"-----------------End Initialization-----------------"

"-----------------Pickup and Drop pill Functions-----------------"
#region Pickup/Drop
def pickup_pill(): #COMPLETE THIS
    vacuumtest.vacuum_on()
    sleep(0.4)

    baseline = adctest.getbaseline()
    print("Baseline Value:", baseline)
    # except Exception as e: print("Initialization error:", e) CHECCK WITH ANDRE

    steppertest.arm_slp.value(1) 
    steppertest.arm_dir.value(0)
    sleep(0.25)
    steppertest.arm_step.value(0)
    arm_pos = 0
    while(not (adctest.checkpillpickup(baseline) and arm_pos <= 100)): #change 100 to whatever step is max depth.
          steppertest.step_arm()
          arm_pos += 1
    #at this point, arm has lowered with vacuum on until ADC hit. Vacuum is on, Stepper is live but not moving.
    sleep(0.25)
    steppertest.arm_dir.value(1)                #direction is reversed to raise arm.


    for i in range(arm_pos):        #step upwards same steps as went downwards.
        steppertest.step_arm()  
    arm_pos = 0                     #reset arm_pos to 0 once at top.
    if(adctest.checkpillpickup(baseline)):  
        print("pill still here!\n")   #check if pill is still there
        sleep(0.25)                  #0.25s delay before dropping pill.
    else:
        print("Pill Dropped. Trying again.\n")
        vacuumtest.vacuum_off()
        sleep(1)
        pickup_pill()
    return 0

def drop_pill():                #Drop Pill will rotate to an opening, drop the pill, and rotate back.
    print("dropping pill!\n")
    steppertest.rotate_to_opening()
    vacuumtest.vacuum_off()
    sleep(0.5)
    print("Pill dropped. Moving back to origin container.")
    steppertest.rotate_back_to_container()
    return 0
#endregion
"-----------------End Pickup and Drop Functions-----------------"

"-----------------Update values, Dispenseforcontainer-----------------"
#region Update/1 dispense sequence
def update_values(amounts, doses):
    for x in range(len(amounts)):
        amounts[x]=amounts[x]-doses[x]

def dispensePill(currentpos, destinationpos, amount):
    
    
        steppertest.rotate_to_container(currentpos, destinationpos)
        for i in range(amount):
            pickup_pill()
            drop_pill()

            return True
#endregion
def Dispenser(data):
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
            doses=data['schedule'][x+1:x+_NUM_CONTAINERS+1]         #Doses has the array that will be used 
            break
    if (doses==[0]):
        return False    # It was not time to dispense.
    
    #begin dispensing using "doses"
    "Calibrate, then set current susan position to 0, then loop through dispensePill, using currentpos, i (container number) and then doses[i] for amount."

    steppertest.calibrate()                 
    currentpos = 0

    for x in range(len(data['amounts'])):
        if doses[x] > data['amounts'][x]:
            print(f"insufficient pills in container {x}")
            return True

    for i in range(_NUM_CONTAINERS):
        if doses[i] != 0:
            dispensePill(currentpos, i, doses[i])
            currentpos += 1
            sleep(0.75)     #delay 0.75s after all pills have been dispensed from a container

        


    update_values(data['amounts'], doses)
    return True         # It was time to dispense.

def reset():
    steppertest.Sleeptoggle('susan', 0)
    vacuumtest.vacuum_off()

if __name__ == "__main__":      #TESTING PURPOSES ONLY
    while(True):
        try:
            vacuumtest.vacuum_on()
            sleep(0.4)

            baseline = adctest.getbaseline()
            print("Baseline Value:", baseline)
            # except Exception as e: print("Initialization error:", e) CHECCK WITH ANDRE

            steppertest.arm_slp.value(1) 
            steppertest.arm_dir.value(0)
            sleep(0.25)
            steppertest.arm_step.value(0)
            arm_pos = 0
            for i in range(500):
                adctest.checkpillpickup(baseline)
                steppertest.step_arm()

            #at this point, arm has lowered with vacuum on until ADC hit. Vacuum is on, Stepper is live but not moving.
            sleep(0.25)
            reset()

        except OSError as e:
                print("Buffering...")
            # print("I2C Error:", e)
                sleep(0.01)  # give bus time to recover
