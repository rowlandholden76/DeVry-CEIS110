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
     in the requested time window noaa stations have data for. 
     The backend is currently hard-coded to fetch data for ZIP code 98204, 
     but the GUI is designed to allow dynamic input of ZIP codes in the future. 
     The number of cloudy days is currently a placeholder and will be implemented 
     in the next step after we have the cleaned data available in the GUI.
"""
import customtkinter as ctk
import tkinter.messagebox as messagebox
from PIL import Image, ImageTk
import threading
import os

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
        header_label = ctk.CTkLabel(self.results_container,text=f"14 Day Forecast:",font=("Arial", 16, "bold"))
        header_label.pack(pady=(0, 10))
    
        forcast_frame = ctk.CTkFrame(self.results_container)
        forcast_frame.pack(pady=5, padx=20, fill="x")

        headings = ["Day/Period", "Temp (°F)", "Description", "Chance of Rain"]
        for col, heading in enumerate(headings):
            label = ctk.CTkLabel(forcast_frame, text=heading, font=("Courier", 15, "bold"), justify="left")
            label.grid(column=col, row=0, sticky="w", pady=5, padx=(0,15))

        for i, period in enumerate(forecast_data):
            chance = period['probabilityOfPrecipitation']['value'] or 0  # default to 0 if None

            # Day / Period Name
            label_day = ctk.CTkLabel(forcast_frame, text=period['name'], font=("Courier", 15), justify="left")
            label_day.grid(column=0, row=i+1, sticky="w", pady=2, padx=(0,15))

            # Temperature
            label_temp = ctk.CTkLabel(forcast_frame, text=f"{period['temperature']}°F", font=("Courier", 15), justify="left")
            label_temp.grid(column=1, row=i+1, sticky="w", pady=2, padx=(0,25))

            # Short Forecast / Description
            label_desc = ctk.CTkLabel(forcast_frame, text=period['shortForecast'], font=("Courier", 15), justify="left")
            label_desc.grid(column=2, row=i+1, sticky="w", pady=2, padx=(0,25))

            # Chance of Rain with conditional coloring
            if chance >= 60:
                color = "red" 
            elif chance >= 30:
                color = "orange"
            else:
                color = "green"
            label_rain = ctk.CTkLabel(forcast_frame, text=f"{chance}%", font=("Courier", 15), justify="left", text_color=color)
            label_rain.grid(column=3, row=i+1, sticky="w", pady=2, padx=(0,15))



    def create_widgets(self) -> None:
        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkLabel(self, text="Weather Data Analyzer", font=("Arial", 24, "bold"))
        header.pack(pady=(20, 10))

        # ── Tabs creation ────────────────────────────────────────────────
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(pady=10, padx=30, fill="both", expand=True)

        self.overview_tab = self.tabs.add("Overview")
        self.standard_plot_tab = self.tabs.add("Standard Plot")
        self.box_plot_tab = self.tabs.add("Box Plot")
        self.temp_histogram_tab = self.tabs.add("Temp Histogram")
        self.raw_data_tab = self.tabs.add("Raw Data")
        # ── Input area ───────────────────────────────────────────────────
        input_frame = ctk.CTkFrame(self.overview_tab)
        input_frame.pack(pady=10, padx=30)

        input_frame.grid_columnconfigure(2, weight=1)

        zip_label = ctk.CTkLabel(input_frame, text="ZIP Code:", font=("Arial", 14))#.pack(side="left", padx=(0, 10))
        zip_label.grid(row=0, column=0, padx=(0, 10))

        self.zip_entry = ctk.CTkEntry(input_frame, width=140, placeholder_text="e.g. 98204")
        # May not need this self.zip_entry.insert(0, "98204")
        self.zip_entry.grid(row=0, column=1, padx=(0,2))

        fetch_btn = ctk.CTkButton(input_frame, text="Fetch & Analyze", width=160,
                                 command=self.start_fetch_thread)
        fetch_btn.grid(row=0, column=2, padx=20)

        # ── Status ───────────────────────────────────────────────────────
        self.status = ctk.CTkLabel(self, text="Ready", font=("Arial", 13), text_color="gray")
        self.status.pack(pady=(10, 5))

        # ── Results scrollable area ──────────────────────────────────────
        self.results_container = ctk.CTkScrollableFrame(self.overview_tab, fg_color="transparent")
        self.results_container.pack(pady=10, padx=30, fill="both", expand=True)

    def start_fetch_thread(self) -> None:
        self.status.configure(text="Fetching data from NOAA... Please wait", text_color="orange")
        self.update_idletasks()  # force redraw

        # Clear previous results
        for child in self.results_container.winfo_children():
            child.destroy()

        thread = threading.Thread(target=self.run_analysis, daemon=True)
        thread.start()

    def run_analysis(self) -> None:
        try:
            if self.zip_entry.get().strip() == "":
                self.backend.zip_code = "98204"  # default zip code if none provided
            else:   
                self.backend.zip_code = self.zip_entry.get().strip()

            temp_list, humidity_list, timestamps = self.backend.init_weather_data()
            self.backend.create_plots(temp_list, humidity_list, timestamps)

            self.forcast_data = self.backend.get_forcast_data()
            self.configure_forcast_data(self.forcast_data)
            self.print_raw_forcast_data()

            # We skip console stats printing for GUI version – we'll show them in UI
            self.after(0, self.show_results, temp_list, humidity_list)

            self.print_raw_noaa_data()

        except Exception as e:
            self.after(0, self.show_error, str(e))

    def clean_record(self, record) -> dict:
        new_record = {}
        new_record["timestamp"] = record["timestamp"][1:record["timestamp"].find("+")-1].strip()  # remove brackets and whitespace
        
        record = self.backend.convert_temp_to_F(record)
        if record["temperature"]["value"] is not None: 
            new_record["temperature"] = round(record["temperature"]["value"], 2)
        else:
            new_record["temperature"] = record["temperature"]["value"]
        
        if record["relativeHumidity"]["value"] is not None:
            hum = str(record["relativeHumidity"]["value"]).strip()
            hum = round(float(record["relativeHumidity"]["value"]), 2)
            new_record["relativeHumidity"] = hum
        else:
            new_record["relativeHumidity"] = record["relativeHumidity"]["value"]
        
        new_record["textDescription"] = record["textDescription"].strip()  # remove brackets and whitespace

        return new_record

    def print_raw_noaa_data(self) -> None:
        raw_data_text = ctk.CTkLabel(self.raw_data_tab, text="Raw NOAA Data:", font=("Arial", 14, "bold"))
        raw_data_text.pack(pady=(20, 10))

        raw_data_frame = ctk.CTkScrollableFrame(self.raw_data_tab, width=900, height=400)
        raw_data_frame.grid_columnconfigure(3, weight=1)
        raw_data_frame.pack(pady=10, padx=30, fill="both", expand=True)

        raw_weather_data = self.backend.get_noaa_data()

        # header
        record_header = ctk.CTkLabel(raw_data_frame, text="Timestamp", font=("Courier", 15, "bold"), justify="left")
        record_header.grid(column = 0, row=0, sticky="w", pady=5, padx=(0,20))
        record_header = ctk.CTkLabel(raw_data_frame, text="Temperature", font=("Courier", 15, "bold"), justify="left")
        record_header.grid(column = 1, row=0, sticky="w", pady=5, padx=(0,15))
        record_header = ctk.CTkLabel(raw_data_frame, text="Humidity", font=("Courier", 15, "bold"), justify="left")
        record_header.grid(column = 2, row=0, sticky="w", pady=5, padx=(0,15))
        record_header = ctk.CTkLabel(raw_data_frame, text="Description", font=("Courier", 15, "bold"), justify="left")
        record_header.grid(column = 3, row=0, sticky="w", pady=5, padx=(0,15))

        for i, record in enumerate(raw_weather_data):
            record = self.clean_record(record)

            record_label_dte = ctk.CTkLabel(raw_data_frame, text=str(record["timestamp"]), font=("Courier", 15), justify="left")
            record_label_dte.grid(column = 0, row=i+1, sticky="w", pady=2, padx=(0,20))
            record_label_temp = ctk.CTkLabel(raw_data_frame, text=(str(record["temperature"]) + " °F"), font=("Courier", 15), justify="left")
            record_label_temp.grid(column = 1, row=i+1, sticky="w", pady=2, padx=(0,15))
            record_label_humid = ctk.CTkLabel(raw_data_frame, text=(str(record["relativeHumidity"]) + "%"), font=("Courier", 15), justify="left")
            record_label_humid.grid(column = 2, row=i+1, sticky="w", pady=2, padx=(0,15))
            record_label_desc = ctk.CTkLabel(raw_data_frame, text=str(record["textDescription"]), font=("Courier", 15), justify="left")
            record_label_desc.grid(column = 3, row=i+1, sticky="w", pady=2, padx=(0,15) )

    def print_raw_forcast_data(self) -> None:
        self.forcast_data

    def show_results(self, temp_list, humidity_list) -> None:
        # ── Cloudy days & basic info ─────────────────────────────────────
        cloudy_label = ctk.CTkLabel(self.results_container,
                                    text=f"Cloudy days in last ~10 days: {self.backend.cloudy_days}",  
                                    font=("Arial", 16, "bold"))
        cloudy_label.pack(pady=(20, 10))

        # ── Stats ─────────────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(self.results_container)
        stats_frame.pack(pady=15, fill="x")
        stats_frame.grid_columnconfigure((0,1), weight=1)

        temp_stats = ctk.CTkLabel(stats_frame,
                                  text="Temperature Statistics\n" +
                                       f"Avg: {round(sum(temp_list)/len(temp_list),1)}°F\n" +
                                       f"Min: {round(min(temp_list),1)}°F\n" +
                                       f"Max: {round(max(temp_list),1)}°F",
                                  justify="left", anchor="w")
        temp_stats.grid(row=0, column=0, padx=40, pady=10, sticky="w")

        humid_stats = ctk.CTkLabel(stats_frame,
                                   text="Humidity Statistics\n" +
                                        f"Avg: {round(sum(humidity_list)/len(humidity_list),1)}%\n" +
                                        f"Min: {round(min(humidity_list),1)}%\n" +
                                        f"Max: {round(max(humidity_list),1)}%",
                                   justify="left", anchor="w")
        humid_stats.grid(row=0, column=1, padx=40, pady=10, sticky="w")

        # ── Plots ─────────────────────────────────────────────────────────
        for plot_name in ["weather.png", "boxplot.png", "temperature_histogram.png"]:
            if os.path.exists(plot_name):
                try:
                    img = Image.open(plot_name)
                    img.thumbnail((700, 500))  # reasonable max size
                    #photo = ImageTk.PhotoImage(img)

                    if plot_name == "weather.png":
                        img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        img_label = ctk.CTkLabel(self.standard_plot_tab, image=img_ctl, text="")
                    elif plot_name == "boxplot.png":
                        img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        img_label = ctk.CTkLabel(self.box_plot_tab, image=img_ctl, text="")
                    elif plot_name == "temperature_histogram.png":
                        img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        img_label = ctk.CTkLabel(self.temp_histogram_tab, image=img_ctl, text="")
               
                    img_label.pack(pady=15)
                except:
                    pass

        self.status.configure(text="Analysis complete", text_color="green")

    def show_error(self, msg) -> None:
        self.status.configure(text=f"Error: {msg}", text_color="red")

    def on_closing(self) -> None:
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

if __name__ == "__main__":
    app = WeatherAppGUI()
    app.mainloop()