#pragma once

#include <stdbool.h>

#include "esp_wifi.h"

#define CAMERA_STREAM_PORT 81

void wifi_setup_start(void);
bool wifi_setup_load(wifi_config_t *config);
