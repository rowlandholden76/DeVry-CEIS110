"""
NOAA Weather Data Analyzer GUI
==============================

Author:    Rowland Holden
Date:      Feb 23, 2026
Course:    CEIS 101 - Final Project (Enhanced)
Purpose:   Provides a gui for fetching and analyzing NOAA weather data for a specified ZIP code, with 
            visualizations and statistics.

Features:
- display statistics (avg, min, max) for temperature and humidity
- show number of cloudy days in the last ~10 days
- generate and display plots: Standard line plot of temperature & humidity, 
    box plot comparison, and temperature histogram

Output Files:
- weather.png          : Temperature & Humidity over time
- boxplot.png          : Box plot comparison
- temperature_histogram.png : Temperature distribution

Requirements:
- Python 3.x
- customtkinter
- Pillow (PIL)
- noaa_weather_backend.py (must be in the same directory)
- threading (standard library)
- os (standard library)

Note: The noaa_weather_backend returns all available records from the Noaa stations for the various zip codes
     in the requested time window noaa stations have data for. This means the number of records and the time 
     window they cover can vary based on the zip code and station data availability.
"""
import customtkinter as ctk
import tkinter.messagebox as messagebox
from PIL import Image, ImageTk
import threading
import os
import gc

from noaa_weather_backend import RowlandNoaaWeather   

ctk.set_appearance_mode("System")          # "Light", "Dark", "System"
ctk.set_default_color_theme("blue")

class WeatherAppGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Weather Analyzer – Rowland Holden")
        self.geometry("1000x850")
        self.minsize(900, 700)

        self.backend = RowlandNoaaWeather()

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_forcast_data(self, forecast_data) -> None:
        self.results_container = ctk.CTkScrollableFrame(self.overview_tab, width=900, height=400)
        self.results_container.pack(pady=15, fill="both", expand=True)

        header_label = ctk.CTkLabel(self.results_container,
                                    text=f"14 Day Forecast:",
                                    font=("Arial", 16, "bold"))
        header_label.pack(pady=(0, 10))
    
        forcast_frame = ctk.CTkFrame(self.results_container)
        forcast_frame.pack(pady=5, padx=20, fill="x")

        headings = ["Day/Period", "Temp (°F)", "Description", "Chance of Rain"]
        for col, heading in enumerate(headings):
            label = ctk.CTkLabel(forcast_frame, 
                                 text=heading, 
                                 font=("Courier", 15, "bold"), justify="left")
            label.grid(column=col, row=0, sticky="w", pady=5, padx=(0,15))

        for i, period in enumerate(forecast_data):
            chance = period['probabilityOfPrecipitation']['value'] or 0  # default to 0 if None

            # Day / Period Name
            label_day = ctk.CTkLabel(forcast_frame, 
                                     text=period['name'], 
                                     font=("Courier", 15), justify="left")
            label_day.grid(column=0, row=i+1, sticky="w", pady=2, padx=(0,15))

            # Temperature
            label_temp = ctk.CTkLabel(forcast_frame, 
                                      text=f"{period['temperature']}°F", 
                                      font=("Courier", 15), justify="left")
            label_temp.grid(column=1, row=i+1, sticky="w", pady=2, padx=(0,25))

            # Short Forecast / Description
            label_desc = ctk.CTkLabel(forcast_frame, 
                                      text=period['shortForecast'], 
                                      font=("Courier", 15), justify="left")
            label_desc.grid(column=2, row=i+1, sticky="w", pady=2, padx=(0,25))

            # Chance of Rain with conditional coloring
            if chance >= 60:
                color = "red" 
            elif chance >= 30:
                color = "orange"
            else:
                color = "green"
            label_rain = ctk.CTkLabel(forcast_frame, 
                                      text=f"{chance}%", 
                                      font=("Courier", 15), justify="left", 
                                      text_color=color)
            label_rain.grid(column=3, row=i+1, sticky="w", pady=2, padx=(0,15))

    def create_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(pady=10, padx=30, fill="both", expand=True)

        self.overview_tab = self.tabview.add("Overview")
        self.standard_plot_tab = self.tabview.add("Temp & Humidity Plot")

        self.box_plot_tab = self.tabview.add("Box Plot")
        self.temp_histogram_tab = self.tabview.add("Temp Histogram")

        self.raw_data_tab = self.tabview.add("Raw Data")

    def create_input_area(self) -> None:
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=10, padx=30)

        zip_label = ctk.CTkLabel(input_frame, 
                                 text="Enter ZIP Code:", 
                                 font=("Arial", 13))
        zip_label.grid(row=0, column=0, sticky="w", pady=5)

        self.zip_entry = ctk.CTkEntry(input_frame, width=100, placeholder_text="e.g. 98204")
        self.zip_entry.grid(row=0, column=1, sticky="w", pady=5, padx=(10,20))

        fetch_button = ctk.CTkButton(input_frame, 
                                     text="Fetch & Analyze", 
                                     command=self.start_fetch_thread)
        fetch_button.grid(row=0, column=2, sticky="w", pady=5)

    def create_results_container(self) -> None:
        self.results_container = ctk.CTkScrollableFrame(self.overview_tab, width=900, height=400)
        self.results_container.pack(pady=15, fill="both", expand=True)

    def create_widgets(self) -> None:
        # Window Header (shows on all tabs)
        header = ctk.CTkLabel(self, text="Weather Data Analyzer", font=("Arial", 24, "bold"))
        header.pack(pady=(20, 10))

        self.create_input_area() # Only shows on overview tab, but we can easily move it to a more global area if desired
        self.create_tabs()
        
        # Status text at the bottom of the overview tab shows current state 
        # (e.g. "Ready", "Fetching data...", "Analysis complete", "Error: ...") 
        # shows on all tabs but is updated by the overview tab's processes activated by the fetch button
        self.status = ctk.CTkLabel(self, text="Ready", font=("Arial", 13), text_color="gray")
        self.status.pack(pady=(10, 5))

        #self.create_results_container()

    def start_fetch_thread(self) -> None:
        self.status.configure(text="Fetching data from NOAA... Please wait", text_color="orange")
        self.update_idletasks()  # force redraw

        # Clear previous results
        for tab_name in ["Overview", "Temp & Humidity Plot", "Box Plot", "Temp Histogram", "Raw Data"]:
                tab = self.tabview.tab(tab_name)
                for child in tab.winfo_children():
                    if hasattr(child, 'image'):
                        child.image = None          # drop PhotoImage ref early
                    child.destroy()

        #self.create_tabs()  # Recreate the tabs after destroying them to start fresh

        gc.collect()  # Force garbage collection to free memory from previous results before starting new analysis

        # create and start a new thread to run the analysis so the GUI doesn't freeze while waiting for API calls and processing
        thread = threading.Thread(target=self.run_analysis, daemon=True) # daemon=True allows the thread to exit when the main program exits
        thread.start()

    def run_analysis(self) -> None:
        try:
            if self.zip_entry.get().strip() == "":
                self.backend.zip_code = "98204"  # default zip code if none provided
            else:   
                self.backend.zip_code = self.zip_entry.get().strip()

            # Fetch and process data using the backend
            self.temp_list, humidity_list, timestamps = self.backend.init_weather_data()
            self.backend.create_plots(self.temp_list, humidity_list, timestamps)

            # Fetch forecast data and show in the overview tab
            self.raw_forcast_data = self.backend.get_forecast_data()
            self.configure_forcast_data(self.raw_forcast_data)
            # print the raw forcast data in the raw forecast tab (currently just reusing the raw data tab for simplicity, 
            # but could easily be split into a separate tab if desired)
            self.print_raw_forcast_data()

            # We skip console stats printing for GUI version – we'll show them in UI
            # Ensure this runs after the API calls and processing is done, and runs in the main thread to safely update the GUI with results (Thread-safe GUI updates)
            self.after(0, self.show_results, humidity_list) 

            self.print_raw_noaa_data()

            gc.collect()  # Force garbage collection after processing to free memory from large data structures and images

        except Exception as e:
            self.after(0, self.show_error, str(e))

    def print_raw_noaa_data(self) -> None:
        raw_data_text = ctk.CTkLabel(self.raw_data_tab, text="Raw NOAA Data:", font=("Arial", 20, "bold"))
        raw_data_text.pack(pady=(20, 10))

        self.add_history_msg(self.raw_data_tab)

        for weather in self.raw_noaa_data:
            self.backend.convert_temp_to_F(weather)  # Convert temperatures to Fahrenheit for display

        raw_data_frame = ctk.CTkScrollableFrame(self.raw_data_tab, width=900, height=400)
        raw_data_frame.grid_columnconfigure(3, weight=1)
        raw_data_frame.pack(pady=10, padx=30, fill="both", expand=True)

        # headers
        headers = ["Timestamp", "Temperature", "Humidity", "Description"]
        for i, header in enumerate(headers):
            record_header = ctk.CTkLabel(raw_data_frame, 
                                         text=header, 
                                         font=("Courier", 15, "bold"), justify="left")
            record_header.grid(column=i, row=0, sticky="w", pady=5, padx=(0,15))

        # record_header = ctk.CTkLabel(raw_data_frame, text="Timestamp", font=("Courier", 15, "bold"), justify="left")
        # record_header.grid(column = 0, row=0, sticky="w", pady=5, padx=(0,20))
        # record_header = ctk.CTkLabel(raw_data_frame, text="Temperature", font=("Courier", 15, "bold"), justify="left")
        # record_header.grid(column = 1, row=0, sticky="w", pady=5, padx=(0,15))
        # record_header = ctk.CTkLabel(raw_data_frame, text="Humidity", font=("Courier", 15, "bold"), justify="left")
        # record_header.grid(column = 2, row=0, sticky="w", pady=5, padx=(0,15))
        # record_header = ctk.CTkLabel(raw_data_frame, text="Description", font=("Courier", 15, "bold"), justify="left")
        # record_header.grid(column = 3, row=0, sticky="w", pady=5, padx=(0,15))

        for i, record in enumerate(self.raw_noaa_data):
            # record = self.clean_record(record)

            record_label_dte = ctk.CTkLabel(raw_data_frame, 
                                            text=str(record["timestamp"]), 
                                            font=("Courier", 15), justify="left")
            record_label_dte.grid(column = 0, row=i+1, sticky="w", pady=2, padx=(0,20))
            record_label_temp = ctk.CTkLabel(raw_data_frame, 
                                             text=(str(record["temperature"]["value"]) + " °F"), 
                                             font=("Courier", 15), justify="left")
            record_label_temp.grid(column = 1, row=i+1, sticky="w", pady=2, padx=(0,15))
            record_label_humid = ctk.CTkLabel(raw_data_frame, 
                                              text=(str(record["relativeHumidity"]["value"]) + "%"), 
                                              font=("Courier", 15), justify="left")
            record_label_humid.grid(column = 2, row=i+1, sticky="w", pady=2, padx=(0,15))
            record_label_desc = ctk.CTkLabel(raw_data_frame, 
                                             text=str(record["textDescription"]), 
                                             font=("Courier", 15), justify="left")
            record_label_desc.grid(column = 3, row=i+1, sticky="w", pady=2, padx=(0,15) )

    def print_raw_forcast_data(self) -> None:
        self.raw_forcast_data

    def get_hist_days(self) -> int:
        unique_dates = set()  # Use a set to track unique dates without worrying about duplicates
        self.raw_noaa_data = list(self.backend.get_noaa_data())

        if not self.raw_noaa_data:
            return 0
        
        for record in self.raw_noaa_data:
            date = record["timestamp"]
            date = date[:date.find("T")].strip()  # remove timezone and whitespace
            unique_dates.add(date)

        return len(unique_dates)

    def add_history_msg(self, container: ctk.CTkFrame | ctk.CTkTabview) -> None:
        show_days_of_noaa_history = ctk.CTkLabel(container,
                                                 text=(
                                                     f"NOAA historical data covers approximately {len(self.temp_list)} records over "
                                                     f"{self.get_hist_days()} days (varies based on station data availability)"),
                                                 font=("Arial", 16, "bold", "italic"))
        show_days_of_noaa_history.pack(pady=(0, 20))

    def show_results(self, humidity_list) -> None:
        show_history_msg = ctk.CTkLabel(self.results_container,
                                        text=f"Showing historical data for ZIP code: {self.backend.zip_code}",
                                        font=("Arial", 24, "bold"))
        show_history_msg.pack(pady=(20, 10))
        self.add_history_msg(self.results_container)

        # displays the number of cloudy days in the noaa data
        cloudy_label = ctk.CTkLabel(self.results_container,
                                    text=f"Cloudy days in last ~10 days: {self.backend.cloudy_days}",  
                                    font=("Arial", 16, "bold"))
        cloudy_label.pack(pady=(20, 10))

        # Prints the stats from the noaa data in a with temperature stats and humidity stats side by side in the overview tab
        stats_frame = ctk.CTkFrame(self.results_container)
        stats_frame.pack(pady=15, fill="x")
        stats_frame.grid_columnconfigure((0,1), weight=1)

        temp_stats = ctk.CTkLabel(stats_frame,
                                  text="Temperature Statistics\n" +
                                       f"Avg: {round(sum(self.temp_list)/len(self.temp_list),1)}°F\n" +
                                       f"Min: {round(min(self.temp_list),1)}°F\n" +
                                       f"Max: {round(max(self.temp_list),1)}°F",
                                  justify="left", anchor="w")
        temp_stats.grid(row=0, column=0, padx=40, pady=10, sticky="w")

        humid_stats = ctk.CTkLabel(stats_frame,
                                   text="Humidity Statistics\n" +
                                        f"Avg: {round(sum(humidity_list)/len(humidity_list),1)}%\n" +
                                        f"Min: {round(min(humidity_list),1)}%\n" +
                                        f"Max: {round(max(humidity_list),1)}%",
                                   justify="left", anchor="w")
        humid_stats.grid(row=0, column=1, padx=40, pady=10, sticky="w")

        # Creates plots on the respective tabs if the plot files exist (they should if the backend processing completed successfully)
        for plot_name in ["weather.png", "boxplot.png", "temperature_histogram.png"]:
            if os.path.exists(plot_name):
                try:
                    with Image.open(plot_name) as img:                # ← auto-closes file
                        # Make a copy/resized version while file is open
                        img_resized = img.copy()                      # or img.thumbnail() if in-place is ok
                        img_resized.thumbnail((700, 500), Image.LANCZOS)

                        photo = ImageTk.PhotoImage(img_resized)

                        if plot_name == "weather.png":
                            label = ctk.CTkLabel(self.standard_plot_tab, image=photo, text="")
                        elif plot_name == "boxplot.png":
                            label = ctk.CTkLabel(self.box_plot_tab, image=photo, text="")
                        elif plot_name == "temperature_histogram.png":
                            label = ctk.CTkLabel(self.temp_histogram_tab, image=photo, text="")

                        label.image = photo                           # keep strong ref
                        label.pack(pady=10, fill="x")
                        img.close()                 # or .grid() etc.
                except Exception as e:
                    print(f"Error loading plot {plot_name}: {e}")
                    # Optional: show error label in GUI
                    error_lbl = ctk.CTkLabel(self.results_container, text=f"Failed to load {plot_name}", text_color="red")
                    error_lbl.pack(pady=5)
        
        
        # for plot_name in ["weather.png", "boxplot.png", "temperature_histogram.png"]:
        #     if os.path.exists(plot_name):
        #         try:
        #             img = Image.open(plot_name)
        #             img.thumbnail((700, 500))  # reasonable max size
        #             #photo = ImageTk.PhotoImage(img)

        #             if plot_name == "weather.png":
        #                 img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        #                 img_label = ctk.CTkLabel(self.standard_plot_tab, image=img_ctl, text="")
        #             elif plot_name == "boxplot.png":
        #                 img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        #                 img_label = ctk.CTkLabel(self.box_plot_tab, image=img_ctl, text="")
        #             elif plot_name == "temperature_histogram.png":
        #                 img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        #                 img_label = ctk.CTkLabel(self.temp_histogram_tab, image=img_ctl, text="")
               
        #             img_label.pack(pady=15)
        #         except:
        #             pass

        self.status.configure(text="Analysis complete", text_color="green")

    def show_error(self, msg) -> None:
        self.status.configure(text=f"Error: {msg}", text_color="red")

    def on_closing(self) -> None:
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

if __name__ == "__main__":
    app = WeatherAppGUI()
    app.mainloop()