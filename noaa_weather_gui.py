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
        self.title("NOAA Weather Analyzer – Rowland Holden")
        self.geometry("1000x850")
        self.minsize(900, 700)

        self.backend = RowlandNoaaWeather()

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        input_frame.pack(pady=10, padx=30, fill="x")

        input_frame.grid_columnconfigure(3, weight=1)

        zip_label = ctk.CTkLabel(input_frame, text="ZIP Code:", font=("Arial", 14))#.pack(side="left", padx=(0, 10))
        zip_label.grid(row=0, column=0, padx=(0, 10))

        self.zip_entry = ctk.CTkEntry(input_frame, width=140, placeholder_text="e.g. 98204")
        # May not need this self.zip_entry.insert(0, "98204")
        self.zip_entry.grid(row=0, column=1, padx=10)

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
            # For now we will just set the zip code in the backend to whatever is in the entry box, but we will need to add some 
            # validation here in the future.
            self.backend.zip_code = self.zip_entry.get().strip()
            temp_list, humidity_list, timestamps = self.backend.init_weather_data()
            self.backend.create_plots(temp_list, humidity_list, timestamps)
            # We skip console stats printing for GUI version – we'll show them in UI

            self.after(0, self.show_results, temp_list, humidity_list)

        except Exception as e:
            self.after(0, self.show_error, str(e))

    def print_raw_data(self) -> None:
        raw_data_text = ctk.CTkLabel(self.raw_data_tab, text="Raw NOAA Data:", font=("Arial", 14, "bold"))
        raw_data_text.pack(pady=(20, 10))

        raw_data_frame = ctk.CTkScrollableFrame(self.raw_data_tab)
        raw_data_frame.pack(pady=10, padx=30, fill="both", expand=True)

        raw_weather_data = self.backend.get_noaa_data()

        # print(weather["timestamp"], "\t",
        #   weather["temperature"]["value"], " °F\t",
        #   weather["relativeHumidity"]["value"], "\t",
        #   weather["textDescription"], "\t",)

        for record in raw_weather_data:
            record_label = ctk.CTkLabel(raw_data_frame, text=(str(record["timestamp"]) + "\t",
                str(record["temperature"]["value"]) + " °F\t",
                str(record["relativeHumidity"]["value"]) + "%\t",
                str(record["textDescription"]) + "\t",), 
                font=("Courier", 15), justify="left")
            
            record_label.pack(anchor="w", pady=2)

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

        self.print_raw_data()

        self.status.configure(text="Analysis complete", text_color="green")

    def show_error(self, msg) -> None:
        self.status.configure(text=f"Error: {msg}", text_color="red")

    def on_closing(self) -> None:
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

if __name__ == "__main__":
    app = WeatherAppGUI()
    app.mainloop()