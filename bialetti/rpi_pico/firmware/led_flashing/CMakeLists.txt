add_executable(led_flashing
        led_flashing.c
        )

target_link_libraries(led_flashing
                      pico_stdlib
                      pico_cyw43_arch_none
)

# enable usb output, disable uart output
pico_enable_stdio_usb(led_flashing 1)
pico_enable_stdio_uart(led_flashing 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(led_flashing)
