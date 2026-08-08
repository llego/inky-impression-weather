# Inky Impression Weather

This script reads weather data from Home Assistant and renders a two-panel weather view for an Inky Impression e-paper display.

The development workflow is preview-first: render a local PNG on `laptop`, inspect it, then deploy the same code to the Raspberry Pi Zero that is connected to the display.

![Example](/inky-impression-weather.png)

## Development

Enter the Nix development shell on `laptop`:

```sh
nix develop
```

Create a local `parameters.py` from `parameters.example.py` and fill in the Home Assistant URL, entity URLs, and token. `parameters.py` is ignored by Git and must not be committed.

Render a preview without importing or touching Inky hardware:

```sh
python update-weather.py --output preview.png --no-display
```

## Raspberry Pi Runtime

The Pi Zero needs the Pimoroni Inky libraries installed and a Pi-local `parameters.py`:

```sh
curl https://get.pimoroni.com/inky | bash
```

Run a manual update on the Pi:

```sh
python3 update-weather.py --display
```

## Deployment

Deploy from `laptop` to the Pi Zero:

```sh
rsync -az --delete \
  --exclude .git \
  --exclude __pycache__ \
  --exclude preview.png \
  --exclude parameters.py \
  ./ llego@rpizero.home:/home/llego/inky-impression-weather/
```

See `deploy/README.md` for the user-level `systemd` service and timer setup.
