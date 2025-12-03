from machine import Pin, PWM
import time

dutycycle2 = int(65535 * .02)

pwm =  PWM(Pin(9))


def buzzeroff():
    pwm.duty_u16(0)

def buzzervolume(duty_cycle = 2):
    duty = int((duty_cycle * 0.01 * 65535))
    pwm.duty_u16(duty)

def buzzerfreq(freq = 500):
    pwm.freq(freq)


if __name__ == "__main__":
    while True:
        buzzerfreq(500)
        buzzervolume(2)
    
