#include <stdio.h>

#include "esp_camera.h"
#include "esp_event.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "nvs_flash.h"

#include "wifi_setup.h"

#define STREAM_BOUNDARY "frameboundary"

static const char *TAG = "smartglasses_cam";

static esp_err_t stream_handler(httpd_req_t *request)
{
    esp_err_t result = httpd_resp_set_type(
        request, "multipart/x-mixed-replace; boundary=" STREAM_BOUNDARY);
    while (result == ESP_OK) {
        camera_fb_t *frame = esp_camera_fb_get();
        if (!frame) {
            ESP_LOGW(TAG, "Camera frame unavailable");
            return ESP_FAIL;
        }

        char header[96];
        int header_length = snprintf(
            header, sizeof(header),
            "\r\n--" STREAM_BOUNDARY "\r\nContent-Type: image/jpeg\r\nContent-Length: %zu\r\n\r\n",
            frame->len);
        result = httpd_resp_send_chunk(request, header, header_length);
        if (result == ESP_OK) {
            result = httpd_resp_send_chunk(request, (const char *)frame->buf, frame->len);
        }
        esp_camera_fb_return(frame);
    }
    return result;
}

static void start_stream_server(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = CAMERA_STREAM_PORT;
    httpd_handle_t server = NULL;
    const httpd_uri_t stream = {
        .uri = "/stream",
        .method = HTTP_GET,
        .handler = stream_handler,
    };
    ESP_ERROR_CHECK(httpd_start(&server, &config));
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &stream));
}

static void wifi_event_handler(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        const ip_event_got_ip_t *event = data;
        ESP_LOGI(TAG, "MJPEG: http://" IPSTR ":%d/stream", IP2STR(&event->ip_info.ip), CAMERA_STREAM_PORT);
        return;
    }

    if (id == WIFI_EVENT_STA_DISCONNECTED) {
        const wifi_event_sta_disconnected_t *event = data;
        ESP_LOGW(TAG, "Wi-Fi disconnected (reason %u); reconnecting", (unsigned)event->reason);
    }
    esp_err_t result = esp_wifi_connect();
    if (result != ESP_OK) {
        ESP_LOGE(TAG, "Wi-Fi connect: %s", esp_err_to_name(result));
    }
}

static void start_wifi(wifi_config_t *config)
{
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_START, wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_DISCONNECTED, wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event_handler, NULL));

    // 설정 모듈이 인증 정보를 관리합니다.
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, config));
    ESP_ERROR_CHECK(esp_wifi_start());
}

void app_main(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    wifi_setup_start();

    wifi_config_t wifi = {0};
    if (!wifi_setup_load(&wifi)) {
        ESP_LOGI(TAG, "Waiting for Wi-Fi setup over USB-UART");
        return;
    }

    // 기존 cam_stream의 ESP32-S3-N16R8 / OV2640 핀 설정입니다.
    const camera_config_t camera = {
        .pin_pwdn = -1,
        .pin_reset = -1,
        .pin_xclk = 15,
        .pin_sccb_sda = 4,
        .pin_sccb_scl = 5,
        .pin_d0 = 11,
        .pin_d1 = 9,
        .pin_d2 = 8,
        .pin_d3 = 10,
        .pin_d4 = 12,
        .pin_d5 = 18,
        .pin_d6 = 17,
        .pin_d7 = 16,
        .pin_vsync = 6,
        .pin_href = 7,
        .pin_pclk = 13,
        .xclk_freq_hz = 20000000,
        .ledc_timer = LEDC_TIMER_0,
        .ledc_channel = LEDC_CHANNEL_0,
        .pixel_format = PIXFORMAT_JPEG,
        .frame_size = FRAMESIZE_QVGA,
        .jpeg_quality = 12,
        .fb_count = 1,
        .fb_location = CAMERA_FB_IN_PSRAM,
        .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
    };
    esp_err_t result = esp_camera_init(&camera);
    if (result != ESP_OK) {
        ESP_LOGE(TAG, "Camera init: %s (0x%x)", esp_err_to_name(result), result);
        return;
    }

    start_stream_server();
    start_wifi(&wifi);
}
