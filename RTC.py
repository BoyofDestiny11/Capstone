from machine import I2C, Pin
import time


class DS3231:
    def __init__(self, i2c, address=0x68):
        self.i2c = i2c
        self.address = address

    def _bcd2dec(self, bcd):
        return (bcd >> 4) * 10 + (bcd & 0x0F)

    def _dec2bcd(self, dec):
        return ((dec // 10) << 4) | (dec % 10)

    def get_time(self):
        data = self.i2c.readfrom_mem(self.address, 0x00, 7)
        second = self._bcd2dec(data[0] & 0x7F)
        minute = self._bcd2dec(data[1])
        hour = self._bcd2dec(data[2] & 0x3F)
        return (hour, minute, second)

    def get_minutes(self):
        hour, minute, _ = self.get_time()
        return hour * 60 + minute

    def set_time(self, hour, minute, second=0):
        data = bytearray(3)
        data[0] = self._dec2bcd(second)
        data[1] = self._dec2bcd(minute)
        data[2] = self._dec2bcd(hour)
        self.i2c.writeto_mem(self.address, 0x00, data)


def clocksetup(I2cv, sclp, sdap):   

    i2c = I2C(I2cv, scl=Pin(sclp), sda=Pin(sdap))
    rtc = DS3231(i2c)
    return rtc

# ---- Step 1: Set time once ----
# (year, month, day, hour, minute, second)
# Uncomment next line ONCE to set your correct time
#rtc.set_time(11, 6, 0)

#time.sleep(1)
#setup is I2C #, then SCL, then SDA pins.
# rtc = clocksetup(1, 3, 2)
# # ---- Step 2: Read it back ----
# (h, m, s) = rtc.get_time()
# print("RTC time:  {:02d}:{:02d}:{:02d}".format(h, m, s))
# print("Minutes since midnight:", rtc.get_minutes())
