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

ICON_THERMOMETER = "\uf055"
ICON_RAIN = "\uf084"
ICON_HUMIDITY = "\uf07a"
ICON_WIND = "\uf050"

CONDITION_ICONS = {
    "clear": "\uf00d",
    "clear-day": "\uf00d",
    "clear-night": "\uf02e",
    "cloudy": "\uf013",
    "fog": "\uf014",
    "foggy": "\uf014",
    "hail": "\uf015",
    "lightning": "\uf016",
    "lightning-rainy": "\uf01d",
    "partly-cloudy-day": "\uf002",
    "partly-cloudy-night": "\uf031",
    "partlycloudy": "\uf002",
    "pouring": "\uf019",
    "rainy": "\uf019",
    "snowy": "\uf01b",
    "snowy-rainy": "\uf017",
    "sunny": "\uf00d",
    "thunderstorm": "\uf01e",
    "windy": "\uf021",
}

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
    current_temperature: float
    today_low_temperature: float
    today_high_temperature: float
    today_humidity: int
    today_precipitation: float
    today_wind_speed: float
    today_text: str
    tomorrow_condition: str
    tomorrow_low_temperature: float
    tomorrow_high_temperature: float
    tomorrow_humidity: int
    tomorrow_precipitation: float
    tomorrow_wind_speed: float
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
        current_temperature=temperature,
        today_low_temperature=today_forecast["templow"],
        today_high_temperature=today_forecast["temperature"],
        today_humidity=humidity,
        today_precipitation=today_forecast["precipitation"],
        today_wind_speed=wind_speed,
        today_text=today_text,
        tomorrow_condition=tomorrow_forecast["condition"],
        tomorrow_low_temperature=tomorrow_forecast["templow"],
        tomorrow_high_temperature=tomorrow_forecast["temperature"],
        tomorrow_humidity=tomorrow_forecast["humidity"],
        tomorrow_precipitation=tomorrow_forecast["precipitation"],
        tomorrow_wind_speed=tomorrow_forecast["wind_speed"],
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


def load_symbol_font(size: int) -> ImageFont.ImageFont:
    font_path = os.environ.get("INKY_WEATHER_SYMBOL_FONT")
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            print(f"Warning: could not load INKY_WEATHER_SYMBOL_FONT={font_path}")

    for font_path in (
        BASE_DIR / "fonts" / "weathericons-regular.otf",
        "/run/current-system/sw/share/fonts/opentype/weathericons-regular.otf",
        "/usr/share/fonts/opentype/weathericons-regular.otf",
    ):
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    return load_font(size)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    try:
        bbox = draw.multiline_textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return font.getsize(text)


def draw_symbol_value(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    symbol: str,
    value: str,
    color: int,
    symbol_font: ImageFont.ImageFont,
    value_font: ImageFont.ImageFont,
) -> int:
    symbol_width, _ = text_size(draw, symbol, symbol_font)
    draw.text(position, symbol, color, symbol_font)
    value_x = position[0] + symbol_width + 8
    draw.text((value_x, position[1]), value, color, value_font)
    value_width, _ = text_size(draw, value, value_font)
    return value_x + value_width


def condition_icon(condition: str) -> str:
    return CONDITION_ICONS.get(condition, CONDITION_ICONS["cloudy"])


def render_report(report: WeatherReport, width: int, height: int) -> Image.Image:
    image = Image.new("P", (width, height), WHITE)
    image.putpalette(DISPLAY_PALETTE)
    draw = ImageDraw.Draw(image)

    font_current = load_font(88)
    font_today_detail = load_font(30)
    font_tomorrow = load_font(27)
    font_heading = load_font(22)
    font_mini = load_font(18)
    font_symbol = load_symbol_font(27)
    font_today_condition = load_symbol_font(118)
    font_tomorrow_condition = load_symbol_font(94)

    split_y = int(height * 0.64)
    draw.line((1, split_y, width, split_y), fill=RED, width=3)

    timestamp_width, timestamp_height = text_size(draw, report.timestamp, font_mini)
    draw.text((width - timestamp_width, height - timestamp_height), report.timestamp, BLACK, font_mini)

    draw.text((20, 4), "Idag", BLACK, font_heading)
    draw.text((16, 58), condition_icon(report.today_icon), BLACK, font_today_condition)

    current = f"{report.current_temperature:.1f}°C"
    draw.text((150, 32), current, BLACK, font_current)

    draw_symbol_value(
        draw,
        (150, 150),
        ICON_THERMOMETER,
        f"{report.today_low_temperature:.1f}...{report.today_high_temperature:.1f}°C",
        BLACK,
        font_symbol,
        font_today_detail,
    )
    rain_end = draw_symbol_value(
        draw,
        (150, 194),
        ICON_RAIN,
        f"{report.today_precipitation:.1f} mm",
        BLACK,
        font_symbol,
        font_today_detail,
    )
    draw_symbol_value(
        draw,
        (rain_end + 28, 194),
        ICON_HUMIDITY,
        f"{report.today_humidity}%",
        BLACK,
        font_symbol,
        font_today_detail,
    )
    draw_symbol_value(
        draw,
        (150, 232),
        ICON_WIND,
        f"{report.today_wind_speed:.1f} m/s",
        BLACK,
        font_symbol,
        font_today_detail,
    )

    draw.text((20, split_y + 6), "Imorgon", BLUE, font_heading)
    draw.text((16, split_y + 56), condition_icon(report.tomorrow_condition), BLUE, font_tomorrow_condition)
    tomorrow_x = 132
    tomorrow_y = split_y + 32
    draw_symbol_value(
        draw,
        (tomorrow_x, tomorrow_y),
        ICON_THERMOMETER,
        f"{report.tomorrow_low_temperature:.1f}...{report.tomorrow_high_temperature:.1f}°C",
        BLUE,
        font_symbol,
        font_tomorrow,
    )
    draw_symbol_value(
        draw,
        (tomorrow_x, tomorrow_y + 30),
        ICON_RAIN,
        f"{report.tomorrow_precipitation:.1f} mm",
        BLUE,
        font_symbol,
        font_tomorrow,
    )
    hum_end = draw_symbol_value(
        draw,
        (tomorrow_x, tomorrow_y + 60),
        ICON_HUMIDITY,
        f"{report.tomorrow_humidity}%",
        BLUE,
        font_symbol,
        font_tomorrow,
    )
    draw_symbol_value(
        draw,
        (hum_end + 28, tomorrow_y + 60),
        ICON_WIND,
        f"{report.tomorrow_wind_speed:.1f} m/s",
        BLUE,
        font_symbol,
        font_tomorrow,
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
