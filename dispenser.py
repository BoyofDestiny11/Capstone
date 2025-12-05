from machine import Pin, PWM, I2C
from time import sleep
import time
import RTC
import Vacuum
import stepper
import adc
import buzzer
import memory


"-----------------Initialization-----------------"

_NUM_CONTAINERS = const(10)             #num containers
global arm_pos                          #current arbitrary position of arm. From 0 (top, calibrated position) to 628 (bottom, MAX_DEPTH).
global susan_pos                        #current container position of the susan.
global attempt                          #attempt # to avoid infinite loop of pickup pill
global noPill
sensor = adc.adcpinsetup(0,1,0)          #DO WE NEED THIS?
clock = RTC.clocksetup(1,3,2)
button = Pin(8, Pin.IN)
#endregion

"-----------------End Initialization-----------------"
def calcheck():
    if(stepper.arm_cal.value() == 0):
         print('Arm Limit switch hit')
"-----------------Pickup and Drop pill Functions-----------------"
#region Pickup/Drop
def pickup_pill(pill_depth = 0): #COMPLETE THIS
    global arm_pos
    global noPill
    noPill = 0
    adccheck = 0
    arm_pos = 0
#turn on vacuum and wait for it to stabilize
    Vacuum.vacuum_on() 
    sleep(0.6)

#getbaseline value for adc.
    baseline = adc.getbaseline(sensor)
# except Exception as e: print("Initialization error:", e) CHECCK WITH ANDRE
    sleep(0.1)
    # stepper.raise_arm(0.001)
#set arm stepper output to 0 to prepare for lowering.
    stepper.arm_step.value(0)
    stepper.arm_dir.value(0)
    
    for x in range(pill_depth):
         stepper.step_arm(.001)
    # while(arm_pos <= stepper.MAX_DEPTH):
            # if(arm_pos <= 250):
            #     stepper.step_arm(0.001)
            #     arm_pos = arm_pos + 1
            # else:
    while(not (adc.checkpillpickup(sensor, baseline)) and (arm_pos + pill_depth) <= stepper.MAX_DEPTH):
        stepper.step_arm(0.05)
        arm_pos = arm_pos + 1
        # print(f'step # {arm_pos}')
#at this point, arm has lowered with vacuum on until ADC hit. Vacuum is on, Stepper is live but not moving.
    sleep(0.25) #delay to ensure pill is secure.
    if(adc.checkpillpickup(sensor, baseline)):
        for x in range(6):
            stepper.step_arm(0.025)
#raise arm back to top position. USE THIS TO RECORD DEPTH REACHED FOR MEMORY IF NEEDED!
    stepper.raise_arm(.001)
    arm_pos = 0                     #reset arm_pos to 0 once at top.
    sleep(0.1)
    # print(adc.checkpillpickup(sensor, baseline))
    for x in range(10):
        if(adc.checkpillpickup(sensor, baseline)):
            adccheck = 1
    if(adccheck == 0):
        buzzer.error(2)
        noPill = 1

    sleep(0.5)
#check if pill is still there when at the top.
    # if(adc.checkpillpickup(sensor, baseline)):
    #     attempt = 0  
    #     sleep(0.25)                  #0.25s delay before dropping pill.
    #     return True

    # else:                            #if pill has dropped, reset, and try again after 1s
    #     Vacuum.vacuum_off()
    #     sleep(1)
    #     attempt = attempt + 1
    #     if(attempt <= 5):
    #         pickup_pill()
    #     else:
    #          print(f'Could no pickup pill after {attempt} attempts')
    #          attempt = 0
    #     return False

def drop_pill():                #Drop Pill will rotate to an opening, drop the pill, and rotate back.
    stepper.rotate_to_opening()
    # susan_pos = susan_pos + 0.5
    Vacuum.vacuum_off()
    sleep(5)
    print("Pill dropped. Moving back to origin container.")
    stepper.rotate_back_to_container()
    # susan_pos = susan_pos - 0.5
    return 0
#endregion
"-----------------End Pickup and Drop Functions-----------------"

"-----------------Update values, Dispenseforcontainer-----------------"
#region Update/1 dispense sequence
def update_values(amounts, doses):
    for x in range(len(amounts)):
        amounts[x]=amounts[x]-doses[x]

def dispensePill(current, destination, amount):
        # stepper.Sleeptoggle('arm', 1)
        # stepper.Sleeptoggle('susan', 1)
        sleep(0.2)

        stepper.rotate_to_container(current, destination)
        stepper.raise_arm()
        for i in range(amount):
            pickup_pill(300)
            if(not noPill):
                drop_pill()
            else: Vacuum.vacuum_off()
        return True
