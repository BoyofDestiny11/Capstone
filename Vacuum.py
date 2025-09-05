from machine import Pin, PWM
from time import sleep

vac = machine.Pin(15) #this is the pin for the pwm vacuum
vac_pwm = PWM(vac)

#Set PWM frequency
frequency = 4000
vac_pwm.freq (frequency)


def vacuum_on():
    #do stuff pwm
    vac_pwm.duty_u16(65536)

def vacuum_off():
    #do stuff
    
    vac_pwm.duty_u16(0)

def test():
    vacuum_on()
    sleep(3)
    vacuum_off()
    sleep(5)