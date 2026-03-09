# Usage

Run the GUI (from the project root or installed environment):

```bash
# From the repo virtualenv
.venv/Scripts/python.exe -m weather_GUI
# Or use the console script (after installation)
.venv/Scripts/weather-gui
```

Run the backend as a script:

```bash
.venv/Scripts/python.exe -m noaa_weather_backend
# Or
.venv/Scripts/noaa-weather
```

Notes:
- This project intentionally does not package the `docs/` directory into the distribution.
- Dependencies are listed in `requirements.txt` and `setup.cfg`.
