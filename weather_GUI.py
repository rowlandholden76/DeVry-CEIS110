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

        # The tab view will never be destroyed when reseting for new zip, create it here. 
        self.tabs = ctk.CTkTabview(self)

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_tabs(self) -> None:
        self.forecast_tab = self.tabs.add("Forecast")
        self.hist_stats_tab = self.tabs.add("Historical Statistics")
        self.std_plot_tab = self.tabs.add("Standard Plot")
        self.box_plot_tab = self.tabs.add("Box Plot")
        self.temp_hist_tab = self.tabs.add("Temperature Histogram")
        self.hist_raw_data_tab = self.tabs.add("Historical Raw Data")
        self.forecast_raw_data_tab = self.tabs.add("Forecast Raw Data")

    def create_frames(self) -> None:
        # Input Frame for ZIP code and Fetch button
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10)
        self.input_frame.grid_columnconfigure(2, weight=1)

        # Now pack the tabs so the input frame is at the top of the window
        self.tabs.pack(expand=True, fill="both", padx=30, pady=10)

        # Forecast Frame for displaying weather forecast
        self.forecast_frame = ctk.CTkScrollableFrame(self.forecast_tab)
        self.forecast_frame.pack(pady=5, padx=20, fill="x")

        # Statistics frame header to be seperate from the grid
        self.stats_frame_header = ctk.CTkFrame(self.hist_stats_tab)
        self.stats_frame_header.pack(pady=(10,0))

        # Statistics Frame for displaying weather statistics
        self.stats_frame = ctk.CTkFrame(self.hist_stats_tab)
        self.stats_frame.grid_columnconfigure((0,1), weight=1)
        self.stats_frame.pack(pady=15, fill="x")

        # Plot Frames for displaying generated plots
        self.std_plot_frame = ctk.CTkFrame(self.std_plot_tab)
        self.std_plot_frame.pack(pady=10)

        self.box_plot_frame = ctk.CTkFrame(self.box_plot_tab)
        self.box_plot_frame.pack(pady=10)

        self.temp_hist_frame = ctk.CTkFrame(self.temp_hist_tab)
        self.temp_hist_frame.pack(pady=10)

        # Raw Data Frames for displaying raw data in text format
        self.hist_raw_data_frame = ctk.CTkScrollableFrame(self.hist_raw_data_tab,width=900, height=400)
        self.hist_raw_data_frame.grid_columnconfigure(3, weight=1)    
        self.hist_raw_data_frame.pack(pady=10, padx=30, fill="both", expand=True)

        # Forecast raw data frame
        self.forecast_raw_data_frame = ctk.CTkScrollableFrame(self.forecast_raw_data_tab, width=900, height=400)
        self.forecast_raw_data_frame.pack(pady=10, padx=30, fill="both", expand=True)

    def create_widgets(self) -> None:
        # Title Label
        self.title_label = ctk.CTkLabel(self, text="NOAA Weather Data Analyzer", font=ctk.CTkFont("Arial", size=24, weight="bold"))
        self.title_label.pack(pady=20)

        # Create Tabs
        self.create_tabs()
        # Create Frames
        self.create_frames()

        # create static widgets that do not contain data that needs to be reset when fetching new data for a different zip code.
        zip_label = ctk.CTkLabel(self.input_frame, 
                                 text="Enter ZIP Code:", 
                                 font=("Arial", 13))
        zip_label.grid(row=0, column=0, sticky="w", pady=5)

        self.zip_entry = ctk.CTkEntry(self.input_frame, width=100, placeholder_text="e.g. 98204")
        self.zip_entry.grid(row=0, column=1, sticky="w", pady=5, padx=(10,20))

        fetch_button = ctk.CTkButton(self.input_frame, 
                                     text="Fetch & Analyze", 
                                     command=self.start_fetch_thread)
        fetch_button.grid(row=0, column=2, sticky="w", pady=5)
        
        # Forecast header
        forecast_label = ctk.CTkLabel(self.forecast_frame, text="14 Day Weather Forecast", font=ctk.CTkFont("Arial", size=20, weight="bold"))
        forecast_label.pack(pady=(0, 10))

        # Raw Forecast Data header
        forecast_raw_data_lable = ctk.CTkLabel(self.forecast_raw_data_frame, text="Raw Forecast Data (JSON format)", font=ctk.CTkFont("Arial", size=20, weight="bold"))
        forecast_raw_data_lable.pack(pady=10, padx=10)

        # Noaa raw data header
        raw_data_text = ctk.CTkLabel(self.hist_raw_data_frame, text="Raw NOAA Data:", font=ctk.CTkFont("Arial", size=20, weight="bold"))
        raw_data_text.pack(pady=(20, 10))

        # Statistics Header
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Weather Statistics", font=ctk.CTkFont("Arial", size=20, weight="bold"))
        self.stats_label.pack(pady=10)

        # Status Label for displaying messages to the user
        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont("Arial",size=12), text_color="green")
        self.status_label.pack(pady=(10,15))

    def clear_previous_data(self) -> None:
        # Clear Forecast Frame
        for widget in self.forecast_frame.winfo_children():
            widget.destroy()

        # Clear Statistics Frame
        for widget in self.stats_frame.winfo_children():
                widget.destroy()

        # Clear Plot Frames
        for frame in [self.std_plot_frame, self.box_plot_frame, self.temp_hist_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        # Clear Raw Data Frames
        for frame in [self.hist_raw_data_frame, self.forecast_raw_data_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

    def start_fetch_thread(self) -> None:
        # Update stuatus label to indicate data fetching
        self.status_label.configure(text="Fetching data...", text_color="orange")
        self.update_idletasks()  # Ensure the status label updates immediately

        # Clear Previous Data and Plots
        self.clear_previous_data()

        # Start a new thread to fetch data to avoid blocking the GUI
        fetch_thread = threading.Thread(target=self.run_analysis, daemon=True)
        fetch_thread.start()

    def get_data(self) -> None:
        self.forecast_data = self.backend.get_forecast_data()
        self.noaa_data = list(self.backend.get_noaa_data())

        # Convert temperatures to Fahrenheit for all records in noaa_data
        for weather in self.noaa_data:
            self.backend.convert_temp_to_F(weather)

        self.temp_list, self.humidity_list, self.timestamps = self.backend.init_weather_data()

    def get_unique_days(self) -> int:
        unique_days = set()
        for timestamp in self.timestamps:
            day = timestamp.split("T")[0]  # Extract the date part (YYYY-MM-DD)
            unique_days.add(day)
        return len(unique_days)

    def print_records_message(self) -> str:
        num_records = len(self.noaa_data)
        unique_days = self.get_unique_days()
        message = f"Fetched {num_records} records across {unique_days} days from NOAA stations for ZIP code {self.backend.zip_code}."
        return message

    def run_analysis(self) -> None:
        if self.zip_entry.get().strip() == "":
            self.backend.zip_code = "98204"  # Default ZIP code if none provided
        else:
            self.backend.zip_code = self.zip_entry.get().strip()

        try:
            self.get_data()
            self.backend.create_plots(self.temp_list, self.humidity_list, self.timestamps)

            self.after(0, self.show_results)  # Schedule the GUI update to run in the main thread


            # Update status label to indicate success
            self.status_label.configure(text="Data fetched and analyzed successfully!", text_color="green")
        except Exception as e:
            # Handle any exceptions that occur during data fetching or analysis
            self.after(0, self.showerror, str(e))
    
    def populate_forecast(self) -> None:
        for i, period in enumerate(self.forecast_data):
            chance = period['probabilityOfPrecipitation']['value'] or 0  # default to 0 if None

            # Day / Period Name
            label_day = ctk.CTkLabel(self.forecast_frame, text=period['name'], font=("Courier", 15), justify="left")
            label_day.grid(column=0, row=i+1, sticky="w", pady=2, padx=(0,15))

            # Temperature
            label_temp = ctk.CTkLabel(self.forecast_frame, text=f"{period['temperature']}°F", font=("Courier", 15), justify="left")
            label_temp.grid(column=1, row=i+1, sticky="w", pady=2, padx=(0,25))

            # Short Forecast / Description
            label_desc = ctk.CTkLabel(self.forecast_frame, text=period['shortForecast'], font=("Courier", 15), justify="left")
            label_desc.grid(column=2, row=i+1, sticky="w", pady=2, padx=(0,25))

            # Chance of Rain with conditional coloring
            if chance >= 60:
                color = "red" 
            elif chance >= 30:
                color = "orange"
            else:
                color = "green"
            label_rain = ctk.CTkLabel(self.forecast_frame, text=f"{chance}%", font=("Courier", 15), justify="left", text_color=color)
            label_rain.grid(column=3, row=i+1, sticky="w", pady=2, padx=(0,15))


    def configure_forecast_data(self) -> None:
        headings = ["Day/Period", "Temp (°F)", "Description", "Chance of Rain"]
        for col, heading in enumerate(headings):
            label = ctk.CTkLabel(self.forecast_frame, text=heading, font=("Courier", 15, "bold"), justify="left")
            label.grid(column=col, row=0, sticky="w", pady=5, padx=(0,15))
            
        self.populate_forecast()

    def update_forecast_tab(self) -> None:
        self.configure_forecast_data()

    def update_stats_tab(self) -> None:
        message = self.print_records_message()
        recrods_label = ctk.CTkLabel(self.stats_frame_header, text=message, font=("Arial", 16), justify="center")
        recrods_label.pack(pady=(10, 20))

        cloudy_label = ctk.CTkLabel(self.stats_frame_header,
                                    text=f"Cloudy days in last ~10 days: {self.backend.cloudy_days}",  
                                    font=("Arial", 16, "bold"))
        cloudy_label.pack(pady=(20, 10))

        temp_stats = ctk.CTkLabel(self.stats_frame,
                                  text="Temperature Statistics\n" +
                                       f"Avg: {round(sum(self.temp_list)/len(self.temp_list),1)}°F\n" +
                                       f"Min: {round(min(self.temp_list),1)}°F\n" +
                                       f"Max: {round(max(self.temp_list),1)}°F",
                                  justify="left", anchor="w")
        temp_stats.grid(row=0, column=0, padx=40, pady=10, sticky="w")

        humid_stats = ctk.CTkLabel(self.stats_frame,
                                   text="Humidity Statistics\n" +
                                        f"Avg: {round(sum(self.humidity_list)/len(self.humidity_list),1)}%\n" +
                                        f"Min: {round(min(self.humidity_list),1)}%\n" +
                                        f"Max: {round(max(self.humidity_list),1)}%",
                                   justify="left", anchor="w")
        humid_stats.grid(row=0, column=1, padx=40, pady=10, sticky="w")

    def update_forecast_raw_data_tab(self) -> None:
        forecast_raw_data_label = ctk.CTkLabel(self.forecast_raw_data_frame,font=ctk.CTkFont(family="Arial", size=14), width=900, height=200)
        forecast_raw_data_label.pack(pady=10, padx=10)

        for record in self.forecast_data:
            forecast_raw_data_label.configure(text=f"{forecast_raw_data_label.cget('text')}\n{record}")

    def update_plots(self) -> None:
        for plot_name in ["weather.png", "boxplot.png", "temperature_histogram.png"]:
            if os.path.exists(plot_name):
                try:
                    img = Image.open(plot_name)
                    img.thumbnail((700, 500))  # reasonable max size

                    if plot_name == "weather.png":
                        img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        img_label = ctk.CTkLabel(self.std_plot_tab, image=img_ctl, text="")
                    elif plot_name == "boxplot.png":
                        img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        img_label = ctk.CTkLabel(self.box_plot_tab, image=img_ctl, text="")
                    elif plot_name == "temperature_histogram.png":
                        img_ctl = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        img_label = ctk.CTkLabel(self.temp_hist_tab, image=img_ctl, text="")
               
                    img_label.pack(pady=15)
                    img.close()  # Close the image file after loading it into the label
                except:
                    pass

    def create_raw_data_headers(self) -> None:
        record_header = ctk.CTkLabel(self.hist_raw_data_frame, text="Timestamp", font=("Courier", 15, "bold"), justify="left")
        record_header.grid(column = 0, row=0, sticky="w", pady=5, padx=(0,20))
        record_header = ctk.CTkLabel(self.hist_raw_data_frame, text="Temperature", font=("Courier", 15, "bold"), justify="left")
        record_header.grid(column = 1, row=0, sticky="w", pady=5, padx=(0,15))
        record_header = ctk.CTkLabel(self.hist_raw_data_frame, text="Humidity", font=("Courier", 15, "bold"), justify="left")
        record_header.grid(column = 2, row=0, sticky="w", pady=5, padx=(0,15))
        record_header = ctk.CTkLabel(self.hist_raw_data_frame, text="Description", font=("Courier", 15, "bold"), justify="left")
        record_header.grid(column = 3, row=0, sticky="w", pady=5, padx=(0,15))

    def update_hist_raw_data_tab(self) -> None:
        #create headers
        self.create_raw_data_headers()

        for i, record in enumerate(self.noaa_data):

            record_label_dte = ctk.CTkLabel(self.hist_raw_data_frame, text=str(record["timestamp"][:record["timestamp"].find("T")]), font=("Courier", 15), justify="left")
            record_label_dte.grid(column = 0, row=i+1, sticky="w", pady=2, padx=(0,20))
            record_label_temp = ctk.CTkLabel(self.hist_raw_data_frame, text=(f"{record['temperature']['value']:.2f} °F"), font=("Courier", 15), justify="left")
            record_label_temp.grid(column = 1, row=i+1, sticky="w", pady=2, padx=(0,15))
            record_label_humid = ctk.CTkLabel(self.hist_raw_data_frame, text=(f"{record['relativeHumidity']['value']:.1f}%"), font=("Courier", 15), justify="left")
            record_label_humid.grid(column = 2, row=i+1, sticky="w", pady=2, padx=(0,15))
            record_label_desc = ctk.CTkLabel(self.hist_raw_data_frame, text=str(record["textDescription"]), font=("Courier", 15), justify="left")
            record_label_desc.grid(column = 3, row=i+1, sticky="w", pady=2, padx=(0,15) )

    def show_results(self) -> None:
        # Update GUI with new data and plots
        self.update_forecast_tab()
        self.update_stats_tab()
        self.update_plots()
        self.update_hist_raw_data_tab()
        self.update_forecast_raw_data_tab()

        self.status_label.configure(text="Analysis complete", text_color="green")

    def showerror(self, message: str) -> None:
        messagebox.showerror("Error", f"An error occurred: {str(message)}")
        self.status_label.configure(text="Error fetching data.", text_color="red")

    def on_closing(self) -> None:
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

if __name__ == "__main__":
    app = WeatherAppGUI()
    app.mainloop()