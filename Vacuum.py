from machine import Pin, I2C, PWM
import time
import Vacuum

# --- MCP3424 Driver ---
class MCP3424:
    def __init__(self, i2c, address=0x68):
        self.i2c = i2c
        self.address = address
        self.resolution = 12
        self.config = 0x00

    def configure(self, channel=1, resolution=12, gain=1, continuous=False):
        chan_bits = {1: 0x00, 2: 0x20, 3: 0x40, 4: 0x60}[channel]
        res_bits = {12: 0x00, 14: 0x04, 16: 0x08, 18: 0x0C}[resolution]
        gain_bits = {1: 0x00, 2: 0x01, 4: 0x02, 8: 0x03}[gain]

        mode_bit = 0x10 if continuous else 0x00

        self.resolution = resolution
        self.config = 0x80 | chan_bits | mode_bit | res_bits | gain_bits

        # Start conversion
        self.i2c.writeto(self.address, bytes([self.config]))

    def read(self):
        if self.resolution == 18:
            length = 4  # 3 data + 1 status
        else:
            length = 3  # data + status
        for _ in range(5):  # retry up to 5 times
            data = self.i2c.readfrom(self.address, length)
            status = data[-1]
            if not (status & 0x80):  # conversion ready
                break
            time.sleep(0.05)
        else:
            print("Conversion not ready after retries")
            return None


        data = self.i2c.readfrom(self.address, length)
        status = data[-1]
        if status & 0x80:
            print("Conversion not ready")
            return
        if self.resolution == 18:
            # First 3 bytes contain 18-bit result
            raw = (data[0] << 16) | (data[1] << 8) | data[2]
            # Align to signed 18-bit
            raw >>= 6   # drop the two unused LSBs
            if raw & 0x20000:   # check sign bit (bit 17)
                raw -= 1 << 18
        else:
            raw = (data[0] << 8) | data[1]
            if raw & 0x8000:
                raw -= 1 << 16

        return raw

def adcpinsetup(sclvalue, sdavalue):
    # --- Setup I2C and ADC ---
    i2c = I2C(0, scl=Pin(sclvalue), sda=Pin(sdavalue), freq=100000)
    adc = MCP3424(i2c)
    return adc


#This just tells you what device it is. 

#print("I2C devices:", i2c.scan())



def getbaseline():
    adc.configure(channel=1, resolution=18, gain=1, continuous=False)
    time.sleep(0.3)
    baseline = adc.read()
    return baseline

def readadcvalue():
    adc.configure(channel=1, resolution=18, gain=1, continuous=False)
    time.sleep(0.3)
    value = adc.read()
    return value
#For right now, this code returns a 0 for a pill has not been picked up OR a pill pickup error
# and a 1 for if a pill has been picked up. I also have the print commands but these can be commented out. 
def checkpillpickup(baseline, value):
    print("ADC Raw Value:", value)
    if value is None or baseline is None:
        print ("ADC Read Error Delay")
        return 0
    if (((value < baseline - 30) or (value > baseline + 30)) & (value > 1000)):    
        print (" Pill picked up")
        return 1


while(True):
    try:        
        #baseline and value need the adc var to be called adc in order to read in any value. 
        #This main code is just a placeholder for Luke to see how the OSError and the adc setup is supposed to flow.
        # DO NOT INCLUDE THIS IN THE FINAL DESIGN
        adc = adcpinsetup(1,0) # sets up the pins with 0 as the scl and 1 as the sda and initilizing the I2c connection
        Vacuum.vacuum_on() #have to turn on vacuum in order to get the adc values
        baseline = getbaseline() #this is 
        value = readadcvalue()
        checkpillpickup(baseline, value)


        print("Placeholder")
               # print("Pill picked up!")
           # voltage = to_voltage(value)
            #print("Voltage:", voltage)

    except OSError as e:
        print("I2C Error:", e)
        time.sleep(0.5)  # give bus time to recover
