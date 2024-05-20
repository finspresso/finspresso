add_executable(coffee_control
        coffee_control.c
        )

target_link_libraries(coffee_control
                      pico_stdlib
                      hardware_adc
                      pico_cyw43_arch_none
                      hardware_pwm)

# enable usb output, disable uart output
pico_enable_stdio_usb(coffee_control 1)
pico_enable_stdio_uart(coffee_control 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(coffee_control)
