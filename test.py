import json
from requests import get, exceptions
from datetime import datetime


# curl -X GET -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI3Y2NlMzE5YjNhYTg0MTM2YThlYTZiNmY5YzUxMWQxMSIsImlhdCI6MTYzNTg4MDA3NywiZXhwIjoxOTUxMjQwMDc3fQ.rriK0O0fIaz1Be3wNLHddNKQF5V8j3iJaTALCJqPMXk" "Content-Type: application/json" http://192.168.1.115:8123/api/states/sensor.ruuvi_humidity_vardagsrummet | python3 -m json.tool


### API call to Home Assistant
url_indoor = "http://192.168.1.115:8123/api/states/sensor.ruuvi_humidity_vardagsrummet"

headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI3Y2NlMzE5YjNhYTg0MTM2YThlYTZiNmY5YzUxMWQxMSIsImlhdCI6MTYzNTg4MDA3NywiZXhwIjoxOTUxMjQwMDc3fQ.rriK0O0fIaz1Be3wNLHddNKQF5V8j3iJaTALCJqPMXk",
    "content-type": "application/json",
}

try:
    response = get(url_indoor, headers=headers)
except exceptions.RequestException as e:
    raise SystemExit(e)

json_obj = json.loads(response.text)
#print(json.dumps(json_obj, indent=4))


### Variables for current weather
humidity = round(float(json_obj["state"]))

print("humidity is " + str(humidity) + " %")
