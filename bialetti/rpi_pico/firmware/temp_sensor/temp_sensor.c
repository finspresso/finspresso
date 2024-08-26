/**
 * Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/adc.h"
#include "pico/cyw43_arch.h"
#include "hardware/clocks.h"
#include <math.h>



#define MEASURE_PIN    26


int main() {
    stdio_init_all();
    if (cyw43_arch_init()) {
        printf("Wi-Fi init failed");
        return -1;
    }
    printf("ADC Example, measuring GPIO26\n");

    adc_init();

    // Make sure GPIO is high-impedance, no pullups etc
    adc_gpio_init(MEASURE_PIN);
    // Select ADC input 0
    adc_select_input(0);

    float ref_voltage = 3.3f; // [V]
    int analog_read_resolution = 4096; // 12-bit ADC
    int beta =  3950;
    float T_reference = 298.0; // Reference temperature in Kelvin of the resistor
    // Turn on LED
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
    while (1) {
        // 12-bit conversion, assume max value == ADC_VREF == 3.3 V
        const float conversion_factor = ref_voltage / (1 << 12);
        uint16_t adc_reading = adc_read();
        double voltage = adc_reading * conversion_factor;
        printf("Raw value: 0x%03x, voltage: %f V\n", adc_reading, voltage);
        float temp_K = beta / (log(analog_read_resolution / (float)adc_reading - 1) + beta / T_reference);
        float temp_C = temp_K - 273.0;
        printf("Temperature: %fC\n", temp_C);
        sleep_ms(300);
    }
}
