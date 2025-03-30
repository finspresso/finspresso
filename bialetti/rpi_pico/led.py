import machine
import utime


led = machine.Pin("LED", machine.Pin.OUT)

while True:
    led.off()
    utime.sleep_ms(500)
    led.on()
    utime.sleep_ms(500)
