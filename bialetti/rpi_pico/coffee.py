from machine import ADC, Pin, PWM
from math import log
import utime
import time


# adc = ADC(Pin(26))
analogReadResolution = 65535
beta = 3950
TReference = 298.0
KelvinOffset = 273.0
adc_ponti = ADC(28)
pwm = PWM(Pin(22))
pwm.freq(1000)


def kelvinToCentigradeClecius(tempK):
    return tempK - KelvinOffset


def readTemperature():
    VinAnalog = 3.3  # adc.read_u16()
    tempK = beta / (log(analogReadResolution / VinAnalog - 1) + beta / TReference)
    tempC = kelvinToCentigradeClecius(tempK)
    print(tempC)
    time.sleep(1)


def goToPosition(targetPosition, currentPosition):
    # Move to zero position smoothly
    if currentPosition > targetPosition:
        while currentPosition > targetPosition:
            pwm.duty_u16(currentPosition - 1)
            utime.sleep_ms(2)
            currentPosition = currentPosition - 1
    else:
        while currentPosition < targetPosition:
            pwm.duty_u16(currentPosition + 1)
            utime.sleep_ms(2)
            currentPosition = currentPosition + 1


led = Pin("LED", Pin.OUT)
led.on()
while True:
    reading = adc_ponti.read_u16()
    refVoltage = 3.3
    resolution = 2 ** 16 - 1

    voltage = (reading * refVoltage) / resolution
    print("Voltage: ", voltage)
    print("ADC: ", reading)
    pwm.duty_u16(reading)
    utime.sleep(0.2)
