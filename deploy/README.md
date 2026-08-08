# Deployment

Develop and preview on `laptop`, then deploy the repository to the Pi Zero.

```sh
rsync -az --delete \
  --exclude .git \
  --exclude __pycache__ \
  --exclude preview.png \
  --exclude parameters.py \
  ./ llego@rpizero.home:/home/llego/inky-impression-weather/
```

Keep `/home/llego/inky-impression-weather/parameters.py` on the Pi. Create it from `parameters.example.py` and put the real Home Assistant URL, entity URLs, and token there.

Run one manual display update after deploying:

```sh
ssh llego@rpizero.home 'cd /home/llego/inky-impression-weather && python3 update-weather.py --display'
```

Install the user service and timer on the Pi:

```sh
ssh llego@rpizero.home 'mkdir -p ~/.config/systemd/user && cp ~/inky-impression-weather/deploy/inky-weather.* ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now inky-weather.timer'
```

Useful operational commands on the Pi:

```sh
systemctl --user status inky-weather.service
systemctl --user list-timers
journalctl --user -u inky-weather.service -f
```