#endregion
def Dispenser(data):
    global arm_pos
    '''
    returns False: not time, True: was time
        If it was time,
            - updates data['last_dose_taken'] with whether the dose was dispensed.
            - updates amounts
    '''
# Get the schedule that corresponds to the current time or return if there is no match.
    current_time=clock.get_minutes()
    doses=[0]
    for x in range(0, len(data['schedule']), _NUM_CONTAINERS+1):
        if (data['schedule'][x]==current_time):
            doses=data['schedule'][x+1:x+_NUM_CONTAINERS+1]         #Doses has the array that will be used 
            break
    if (doses==[0]):
        return data['last_dose_taken']    # It was not time to dispense. Save the last_pill_taken state.
    
    #begin dispensing using "doses"
    "Calibrate, then set current susan position to 0, then loop through dispensePill, using currentpos, i (container number) and then doses[i] for amount."
    #unsleep both steppers and bring both to 0 position:::
    
    for x in range(len(data['amounts'])):
        if doses[x] > data['amounts'][x]:
            print(f"insufficient pills in container {x}")
            data['last_dose_taken'] = False
            memory.save(data)
            return False                # Pill not taken: Insufficient Amounts Case

    buzzer.wareagle(0.25, 10)
    start_time = time.ticks_ms()
    while (time.ticks_ms() - start_time < 15000):
        if(button.value() == 1):
            break
    if(time.ticks_ms() - start_time >= 15000):
        data['last_dose_taken'] = False
        memory.save(data)
        return False

    #Both steppers are in the 0 position.
    
    stepper.Sleeptoggle('susan', 1)
    stepper.Sleeptoggle('arm', 1)
    stepper.raise_arm()
    arm_pos = 0
    stepper.calibrate()                 
    susan_pos = 0
    for i in range(_NUM_CONTAINERS):
        if doses[i] != 0:
            dispensePill(susan_pos, i, doses[i])
            susan_pos = i
            sleep(0.75)     #delay 0.75s after all pills have been dispensed from a container
        


    update_values(data['amounts'], doses)
    stepper.Sleeptoggle('susan', 0)
    stepper.Sleeptoggle('arm', 0)
    data['last_dose_taken'] = False
    memory.save(data)
    return True         # Pills were dispensed. Update last_dose_taken to true.

def reset():
    stepper.Sleeptoggle('susan', 0)
    stepper.Sleeptoggle('arm', 0)
    Vacuum.vacuum_off()

"DEBUGGING PURPOSES ONLY::::"
#region testing
def stepperadcvacuumtest():
    while(True):
            try:
                Vacuum.vacuum_on()
                sleep(0.4)

                baseline = adc.getbaseline()
                print("Baseline Value:", baseline)
                # except Exception as e: print("Initialization error:", e) CHECCK WITH ANDRE

                stepper.arm_slp.value(1) 
                stepper.arm_dir.value(0)
                sleep(0.25)
                stepper.arm_step.value(0)
                arm_pos = 0
                for i in range(500):
                    adc.checkpillpickup(baseline)
                    stepper.step_arm(0)

                #at this point, arm has lowered with vacuum on until ADC hit. Vacuum is on, Stepper is live but not moving.
                sleep(0.25)
                reset()

            except OSError as e:
                    print("Buffering...")
                # print("I2C Error:", e)
                    sleep(0.01)  # give bus time to recover

data={"schedule": [633, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0,
                   990, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0,
                   992, 10, 0, 0, 0, 0, 0, 0, 0, 0, 9],
    "amounts": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
    "last_dose_taken": True,
    "init_time": 975}

def lower_util_ADC_test():

    global arm_pos
    arm_pos = 0
    stepper.Sleeptoggle('arm', 1)
    sleep(0.25)
    pickup_pill()
    sleep(1)
    stepper.Sleeptoggle('arm', 0)
    reset()
def turnonmotors():
     stepper.Sleeptoggle('susan', 1)
     stepper.Sleeptoggle('arm', 1)

if __name__ == "__main__":
    reset()
    # Vacuum.vacuum_on()
    turnonmotors()
    # sleep(0.25)
    # # # pickup_pill(200)
    # # # stepper.Sleeptoggle('susan', 1)
    # # # # # # # # # stepper.rotate_to_opening()
    # # # # # # # # # stepper.rotate_back_to_container()
    stepper.raise_arm(.001)
    stepper.calibrate()
    # # pickup_pill(200)
    # # stepper.rotate_to_container(0,8)
    dispensePill(0, 4, 4)
    sleep(2)
    reset()

