import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
from requests import exceptions, get


DISPLAY_WIDTH = 600
DISPLAY_HEIGHT = 448
BLACK = 0
WHITE = 1
GREEN = 2
BLUE = 3
RED = 4
YELLOW = 5
ORANGE = 6
CLEAN = 7

PATH = os.path.dirname(os.path.realpath(__file__))


@dataclass
class WeatherReport:
    datasource: str
    today_condition: str
    today_icon: str
    today_text: str
    tomorrow_condition: str
    tomorrow_text: str
    timestamp: str
    indoor_temperature: Optional[int]
    indoor_humidity: Optional[int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render weather for an Inky Impression display")
    parser.add_argument("--output", help="Save rendered image to this path")
    parser.add_argument("--no-display", action="store_true", help="Do not update the Inky display")
    parser.add_argument("--display", action="store_true", help="Update the Inky display")
    parser.add_argument("--width", type=int, default=DISPLAY_WIDTH, help="Preview image width")
    parser.add_argument("--height", type=int, default=DISPLAY_HEIGHT, help="Preview image height")
    return parser.parse_args()


def fetch_json(url: str, headers: dict[str, str]) -> dict:
    try:
        response = get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except exceptions.RequestException as error:
        raise SystemExit(error) from error

    try:
        return response.json()
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON from {url}: {error}") from error


def fetch_optional_sensor(primary_url: str, fallback_url: str, headers: dict[str, str]) -> Optional[int]:
    for url in (primary_url, fallback_url):
        try:
            sensor = fetch_json(url, headers)
            return round(float(sensor["state"]))
        except (KeyError, TypeError, ValueError, SystemExit):
            continue
    return None


def build_report(config) -> WeatherReport:
    current = fetch_json(config.url_fmi, config.headers)
    forecast = fetch_json(config.url_fmi_forecast, config.headers)
    forecast_items = forecast["attributes"]["forecast"]
    today_forecast = forecast_items[0]
    tomorrow_forecast = forecast_items[1]

    datasource = current["attributes"].get("friendly_name", "Home Assistant")
    today_condition = current["state"]
    today_icon = current["attributes"].get("current_icon", today_condition)
    temperature = current["attributes"]["temperature"]
    humidity = current["attributes"]["humidity"]
    wind_speed = round(current["attributes"]["wind_speed"] / 3.6, 1)

    today_text = "\n".join(
        [
            f"Temp: {temperature}°C ({today_forecast['templow']}...{today_forecast['temperature']}°C)",
            f"Fukt: {humidity}%",
            f"Nederbörd: {today_forecast['precipitation']} mm",
            f"Vind: {wind_speed} m/s",
        ]
    )
    tomorrow_text = "\n".join(
        [
            f"Temp: {tomorrow_forecast['templow']}...{tomorrow_forecast['temperature']}°C",
            f"Fukt: {tomorrow_forecast['humidity']}%",
            f"Nederbörd: {tomorrow_forecast['precipitation']} mm",
            f"Vind: {tomorrow_forecast['wind_speed']} m/s",
        ]
    )
    timestamp = f"Uppdaterad {datetime.now().strftime('%Y-%m-%d %H:%M')} från {datasource}"

    indoor_temperature = fetch_optional_sensor(
        config.url_indoor_temp,
        config.url_indoor_temp_sovrummet,
        config.headers,
    )
    indoor_humidity = fetch_optional_sensor(
        config.url_indoor_humidity,
        config.url_indoor_humidity_sovrummet,
        config.headers,
    )

    return WeatherReport(
        datasource=datasource,
        today_condition=today_condition,
        today_icon=today_icon,
        today_text=today_text,
        tomorrow_condition=tomorrow_forecast["condition"],
        tomorrow_text=tomorrow_text,
        timestamp=timestamp,
        indoor_temperature=indoor_temperature,
        indoor_humidity=indoor_humidity,
    )


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        from font_fredoka_one import FredokaOne

        return ImageFont.truetype(FredokaOne, size)
    except (ImportError, OSError):
        for font_path in (
            "/run/current-system/sw/share/X11-fonts/DejaVuSans.ttf",
            "/run/current-system/sw/share/fonts/truetype/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ):
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    try:
        bbox = draw.multiline_textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return font.getsize(text)


def load_icon(name: str) -> Image.Image:
    icon_path = os.path.join(PATH, "icons", f"{name}.PNG8")
    try:
        return Image.open(icon_path).convert("RGBA")
    except FileNotFoundError:
        fallback_path = os.path.join(PATH, "icons", "cloudy.PNG8")
        return Image.open(fallback_path).convert("RGBA")


def render_report(report: WeatherReport, width: int, height: int) -> Image.Image:
    image = Image.new("P", (width, height), BLACK)
    image.putpalette(
        [
            0,
            0,
            0,
            255,
            255,
            255,
            0,
            255,
            0,
            0,
            0,
            255,
            255,
            0,
            0,
            255,
            255,
            0,
            255,
            128,
            0,
            255,
            255,
            255,
        ]
        + [0, 0, 0] * 248
    )
    draw = ImageDraw.Draw(image)

    font_small = load_font(35)
    font_mini = load_font(20)

    today_icon = load_icon(report.today_icon)
    tomorrow_icon = load_icon(report.tomorrow_condition)

    draw.line((1, int(height / 2 - 1), width, int(height / 2 - 1)), fill=RED, width=3)

    timestamp_width, timestamp_height = text_size(draw, report.timestamp, font_mini)
    draw.text((width - timestamp_width, height - timestamp_height), report.timestamp, WHITE, font_mini)

    today_heading_width, today_heading_height = text_size(draw, "Idag", font_mini)
    del today_heading_width
    x_icon = 1
    y_icon = today_heading_height + 1
    x_today = x_icon + today_icon.size[0]
    y_today = 20

    image.paste(today_icon, (x_icon, y_icon), today_icon)
    draw.text((20, 1), "Idag", WHITE, font_mini)
    draw.multiline_text((x_today, y_today), report.today_text, WHITE, font_small)

    tomorrow_heading_width, tomorrow_heading_height = text_size(draw, "Imorgon", font_mini)
    del tomorrow_heading_width
    x_tomorrow_heading = 20
    y_tomorrow_heading = int(height / 2 + 3)
    x_icon_tomorrow = 1
    y_icon_tomorrow = y_tomorrow_heading + tomorrow_heading_height
    x_tomorrow = x_icon_tomorrow + tomorrow_icon.size[0]

    image.paste(tomorrow_icon, (x_icon_tomorrow, y_icon_tomorrow), tomorrow_icon)
    draw.text((x_tomorrow_heading, y_tomorrow_heading), "Imorgon", YELLOW, font_mini)
    draw.multiline_text((x_tomorrow, y_icon_tomorrow), report.tomorrow_text, YELLOW, font_small)

    return image


def show_on_inky(image: Image.Image) -> None:
    from inky.auto import auto

    inky_display = auto()
    inky_display.set_border(inky_display.BLACK)
    inky_display.set_image(image)
    inky_display.show()


def main() -> None:
    args = parse_args()
    if args.no_display and args.display:
        raise SystemExit("Use either --display or --no-display, not both")
    if not args.output and not args.display:
        raise SystemExit("Nothing to do. Use --output preview.png and/or --display")

    try:
        import parameters
    except ImportError as error:
        raise SystemExit("Create parameters.py from parameters.example.py before running") from error

    report = build_report(parameters)
    image = render_report(report, args.width, args.height)

    if args.output:
        image.save(args.output)

    if args.display:
        show_on_inky(image)


if __name__ == "__main__":
    main()
