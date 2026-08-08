ip = "https://home-assistant.example.com"

url_indoor_humidity = ip + "/api/states/sensor.example_indoor_humidity"
url_indoor_humidity_sovrummet = ip + "/api/states/sensor.example_fallback_humidity"
url_indoor_temp = ip + "/api/states/sensor.example_indoor_temperature"
url_indoor_temp_sovrummet = ip + "/api/states/sensor.example_fallback_temperature"
url_fmi = ip + "/api/states/weather.example_current"
url_fmi_forecast = ip + "/api/states/sensor.example_daily_forecast"

headers = {
    "Authorization": "Bearer REPLACE_WITH_HOME_ASSISTANT_TOKEN",
    "content-type": "application/json",
}
