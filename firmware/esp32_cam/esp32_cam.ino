// Freenove ESP32-S3 WROOM 후보 핀 배치입니다. 실제 보드와 일치 확인 후 사용하세요.
// 참고: https://github.com/Freenove/Freenove_ESP32_S3_WROOM_Board
#include <WiFi.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "wifi_secrets.h"  // wifi_secrets.example.h를 복사해 작성; Git에 올리지 마세요.

#ifndef CONFIRM_FREENOVE_CAMERA_PINOUT
#error "보드 핀 배치를 확인한 후 wifi_secrets.h에서 CONFIRM_FREENOVE_CAMERA_PINOUT을 정의하세요."
#endif

static const char* BOUNDARY = "frameboundary";
static httpd_handle_t server = nullptr;

static esp_err_t stream_handler(httpd_req_t* req) {
  esp_err_t result = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frameboundary");
  while (result == ESP_OK) {
    camera_fb_t* frame = esp_camera_fb_get();
    if (!frame) return ESP_FAIL;
    char header[96];
    int len = snprintf(header, sizeof(header),
      "--%s\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
      BOUNDARY, static_cast<unsigned>(frame->len));
    result = httpd_resp_send_chunk(req, header, len);
    if (result == ESP_OK) result = httpd_resp_send_chunk(req, reinterpret_cast<const char*>(frame->buf), frame->len);
    if (result == ESP_OK) result = httpd_resp_send_chunk(req, "\r\n", 2);
    esp_camera_fb_return(frame);
  }
  return result;
}

void setup() {
  Serial.begin(115200);
  camera_config_t camera = {};
  camera.ledc_channel = LEDC_CHANNEL_0;
  camera.ledc_timer = LEDC_TIMER_0;
  camera.pin_d0 = 11; camera.pin_d1 = 9; camera.pin_d2 = 8; camera.pin_d3 = 10;
  camera.pin_d4 = 12; camera.pin_d5 = 18; camera.pin_d6 = 17; camera.pin_d7 = 16;
  camera.pin_xclk = 15; camera.pin_pclk = 13; camera.pin_vsync = 6; camera.pin_href = 7;
  camera.pin_sccb_sda = 4; camera.pin_sccb_scl = 5;
  camera.pin_pwdn = -1; camera.pin_reset = -1;
  camera.xclk_freq_hz = 10000000;
  camera.pixel_format = PIXFORMAT_JPEG;
  camera.frame_size = FRAMESIZE_QVGA;
  camera.jpeg_quality = 12;
  camera.fb_count = 1;
  camera.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  camera.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  esp_err_t err = esp_camera_init(&camera);
  if (err != ESP_OK) {
    Serial.printf("Camera init error: 0x%x\n", err);
    return;
  }
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 30000) {
    delay(500);
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi connection failed; reset to retry.");
    return;
  }
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 81;
  httpd_uri_t uri = {};
  uri.uri = "/stream";
  uri.method = HTTP_GET;
  uri.handler = stream_handler;
  if (httpd_start(&server, &config) != ESP_OK || httpd_register_uri_handler(server, &uri) != ESP_OK) {
    Serial.println("HTTP server start failed.");
    return;
  }
  Serial.print("MJPEG: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");
}

void loop() {
  delay(1000);
}
