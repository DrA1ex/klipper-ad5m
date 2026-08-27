// FlashForge Adventurer 5M eboard support
//
// Copyright (C) 2026, Alexander K <https://github.com/drA1ex>
//
// This file may be distributed under the terms of the GNU GPLv3 license.

#include "gpio.h" // gpio_out_setup
#include "internal.h" // GPIO
#include "sched.h" // DECL_INIT

#define HEATER_POWER_PIN GPIO('B', 7)

static struct gpio_out heater_power;

void
flashforge_ad5m_eboard_init(void)
{
    heater_power = gpio_out_setup(HEATER_POWER_PIN, 1);
}
DECL_INIT(flashforge_ad5m_eboard_init);

void
flashforge_ad5m_eboard_shutdown(void)
{
    gpio_out_reset(heater_power, 0);
}
DECL_SHUTDOWN(flashforge_ad5m_eboard_shutdown);
