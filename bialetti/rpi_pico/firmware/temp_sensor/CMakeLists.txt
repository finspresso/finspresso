add_executable(temp_sensor
        temp_sensor.c
        )

target_link_libraries(temp_sensor
                      pico_stdlib
                      hardware_adc
                      pico_cyw43_arch_none)

# enable usb output, disable uart output
pico_enable_stdio_usb(temp_sensor 1)
pico_enable_stdio_uart(temp_sensor 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(temp_sensor)
