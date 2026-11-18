#include <stdio.h>
#include <string.h>

#include "driver/uart.h"
#include "esp_netif.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs.h"

#include "camera_wifi_config.h"
#include "wifi_setup.h"

typedef struct {
    char ssid[33];
    char password[64];
} wifi_credentials_t;

static const char *const SETTINGS_NAMESPACE = "smartglasses";
static const char *const SETTINGS_KEY = "wifi_v1";
static const char *const SET_PREFIX = "SG WIFI ";

static int hex_digit(char ch)
{
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    return -1;
}

static bool decode_hex(const char *input, char *output, size_t capacity)
{
    size_t length = strlen(input);
    if (length % 2 != 0 || length / 2 >= capacity) return false;
    for (size_t i = 0; i < length; i += 2) {
        int high = hex_digit(input[i]);
        int low = hex_digit(input[i + 1]);
        if (high < 0 || low < 0 || (high == 0 && low == 0)) return false;
        output[i / 2] = (char)((high << 4) | low);
    }
    output[length / 2] = '\0';
    return true;
}

static bool credentials_valid(const wifi_credentials_t *credentials)
{
    size_t ssid_length = strnlen(credentials->ssid, sizeof(credentials->ssid));
    size_t password_length = strnlen(credentials->password, sizeof(credentials->password));
    return ssid_length > 0 && ssid_length < sizeof(credentials->ssid) &&
           password_length < sizeof(credentials->password) &&
           (password_length == 0 || password_length >= 8);
}

bool wifi_setup_load(wifi_config_t *config)
{
    wifi_credentials_t credentials = {0};
    nvs_handle_t handle;
    esp_err_t result = nvs_open(SETTINGS_NAMESPACE, NVS_READONLY, &handle);
    if (result == ESP_OK) {
        size_t size = sizeof(credentials);
        result = nvs_get_blob(handle, SETTINGS_KEY, &credentials, &size);
        nvs_close(handle);
        if (result == ESP_OK && size != sizeof(credentials)) result = ESP_ERR_INVALID_SIZE;
    }
    if (result != ESP_OK || !credentials_valid(&credentials)) {
        if (sizeof(WIFI_SSID) > sizeof(credentials.ssid) ||
            sizeof(WIFI_PASSWORD) > sizeof(credentials.password) ||
            strcmp(WIFI_SSID, "YOUR_WIFI_SSID") == 0 ||
            strcmp(WIFI_PASSWORD, "YOUR_WIFI_PASSWORD") == 0) return false;
        snprintf(credentials.ssid, sizeof(credentials.ssid), "%s", WIFI_SSID);
        snprintf(credentials.password, sizeof(credentials.password), "%s", WIFI_PASSWORD);
    }
    if (!credentials_valid(&credentials)) return false;
    memcpy(config->sta.ssid, credentials.ssid, strlen(credentials.ssid));
    memcpy(config->sta.password, credentials.password, strlen(credentials.password));
    return true;
}

static void respond(const char *response)
{
    puts(response);
    fflush(stdout);
}

static void process_line(char *line)
{
    if (strcmp(line, "SG HELLO") == 0) {
        respond("SG READY 1");
        return;
    }
    if (strcmp(line, "SG STATUS") == 0) {
        wifi_ap_record_t access_point;
        esp_netif_ip_info_t ip;
        esp_netif_t *station = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
        if (station && esp_wifi_sta_get_ap_info(&access_point) == ESP_OK &&
            esp_netif_get_ip_info(station, &ip) == ESP_OK && ip.ip.addr != 0) {
            printf("SG URL http://" IPSTR ":%d/stream\n", IP2STR(&ip.ip), CAMERA_STREAM_PORT);
            fflush(stdout);
        } else {
            respond("SG WAIT");
        }
        return;
    }
    if (strncmp(line, SET_PREFIX, strlen(SET_PREFIX)) != 0) return;

    char *ssid = line + strlen(SET_PREFIX);
    char *separator = strchr(ssid, ',');
    wifi_credentials_t credentials = {0};
    if (separator) *separator = '\0';
    if (!separator || !decode_hex(ssid, credentials.ssid, sizeof(credentials.ssid)) ||
        !decode_hex(separator + 1, credentials.password, sizeof(credentials.password)) ||
        !credentials_valid(&credentials)) {
        respond("SG ERR INVALID");
        return;
    }

    nvs_handle_t handle;
    esp_err_t result = nvs_open(SETTINGS_NAMESPACE, NVS_READWRITE, &handle);
    if (result == ESP_OK) {
        result = nvs_set_blob(handle, SETTINGS_KEY, &credentials, sizeof(credentials));
        if (result == ESP_OK) result = nvs_commit(handle);
        nvs_close(handle);
    }
    if (result != ESP_OK) {
        respond("SG ERR STORAGE");
        return;
    }

    respond("SG SAVED");
    vTaskDelay(pdMS_TO_TICKS(200));
    esp_restart();
}

static void setup_task(void *argument)
{
    char line[200];
    size_t length = 0;
    bool overflow = false;
    for (;;) {
        uint8_t ch;
        if (uart_read_bytes(UART_NUM_0, &ch, 1, portMAX_DELAY) != 1) continue;
        if (ch == '\r') continue;
        if (ch == '\n') {
            line[length] = '\0';
            if (!overflow) process_line(line);
            length = 0;
            overflow = false;
        } else if (length + 1 < sizeof(line)) {
            line[length++] = (char)ch;
        } else {
            overflow = true;
        }
    }
}

void wifi_setup_start(void)
{
    ESP_ERROR_CHECK(uart_driver_install(UART_NUM_0, 512, 0, 0, NULL, 0));
    ESP_ERROR_CHECK(xTaskCreate(setup_task, "wifi_setup", 4096, NULL, 5, NULL) == pdPASS
                    ? ESP_OK : ESP_ERR_NO_MEM);
}
