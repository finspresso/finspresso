import network
from time import sleep
import machine

ssid = "voyager"
password = "uty45323"


def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() is False:
        print("Waiting for connection...")
        sleep(1)
    print(wlan.ifconfig())


try:
    connect()
except KeyboardInterrupt:
    machine.reset()
