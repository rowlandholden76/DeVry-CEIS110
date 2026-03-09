# CEIS110 - Intro to Programming

## Project Files

### 1. Turned-in-Final.py
The actual class final that was turned in.

### 2. Enhanced-Final.py
What I transformed the class final into. There is a huge difference between the two.

### 3. Calculator.py
A practice project I created while taking the class. This wasn't an assignment, but I wanted to challenge myself.

To push myself further, I wrote a calculator that takes an entire expression and prints out the step-by-step process of simplifying it, concluding with the final answer. What makes this unique is my self-imposed constraint: **do this without importing any libraries**. 

This means:
- Parsing and input verification without regular expressions
- Math calculations without the math library
- Handling complex edge cases like unbalanced brackets `(){}[]`, invalid characters, and complex number expressions

Most of the code focuses on error checking, validation, and parsing.

### 4. weather_GUI.py
A GUI created for `noaa_weather_backend.py` that displays:
- A weather forecast
- Historical statistics
- 3 historical plots showing different data perspectives
- Raw data for both forecast and historical information

---

## Notable Issue: Memory Leak Discovery

A significant memory leak was identified in the GUI (~10-15MB per fetch). After thorough investigation using `psutil` and `tracemalloc`, the leak was traced to **native C heap memory**, not the Python code itself.

A second leak was also discovered: a thread leak. By switching from standard threading to a thread pool, the remaining memory leak was eliminated. The program now runs stably at approximately 167MB ±3MB.

**Key findings:**
- Python code remained flat with only minor growth (~1MB per 15 fetches)
- System-level memory showed 10-15MB growth per fetch
- The leak originated when opening plot files (GDI objects)

**Solution:** Rendering plots directly in the GUI instead of opening saved files, and changing from standard threading to a thread pool eliminated the leak. Current performance shows stable memory (167MB ±3MB) after many fetches.


## How to run locally

Quick steps to run the GUI and backend from this repository (Windows):

1. Create and activate a virtual environment (from project root):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Run the GUI:

```powershell
.venv\Scripts\python.exe -m weather_GUI
```

4. Run the backend as a script (optional):

```powershell
.venv\Scripts\python.exe -m noaa_weather_backend
```

Notes:
- The project includes `requirements.txt` and `setup.cfg` for development. We are not publishing to PyPI yet.
- To install the package for development (editable):

```powershell
.venv\Scripts\python.exe -m pip install -e .
```

To uninstall the editable install:

```powershell
.venv\Scripts\python.exe -m pip uninstall weather-analyzer
```

