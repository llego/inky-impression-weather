ip = "http://homeassistant.home:8123"

# Disable Timo's station as it gives wrong temps. Replace with openweathermap
#url = ip + "/api/states/weather.weatherflow_day_based_forecast"
url = ip + "/api/states/weather.openweathermap"

url_indoor_humidity = ip + "/api/states/sensor.ruuvi_humidity_vardagsrummet"
url_indoor_humidity_sovrummet = ip + "/api/states/sensor.ruuvi_humidity_sovrummet"
url_indoor_temp = ip + "/api/states/sensor.ruuvi_temp_vardagsrummet"
url_indoor_temp_sovrummet = ip + "/api/states/sensor.ruuvi_temp_sovrummet"
url_ilmatieteenlaitos = ip + "/api/states/weather.ilmatieteenlaitos_daily"
url_openweathermap = ip + "/api/states/weather.openweathermap"
headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI3Y2NlMzE5YjNhYTg0MTM2YThlYTZiNmY5YzUxMWQxMSIsImlhdCI6MTYzNTg4MDA3NywiZXhwIjoxOTUxMjQwMDc3fQ.rriK0O0fIaz1Be3wNLHddNKQF5V8j3iJaTALCJqPMXk",
    "content-type": "application/json",
}
