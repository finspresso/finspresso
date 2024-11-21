add_executable(pontentiometer
        pontentiometer.c
        )

target_link_libraries(pontentiometer pico_stdlib hardware_adc pico_cyw43_arch_none)

# enable usb output, disable uart output
pico_enable_stdio_usb(pontentiometer 1)
pico_enable_stdio_uart(pontentiometer 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(pontentiometer)

# add url via pico_set_program_url
#example_auto_set_url(pontentiometer)
