from machine import Pin
p28 = Pin(28, Pin.IN)
p27 = Pin(27, Pin.IN)
def SwitchCheck(susan, vacuum):
    if ((susan == 1) & (p28.value() == 0)):
        print("Susan position 0")
        return 1
    
    if ((vacuum == 1) & (p27.value() == 0)):
        print("Vacuum position 0")
        return 1
    else:
        return 0

while(1):
    SwitchCheck(1,1)

