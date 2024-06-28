from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import os
from font_fredoka_one import FredokaOne
import json
from requests import get, exceptions
from datetime import datetime
import parameters

path = os.path.dirname(os.path.realpath(__file__))

inky_display = auto()
inky_display.set_border(inky_display.BLACK)

url = parameters.url
url_ilmatieteenlaitos = parameters.url_ilmatieteenlaitos
url_openweathermap = parameters.url_openweathermap
url_indoor_temp = parameters.url_indoor_temp
url_indoor_temp_sovrummet = parameters.url_indoor_temp_sovrummet
url_indoor_humidity = parameters.url_indoor_humidity
url_indoor_humidity_sovrummet = parameters.url_indoor_humidity_sovrummet
headers = parameters.headers

# API call to home assistant
try:
    response = get(url, headers=headers)
except exceptions.RequestException as e:
    raise SystemExit(e)

json_obj = json.loads(response.text)
#print(json.dumps(json_obj, indent=4))

if json_obj["state"] == "unavailable":
	print("Smartweather is unavailable. Trying openweathermap")
	try:
		#response = get(url_ilmatieteenlaitos, headers=headers)
		response = get(url_openweathermap, headers=headers)
	except exceptions.RequestException as e:
		raise SystemExit(e)
	json_obj = json.loads(response.text)
	#print(json.dumps(json_obj, indent=4))


### Variables for current weather
datasource = json_obj["attributes"]["friendly_name"]
today_cond = json_obj["state"]
temperature = json_obj["attributes"]["temperature"]
humidity = json_obj["attributes"]["humidity"]
#wind_bearing = json_obj["attributes"]["wind_bearing"]
wind_speed = round(json_obj["attributes"]["forecast"][0]["wind_speed"] / 3.6, 1)
today_high = json_obj["attributes"]["forecast"][0]["temperature"]
tomorrow_cond = json_obj["attributes"]["forecast"][1]["condition"]
tomorrow_temp = json_obj["attributes"]["forecast"][1]["temperature"]
tomorrow_wind_speed = round(json_obj["attributes"]["forecast"][1]["wind_speed"] / 3.6, 1)


try:    
	precipitation_probability = json_obj["attributes"]["forecast"][0]["precipitation_probability"]
except KeyError:
	precipitation_probability = None

try:    
	tomorrow_precipitation_probability = json_obj["attributes"]["forecast"][1]["precipitation_probability"]
except KeyError:
	tomorrow_precipitation_probability = None
	

try:
    today_low = json_obj["attributes"]["forecast"][0]["templow"]
except KeyError:
    today_low = None

try: 
    tomorrow_low = json_obj["attributes"]["forecast"][1]["templow"]
except KeyError:
    tomorrow_low = None




#### Construct report text

if today_low == None:
	temp_info = "Ute " + u"{}°C".format(temperature)
	temp_info_tomorrow = u"{}".format(tomorrow_temp)
else:
	temp_info = "Ute " + u"{}°C".format(temperature) + " (" + u"{}".format(today_low) + "..." + u"{}°C".format(today_high) + ")"
	temp_info_tomorrow = u"{}".format(tomorrow_low) + "..." + u"{}°C".format(tomorrow_temp)
	

if precipitation_probability == None:
	precipitation_mm = json_obj["attributes"]["forecast"][0]["precipitation"]
	precipitation_mm_tomorrow = json_obj["attributes"]["forecast"][1]["precipitation"]
	rain_info = "\nNederbörd: " + u"{} mm".format(precipitation_mm)
	rain_info_tomorrow = "\nNederbörd: " + u"{} mm".format(precipitation_mm_tomorrow)
else:
	rain_info = "\nP(regn): " + u"{} %".format(precipitation_probability)
	rain_info_tomorrow = "\nP(regn): " + u"{} %".format(precipitation_probability)




#### Indoor temperature and humidity
try:
    response_indoor_temp = get(url_indoor_temp, headers=headers)
    response_indoor_humidity = get(url_indoor_humidity, headers=headers)
except exceptions.RequestException as e:
    raise SystemExit(e)

try:
    json_obj_indoor_temp = json.loads(response_indoor_temp.text)
    temp_indoor = round(float(json_obj_indoor_temp["state"]))
    json_obj_indoor_humidity = json.loads(response_indoor_humidity.text)
    humidity_indoor = round(float(json_obj_indoor_humidity["state"]))
