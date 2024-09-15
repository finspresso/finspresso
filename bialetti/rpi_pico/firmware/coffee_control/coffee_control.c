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
const float MAX_ANGLE = 270.0;

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

// Function to set the servo angle
void set_servo_angle(uint slice_num, uint channel, float angle) {
    // // Convert the angle (0 to 180) to PWM duty cycle
    float min_pulse_width = 600.0f;  // 1 ms
    float max_pulse_width = 2500.0f;  // 2 ms
    float pulse_width = (angle / MAX_ANGLE) * (max_pulse_width - min_pulse_width) + min_pulse_width;
    pwm_set_chan_level(slice_num, PWM_CHAN_A, pulse_width);
    printf("Pulse Width: %f ms \n", pulse_width);
    // Calculate the duty cycle as a percentage (1 ms to 2 ms pulse width in a 20 ms period)
    // uint16_t duty_cycle = (uint16_t)((pulse_width / 20000.0f) * 65535.0f);
    // // Set the PWM duty cycle
    // printf("Output duty cycle: %i \n", duty_cycle);
    // pwm_set_gpio_level(SERVO_PIN, duty_cycle);
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

    // Initialize the chosen GPIO pin for PWM output
    gpio_set_function(SERVO_PIN, GPIO_FUNC_PWM);

    // Find the PWM slice and channel for the chosen GPIO pin
    uint slice_num_servo = pwm_gpio_to_slice_num(SERVO_PIN);
    uint channel_servo = pwm_gpio_to_channel(SERVO_PIN);

    // Set the PWM frequency (50 Hz)
    pwm_set_clkdiv(slice_num_servo, 125.0f);  // Assuming the system clock is 125 MHz
    pwm_set_wrap(slice_num_servo, 19999);     // 20000 cycles per 50 Hz period


    // Enable the PWM slice
    pwm_set_enabled(slice_num_servo, true);
    pwm_set_chan_level(slice_num_servo, PWM_CHAN_A, 1500);


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
        float angle = output_duty_cycle * MAX_ANGLE;
        set_servo_angle(slice_num_servo, channel_servo, angle);
        sleep_ms(20);  // Delay between angle changes

        // float measured_duty_cycle = measure_duty_cycle(MEASURE_PIN);
        // printf("Output duty cycle = %.1f%%, measured input duty cycle = %.1f%%\n",
        //         output_duty_cycle * 100.f, measured_duty_cycle * 100.f);
        //uint angle = 70;
        //rc_servo_set_angle(&myServo,angle);
    }
}
