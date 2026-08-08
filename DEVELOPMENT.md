# Development Workflow

This project should be developed on `laptop`, with the Raspberry Pi Zero treated as the deployment target. The Inky Impression is slow to refresh and its Python libraries are hardware-specific, so the fastest workflow is to render a local preview image first and only update the physical display after the output looks right.

## Recommended Roles

- `laptop`: primary development machine for OpenCode, editing, Git commits, and preview image review.
- `crisuflix`: optional always-on host for Home Assistant access, backups, or remote coordination, but not the best interactive development host because preview images are easier to inspect on `laptop`.
- Raspberry Pi Zero: production runtime connected to the Inky Impression display.

## Current Findings

- The repository is small: `update-weather.py`, `test.py`, image assets, and `README.md`.
- There is no dependency metadata yet, such as `pyproject.toml`, `requirements.txt`, or a Nix shell.
- There is no deployment script or service/timer definition yet.
- `update-weather.py` imports `inky.auto` at module import time, which makes it hard to run on a non-Pi development machine.
- `test.py` contains a Home Assistant long-lived access token. Revoke that token in Home Assistant and avoid committing replacement secrets.
- The README still describes running the script through cron. A `systemd` service and timer would be easier to inspect and debug.

## Target Development Loop

1. Develop on `laptop` with OpenCode.
2. Render a local `preview.png` without touching Inky hardware.
3. Inspect `preview.png` on `laptop`.
4. Commit changes after the preview looks correct.
5. Deploy the committed code to the Pi Zero.
6. Run one manual update on the Pi Zero.
7. Let a `systemd` timer handle regular production updates.

## Preview-First Interface

The script should grow a hardware-independent preview mode, for example:

```sh
python update-weather.py --output preview.png --no-display
```

Production on the Pi should use the display path:

```sh
python update-weather.py --display
```

To support that, the script should be refactored so only the display path imports and initializes `inky.auto`. Rendering should produce a normal Pillow image first. The same rendered image can then either be saved as `preview.png` on `laptop` or sent to the Inky display on the Pi Zero.

## Suggested Code Structure

- Fetch Home Assistant data in a function that returns plain Python data.
- Normalize the weather and indoor sensor values into a small internal data structure.
- Render that data to a Pillow image.
- Save the image to `preview.png` when running in preview mode.
- Send the image to Inky only when running on the Pi Zero in display mode.

This keeps most development independent of the Pi, the Inky libraries, and the slow e-paper refresh cycle.

## Configuration And Secrets

Do not commit Home Assistant tokens, URLs, or machine-local paths.

Recommended options:

- Keep an untracked `parameters.py` on each machine and commit only `parameters.example.py`.
- Or move configuration to environment variables loaded by the shell or the Pi's service file.

Useful values to keep outside Git:

- Home Assistant base URL.
- Home Assistant long-lived access token.
- Weather entity ID.
- Forecast entity ID.
- Indoor temperature and humidity entity IDs.

## Deployment To Pi Zero

The simplest deployment workflow is `rsync` from `laptop` to the Pi Zero:

```sh
rsync -az --delete \
  --exclude .git \
  --exclude __pycache__ \
  --exclude preview.png \
  ./ pi@pi-zero:/home/pi/inky-impression-weather/
```

Then trigger a manual run:

```sh
ssh pi@pi-zero 'cd /home/pi/inky-impression-weather && python3 update-weather.py --display'
```

If the Pi has Git access, another valid workflow is to clone the repo on the Pi and use `git pull --ff-only` before restarting the service.

## Runtime Scheduling

Prefer a user-level `systemd` service and timer over cron.

Expected operational commands on the Pi:

```sh
systemctl --user status inky-weather.service
systemctl --user list-timers
journalctl --user -u inky-weather.service -f
```

This gives better logs, clearer failures, and easier manual restarts than cron.

## Next Improvements

1. Revoke the exposed token from `test.py`.
2. Add `.gitignore` entries for `parameters.py`, `preview.png`, logs, and `__pycache__`.
3. Add `parameters.example.py` or environment-variable based configuration.
4. Refactor `update-weather.py` into fetch, normalize, render, preview, and display steps.
5. Add `--output`, `--no-display`, and `--display` command-line options.
6. Add a `systemd` service and timer template for the Pi Zero.
7. Add a documented or scripted deploy command for laptop-to-Pi updates.
