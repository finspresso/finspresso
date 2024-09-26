from machine import ADC, Pin
from math import log
import time

adc = ADC(Pin(26))
analogReadResolution = 65535
beta = 3950
TReference = 298.0
KelvinOffset = 273.0


def kelvinToCentigradeClecius(tempK):
    return tempK - KelvinOffset


while True:
    VinAnalog = adc.read_u16()
    tempK = beta / (log(analogReadResolution / VinAnalog - 1) + beta / TReference)
    tempC = kelvinToCentigradeClecius(tempK)
    print(tempC)
    time.sleep(1)
