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
Another leak was also found. A thread leak. Changed from standard threading to a thread pool. This eliminated the rest of the memory leak. The program is now stable at about 167MB plus or minus 3MB. 

**Key findings:**
- Python code remained flat with only minor growth (~1MB per 15 fetches)
- System-level memory showed 10-15MB growth per fetch
- The leak originated when opening plot files (GDI objects)

**Solution:** Rendering plots directly in the GUI instead of opening saved files eliminated the leak. Current performance shows minor memory growth (~1-3MB per fetch) after many refreshes due to Tkinter/matplotlib internals, stabilizing after 10-15 fetches.
