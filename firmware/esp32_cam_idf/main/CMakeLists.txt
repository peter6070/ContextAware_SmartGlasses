idf_component_register(SRCS "camera_stream.c" "wifi_setup.c"
                       PRIV_REQUIRES esp_driver_uart esp_event esp_http_server esp_netif esp_wifi nvs_flash)

file(GLOB wifi_settings CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/wifi_secrets.h")
if(NOT wifi_settings)
    set(wifi_settings "${CMAKE_CURRENT_SOURCE_DIR}/wifi_secrets.example.h")
endif()
configure_file("${wifi_settings}" "${CMAKE_CURRENT_BINARY_DIR}/camera_wifi_config.h" COPYONLY)
target_include_directories(${COMPONENT_LIB} PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
