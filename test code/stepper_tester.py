import Vacuum
import stepper
import adc
import time

def test():
    stepper.arm_slp.value(1)
    stepper.raise_arm()
    stepper.arm_dir(0)
    for x in range(stepper.MAX_DEPTH):
        stepper.arm_step.value(not stepper.arm_step.value())
        time.sleep(stepper.arm_delay)
        stepper.arm_step.value(not stepper.arm_step.value())
        try:
            start=time.time_ns()
            value=sensor.read()
            stop=time.time_ns()
            file.write(f'{value}, {stop-start}, {time.time()}\n')
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            stop=time.time_ns()
            file.write(f'{e}, {stop-start}, {time.time()}\n')
            continue
    stepper.raise_arm()
    stepper.arm_slp.value(0)

file_name='ADC_Measurements.csv'
file=open(file_name, mode='w')
file.write(f'Measurement, Measurement Duration (ns), Time (s)')

sensor=adc.adcpinsetup(0,1,0)
sensor.configure()

Vacuum.vacuum_on()
try:
    stepper.Sleeptoggle('arm', 0)
    test()
except KeyboardInterrupt:
    stepper.Sleeptoggle('arm', 0)
    Vacuum.vacuum_off()
stepper.Sleeptoggle('arm', 0)
Vacuum.vacuum_off()
file.close()