except:
    response_indoor_temp = get(url_indoor_temp_sovrummet, headers=headers)
    response_indoor_humidity = get(url_indoor_humidity_sovrummet, headers=headers)
    json_obj_indoor_temp = json.loads(response_indoor_temp.text)
    try:
        temp_indoor = round(float(json_obj_indoor_temp["state"]))
        json_obj_indoor_humidity = json.loads(response_indoor_humidity.text)
        humidity_indoor = round(float(json_obj_indoor_humidity["state"]))
    except:
        temp_indoor = None
        humidity_indoor = None


today = temp_info + \
"\nInne " + u"{}°C".format(temp_indoor) + \
"\nFukt ute " + u"{}%".format(humidity) + ", inne " + u"{}%".format(humidity_indoor) + \
rain_info + \
"\nVind: " + u"{} m/s".format(wind_speed)

tomorrow = temp_info_tomorrow + \
rain_info_tomorrow + \
"\nVind: " + u"{} m/s".format(tomorrow_wind_speed)

timestamp = "Uppdaterad " + datetime.now().strftime("%Y-%m-%d %H:%M") + " från " + datasource

print("today: \n" + today)
print("\n")
print("tomorrow: \n" + tomorrow)
print("\n")
print("timestamp = " + timestamp)

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
try:
	current_icon = json_obj["attributes"]["current_icon"]
except KeyError:
	current_icon = json_obj["state"]

icon_path_current = path+"/icons/"+current_icon+".PNG8"
icon_today = Image.open(icon_path_current).convert("RGBA")

icon_path_tomorrow = path+"/icons/"+tomorrow_cond+".PNG8"
icon_tomorrow = Image.open(icon_path_tomorrow).convert("RGBA")


### Clean display
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
font_small = ImageFont.truetype(FredokaOne, 35)
font_mini = ImageFont.truetype(FredokaOne, 20)


## Draw line and write timestamp
draw.line((1, int(inky_display.HEIGHT/2 - 1), inky_display.WIDTH, int(inky_display.HEIGHT/2 - 1)), fill=inky_display.RED, width=3)

w_timestamp, h_timestamp = font_mini.getsize(timestamp) # timestamp
x_timestamp = inky_display.WIDTH - w_timestamp
y_timestamp = inky_display.HEIGHT - h_timestamp
draw.text((x_timestamp, y_timestamp), timestamp, inky_display.WHITE, font_mini) 


### Write icon, today's weather and timestamp to display
w_today_heading, h_today_heading = font_mini.getsize("Idag") # Today: heading text
w_icon, h_icon = icon_today.size # icon
w_today, h_today = font_small.getsize(today)

x_heading = 20
y_heading = 1
x_icon = 1
y_icon = h_today_heading + 1

x_today = x_icon + w_icon
y_today = 20

img.paste(icon_today, (x_icon, y_icon))
draw.text((x_heading, y_heading), "Idag", inky_display.YELLOW, font_mini)
draw.text((x_today, y_today), today, inky_display.YELLOW, font_small)



### Write tomorrow to display
w_tomorrow_heading, h_tomorrow_heading = font_mini.getsize("Imorgon")
w_icon_tomorrow, h_icon_tomorrow = icon_tomorrow.size # icon
w_tomorrow, h_tomorrow = font_small.getsize(tomorrow)

x_tomorrow_heading = 20
y_tomorrow_heading = int(inky_display.HEIGHT / 2 + 3)

x_icon_tomorrow = 1
y_icon_tomorrow = y_tomorrow_heading + h_tomorrow_heading

x_tomorrow = x_icon_tomorrow + w_icon_tomorrow
# y_tomorrow = int((inky_display.HEIGHT) - h_tomorrow - 10)
# y_tomorrow = int(y_icon_tomorrow + h_icon_tomorrow/2 - h_tomorrow/2)
y_tomorrow = y_icon_tomorrow

img.paste(icon_tomorrow, (x_icon_tomorrow, y_icon_tomorrow))
draw.text((x_tomorrow_heading, y_tomorrow_heading), "Imorgon", inky_display.GREEN, font_mini)
draw.text((x_tomorrow, y_tomorrow), tomorrow, inky_display.GREEN, font_small)

inky_display.set_image(img)
inky_display.show()

