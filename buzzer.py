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

def wareagle(base = 0.25, volume = 2):
    buzzerfreq(392)
    buzzervolume(volume)
    time.sleep(base * 4)
    buzzerfreq(660)
    time.sleep(base * 2)
    buzzerfreq(587)
    time.sleep(base * 2)
    buzzerfreq(523)
    time.sleep(0.2)
    buzzervolume(0)
    time.sleep(0.1)
    buzzervolume(volume)
    time.sleep(base * 2)
    buzzerfreq(440)
    time.sleep(base)
    buzzerfreq(392)
    time.sleep(1)
    buzzeroff()

if __name__ == "__main__":
    wareagle(0.25, 30)
    
