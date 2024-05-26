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
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "pico/rc.h"

#define SERVO_PIN      22

const uint OUTPUT_PIN = 22;
const uint MEASURE_PIN = 17;

float measure_duty_cycle(uint gpio) {
    // Only the PWM B pins can be used as inputs.
    assert(pwm_gpio_to_channel(gpio) == PWM_CHAN_B);
    uint slice_num = pwm_gpio_to_slice_num(gpio);

    // Count once for every 100 cycles the PWM B input is high
    pwm_config cfg = pwm_get_default_config();
    pwm_config_set_clkdiv_mode(&cfg, PWM_DIV_B_HIGH);
    pwm_config_set_clkdiv(&cfg, 100);
    pwm_init(slice_num, &cfg, false);
    gpio_set_function(gpio, GPIO_FUNC_PWM);

    pwm_set_enabled(slice_num, true);
    sleep_ms(10);
    pwm_set_enabled(slice_num, false);
    float counting_rate = clock_get_hz(clk_sys) / 100;
    float max_possible_count = counting_rate * 0.01;
    return pwm_get_counter(slice_num) / max_possible_count;
}




int main() {
    stdio_init_all();
    if (cyw43_arch_init()) {
        printf("Wi-Fi init failed");
        return -1;
    }
    printf("ADC Example, measuring GPIO26\n");

    adc_init();

    // Make sure GPIO is high-impedance, no pullups etc
    adc_gpio_init(26);
    // Select ADC input 0 (GPIO26)
    adc_select_input(0);

    // Configure PWM slice and set it running
    // const uint count_top = 1000;
    // pwm_config cfg = pwm_get_default_config();
    // pwm_config_set_wrap(&cfg, count_top);
    // pwm_init(pwm_gpio_to_slice_num(OUTPUT_PIN), &cfg, true);
    // gpio_set_function(OUTPUT_PIN, GPIO_FUNC_PWM);

    rc_servo myServo = rc_servo_init(SERVO_PIN);
    rc_servo_start(&myServo, 90);   // set servo1 na 90 degree
    float ref_voltage = 3.3f; // [V]
    while (1) {
        // 12-bit conversion, assume max value == ADC_VREF == 3.3 V
        const float conversion_factor = ref_voltage / (1 << 12);
        uint16_t result = adc_read();
        double voltage = result * conversion_factor;
        printf("Raw value: 0x%03x, voltage: %f V\n", result, voltage);
        if (voltage > 2.5f) {
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
        } else
        {
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
        }
        float output_duty_cycle = voltage / ref_voltage;
        // pwm_set_gpio_level(OUTPUT_PIN, (uint16_t) (output_duty_cycle * (count_top + 1)));
        float measured_duty_cycle = measure_duty_cycle(MEASURE_PIN);
        printf("Output duty cycle = %.1f%%, measured input duty cycle = %.1f%%\n",
                output_duty_cycle * 100.f, measured_duty_cycle * 100.f);
        uint angle = 70;
        rc_servo_set_angle(&myServo,angle);
        sleep_ms(1000);
    }
}
