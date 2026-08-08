import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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

DISPLAY_PALETTE = [
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
] + [0, 0, 0] * 248

BASE_DIR = Path(__file__).resolve().parent


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


def format_weather_text(
    low_temperature,
    high_temperature,
    humidity,
    precipitation,
    wind_speed,
    current_temperature=None,
) -> str:
    if current_temperature is None:
        temperature = f"Temp: {low_temperature}...{high_temperature}°C"
    else:
        temperature = f"Temp: {current_temperature}°C ({low_temperature}...{high_temperature}°C)"

    return "\n".join(
        [
            temperature,
            f"Fukt: {humidity}%",
            f"Nederbörd: {precipitation} mm",
            f"Vind: {wind_speed} m/s",
        ]
    )


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

    today_text = format_weather_text(
        today_forecast["templow"],
        today_forecast["temperature"],
        humidity,
        today_forecast["precipitation"],
        wind_speed,
        current_temperature=temperature,
    )
    tomorrow_text = format_weather_text(
        tomorrow_forecast["templow"],
        tomorrow_forecast["temperature"],
        tomorrow_forecast["humidity"],
        tomorrow_forecast["precipitation"],
        tomorrow_forecast["wind_speed"],
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
    font_path = os.environ.get("INKY_WEATHER_FONT")
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            print(f"Warning: could not load INKY_WEATHER_FONT={font_path}")

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
    icon_path = BASE_DIR / "icons" / f"{name}.PNG8"
    try:
        return Image.open(icon_path).convert("L")
    except FileNotFoundError:
        fallback_path = BASE_DIR / "icons" / "cloudy.PNG8"
        return Image.open(fallback_path).convert("L")


def load_display_icon(name: str, foreground: int) -> Image.Image:
    icon = load_icon(name)
    display_icon = icon.point(lambda value: WHITE if value > 245 else foreground)
    display_icon.putpalette(DISPLAY_PALETTE)
    return display_icon


def draw_section(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    heading: str,
    icon_name: str,
    text: str,
    heading_position: tuple[int, int],
    color: int,
    heading_font: ImageFont.ImageFont,
    body_font: ImageFont.ImageFont,
) -> None:
    heading_width, heading_height = text_size(draw, heading, heading_font)
    del heading_width
    x_icon = 1
    y_icon = heading_position[1] + heading_height
    icon = load_display_icon(icon_name, color)
    x_text = x_icon + icon.size[0]
    y_text = 20 if heading_position[1] == 1 else y_icon

    image.paste(icon, (x_icon, y_icon))
    draw.text(heading_position, heading, color, heading_font)
    draw.multiline_text((x_text, y_text), text, color, body_font)


def render_report(report: WeatherReport, width: int, height: int) -> Image.Image:
    image = Image.new("P", (width, height), WHITE)
    image.putpalette(DISPLAY_PALETTE)
    draw = ImageDraw.Draw(image)

    font_small = load_font(35)
    font_mini = load_font(20)

    draw.line((1, int(height / 2 - 1), width, int(height / 2 - 1)), fill=RED, width=3)

    timestamp_width, timestamp_height = text_size(draw, report.timestamp, font_mini)
    draw.text((width - timestamp_width, height - timestamp_height), report.timestamp, BLACK, font_mini)

    draw_section(image, draw, "Idag", report.today_icon, report.today_text, (20, 1), BLACK, font_mini, font_small)
    draw_section(
        image,
        draw,
        "Imorgon",
        report.tomorrow_condition,
        report.tomorrow_text,
        (20, int(height / 2 + 3)),
        BLUE,
        font_mini,
        font_small,
    )

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
