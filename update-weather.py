from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import os
from font_fredoka_one import FredokaOne
import json
from requests import get

path = os.path.dirname(os.path.realpath(__file__))

inky_display = auto()
inky_display.set_border(inky_display.BLACK)

### API call to Home Assistant
url = "http://192.168.1.115:8123/api/states/weather.smartweather_loosarintie_3_daily"
headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiNjc5OWFkZTIwYWY0ZjYyOThmNjlhNjNiYTA2NjQ1ZSIsImlhdCI6MTYzNTMxMTAxOSwiZXhwIjoxOTUwNjcxMDE5fQ._OhQEGp-_glKqV48yK6qcMG1zar-XAdDb63phxVmGos",
    "content-type": "application/json",
}
response = get(url, headers=headers)
#print(response.text)
json_obj = json.loads(response.text)


### Variables for current weather
today_cond = json_obj["state"]
temperature = json_obj["attributes"]["temperature"]
humidity = json_obj["attributes"]["humidity"]
wind_bearing = json_obj["attributes"]["wind_bearing"]
wind_speed = json_obj["attributes"]["wind_speed"]
tomorrow_cond = json_obj["attributes"]["forecast"][1]["condition"]
tomorrow_temp = json_obj["attributes"]["forecast"][1]["temperature"]
tomorrow_low = json_obj["attributes"]["forecast"][1]["templow"]

#print(json_obj["attributes"]["forecast"])

today = u"{}°C".format(temperature) + " | " + u"{}%".format(humidity)
tomorrow = tomorrow_cond + " | " + u"{}".format(tomorrow_low) + "..." + u"{}°C".format(tomorrow_temp)
print("today: " + today)
print("tomorrow: " + tomorrow)

#exit()

### Possible conditions
"""    
    "clear-night": ["clear-night"],
    "cloudy": ["cloudy"],
    "exceptional": ["cloudy"],
    "fog": ["foggy"],
    "hail": ["hail"],
    "lightning": ["thunderstorm"],
    "lightning-rainy": ["possibly-thunderstorm-day", "possibly-thunderstorm-night"],
    "partlycloudy": [
        "partly-cloudy-day",
        "partly-cloudy-night",
    ],
    "rainy": [
        "rainy",
        "possibly-rainy-day",
        "possibly-rainy-night",
    ],
    "snowy": ["snow", "possibly-snow-day", "possibly-snow-night"],
    "snowy-rainy": ["sleet", "possibly-sleet-day", "possibly-sleet-night"],
    "sunny": ["clear-day"],
    "windy": ["windy"], 
"""


### Determine icon and convert icon to Inky format
current_icon = json_obj["attributes"]["current_icon"]
icon_path = path+"/icons/"+current_icon+".PNG8"
icon = Image.open(icon_path).convert("RGBA")


### Clean display
for _ in range(2):
    for y in range(inky_display.HEIGHT):
        for x in range(inky_display.WIDTH):
            inky_display.set_pixel(x, y, inky_display.CLEAN)
    inky_display.show()


### Prepare Inky Impression screen
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

for y in range(inky_display.height):
	for x in range(inky_display.width):
		img.putpixel((x, y), inky_display.BLACK)

inky_display.set_image(img)
inky_display.show()
#input("Press Enter to continue...")


### Fonts
font_big = ImageFont.truetype(FredokaOne, 100)
font_small = ImageFont.truetype(FredokaOne, 50)




### Write general weather and icon to display
w_general, h_general = font_small.getsize(today_cond)
w_icon, h_icon = icon.size

x_icon = int(inky_display.WIDTH / 2 - (w_general+w_icon) / 2)
y_icon = 10
x_general = int(x_icon + w_icon + 1)
y_general = int(h_icon / 2 - h_general / 2)

img.paste(icon, (x_icon, y_icon))
draw.text((x_general, y_general), today_cond, inky_display.ORANGE, font_small)

### Write temp and humidity to display
w_today, h_today = font_big.getsize(today)
x_today = int((inky_display.WIDTH / 2) - (w_today / 2))
y_today = int((inky_display.HEIGHT / 2) - (h_today / 2) + 20)
draw.text((x_today, y_today), today, inky_display.YELLOW, font_big)

### Write tomorrow to display
w_tomorrow_label, h_tomorrow_label = font_small.getsize("Tomorrow:")
w_tomorrow, h_tomorrow = font_small.getsize(tomorrow)
x_tomorrow_label = int((inky_display.WIDTH / 2) - (w_tomorrow_label / 2))
x_tomorrow = int((inky_display.WIDTH / 2) - (w_tomorrow / 2))
y_tomorrow = int((inky_display.HEIGHT) - h_tomorrow - 10)

draw.text((x_tomorrow_label, y_tomorrow - 60), "Tomorrow:", inky_display.GREEN, font_small)
draw.text((x_tomorrow, y_tomorrow), tomorrow, inky_display.RED, font_small)

inky_display.set_image(img)
inky_display.show()



