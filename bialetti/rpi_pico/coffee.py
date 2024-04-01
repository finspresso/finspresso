from machine import ADC, Pin, PWM
from math import log
import utime
import time


def kelvinToCentigradeClecius(tempK):
    return tempK - KelvinOffset


def readTemperature():
    VinAnalog = 3.3  # adc.read_u16()
    tempK = beta / (log(analogReadResolution / VinAnalog - 1) + beta / TReference)
    tempC = kelvinToCentigradeClecius(tempK)
    print(tempC)
    time.sleep(1)


def goToPosition(targetPosition, currentPosition):
    print("targetPosition: ", targetPosition)
    print("currentPosition: ", currentPosition)
    if currentPosition > targetPosition:
        while currentPosition > targetPosition:
            pwm.duty_u16(currentPosition - 1)
            utime.sleep_us(10)
            currentPosition = currentPosition - 1
    else:
        while currentPosition < targetPosition:
            pwm.duty_u16(currentPosition + 1)
            utime.sleep_us(10)
            currentPosition = currentPosition + 1


# adc = ADC(Pin(26))
analogReadResolution = 65535
beta = 3950
TReference = 298.0
KelvinOffset = 273.0
adcPonti = ADC(28)
pwm = PWM(Pin(22))
pwm.freq(1000)
led = Pin("LED", Pin.OUT)
led.on()
refVoltage = 3.3
resolution = 2 ** 16 - 1

reading = adcPonti.read_u16()
voltage = (reading * refVoltage) / resolution
print("Testreading:")
print("Voltage: ", voltage)
print("ADC: ", reading)
currentPosition = int(resolution / 2)
pwm.duty_u16(30000)
# Loop to gradually change brightness (optional)
# for duty_cycle in range(0, 65536, 50):
#     pwm.duty_u16(duty_cycle)
#     print("duty_cycle: ", duty_cycle)
#     time.sleep_ms(100)  # Adjust delay for desired speed of change
pwm.deinit()
# while True:
#     targetPosition = adcPonti.read_u16()
#     goToPosition(targetPosition, currentPosition)
#     currentPosition = targetPosition
