# Description
This python script calls the Home Assistant API, pulls information from a weather entity, and shows the current weather and forecast on an Inky Impression e-paper display. I'm using a Raspberry Pi Zero.

Please note that The Inky Impression display is really slow to update, around a minute or so. Furthermore, the Python libraries and documentation are mostly made for other Inky devices, making it really tricky to learn the various tricks and tweaks specific to the Inky Impression. Working with the Inky Impression can get quite tedious!

Please note that I have next to zero experience in programming! I don't expect that this is a stable setup in your environment!

![Example](/inky-impression-weather.png)

# Requirements
1. [Inky Impression e-paper display](https://shop.pimoroni.com/products/inky-impression) 
2. Raspberry Pi (e.g. Zero)
3. [Home Assistant](https://www.home-assistant.io/) running on another machine

# Instructions
1. Install Raspberry Pi OS Lite
2. Connect Raspberry Pi to Inky Impression
3. [Set up Inky python libraries](http://docs.pimoroni.com/inkyphat/)
4. Make sure that you have a suitable weather entity in Home Assistant.
5. Configure a Long-Lived Access Token in Home Assistant
6. Modify the Long-Lived Access Token and IP address in `update-weather.py`
7. Update crontab to run the python script regularly; every 15 mins, for example

`crontab -e`

Add the following line the to the end:

`*/15 * * * * python3 /home/pi/inky-impression-weather/update-weather.py >> out.txt  2>&1` 
