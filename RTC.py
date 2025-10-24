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
        day = self._bcd2dec(data[4])
        month = self._bcd2dec(data[5] & 0x1F)
        year = self._bcd2dec(data[6]) + 2000
        return (year, month, day, hour, minute, second)

    def get_minutes_since_midnight(self):
        _, _, _, hour, minute, _ = self.get_time()
        return hour * 60 + minute

    def set_datetime(self, year, month, day, hour, minute, second=0):
        data = bytearray(7)
        data[0] = self._dec2bcd(second)
        data[1] = self._dec2bcd(minute)
        data[2] = self._dec2bcd(hour)
        data[3] = self._dec2bcd(0)      # day of week (not used)
        data[4] = self._dec2bcd(day)
        data[5] = self._dec2bcd(month)
        data[6] = self._dec2bcd(year - 2000)
        self.i2c.writeto_mem(self.address, 0x00, data)

i2c = I2C(1, scl=Pin(3), sda=Pin(2))
rtc = DS3231(i2c)

# ---- Step 1: Set time once ----
# (year, month, day, hour, minute, second)
# Uncomment next line ONCE to set your correct time
#rtc.set_datetime(2025, 10, 23, 15, 34, 20)

time.sleep(1)

# ---- Step 2: Read it back ----
(y, mo, d, h, m, s) = rtc.get_time()
print("RTC time: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(y, mo, d, h, m, s))
print("Minutes since midnight:", rtc.get_minutes_since_midnight())
