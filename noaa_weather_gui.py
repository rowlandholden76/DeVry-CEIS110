# weather_gui.py
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import os

from noaa_weather_backend import RowlandNoaaWeather   

ctk.set_appearance_mode("System")          # "Light", "Dark", "System"
ctk.set_default_color_theme("blue")

class WeatherAppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NOAA Weather Analyzer – Rowland Holden")
        self.geometry("1000x850")
        self.minsize(900, 700)

        self.backend = RowlandNoaaWeather()

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkLabel(self, text="Weather Data Analyzer", font=("Arial", 24, "bold"))
        header.pack(pady=(20, 10))

        # ── Input area ───────────────────────────────────────────────────
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=10, padx=30, fill="x")

        ctk.CTkLabel(input_frame, text="ZIP Code:", font=("Arial", 14)).pack(side="left", padx=(0, 10))
        
        self.zip_entry = ctk.CTkEntry(input_frame, width=140, placeholder_text="e.g. 98204")
        self.zip_entry.insert(0, "98204")
        self.zip_entry.pack(side="left", padx=10)

        fetch_btn = ctk.CTkButton(input_frame, text="Fetch & Analyze", width=160,
                                 command=self.start_fetch_thread)
        fetch_btn.pack(side="left", padx=20)

        # ── Status ───────────────────────────────────────────────────────
        self.status = ctk.CTkLabel(self, text="Ready", font=("Arial", 13), text_color="gray")
        self.status.pack(pady=(10, 5))

        # ── Results scrollable area ──────────────────────────────────────
        self.results_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_container.pack(pady=10, padx=30, fill="both", expand=True)

    def start_fetch_thread(self):
        self.status.configure(text="Fetching data from NOAA... Please wait", text_color="orange")
        self.update_idletasks()  # force redraw

        # Clear previous results
        for child in self.results_container.winfo_children():
            child.destroy()

        thread = threading.Thread(target=self.run_analysis, daemon=True)
        thread.start()

    def run_analysis(self):
        try:
            # For now we ignore the ZIP entry (backend is still hard-coded to 98204)
            # We'll make it dynamic in the next step
            temp_list, humidity_list, timestamps = self.backend.init_weather_data()
            temp_list, humidity_list = self.backend.clean_data(temp_list, humidity_list)
            self.backend.create_plots(temp_list, humidity_list, timestamps)
            # We skip console stats printing for GUI version – we'll show them in UI

            self.after(0, self.show_results, temp_list, humidity_list)

        except Exception as e:
            self.after(0, self.show_error, str(e))

    def show_results(self, temp_list, humidity_list):
        # ── Cloudy days & basic info ─────────────────────────────────────
        cloudy_label = ctk.CTkLabel(self.results_container,
                                    text=f"Cloudy days in last ~10 days: {len(set())}",  # placeholder – we'll fix
                                    font=("Arial", 16, "bold"))
        cloudy_label.pack(pady=(20, 10))

        # ── Stats ─────────────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(self.results_container)
        stats_frame.pack(fill="x", pady=15)

        temp_stats = ctk.CTkLabel(stats_frame,
                                  text="Temperature Statistics\n" +
                                       f"Avg: {round(sum(temp_list)/len(temp_list),1)}°F\n" +
                                       f"Min: {round(min(temp_list),1)}°F\n" +
                                       f"Max: {round(max(temp_list),1)}°F",
                                  justify="left", anchor="w")
        temp_stats.pack(side="left", padx=40, pady=10)

        humid_stats = ctk.CTkLabel(stats_frame,
                                   text="Humidity Statistics\n" +
                                        f"Avg: {round(sum(humidity_list)/len(humidity_list),1)}%\n" +
                                        f"Min: {round(min(humidity_list),1)}%\n" +
                                        f"Max: {round(max(humidity_list),1)}%",
                                   justify="left", anchor="w")
        humid_stats.pack(side="left", padx=40, pady=10)

        # ── Plots ─────────────────────────────────────────────────────────
        for fname in ["weather.png", "boxplot.png", "temperature_histogram.png"]:
            if os.path.exists(fname):
                try:
                    img = Image.open(fname)
                    img.thumbnail((700, 500))  # reasonable max size
                    photo = ImageTk.PhotoImage(img)
                    lbl = ctk.CTkLabel(self.results_container, image=photo, text="")
                    lbl.image = photo  # keep reference
                    lbl.pack(pady=15)
                except:
                    pass

        self.status.configure(text="Analysis complete", text_color="green")

    def show_error(self, msg):
        self.status.configure(text=f"Error: {msg}", text_color="red")

    def on_closing(self):
        if ctk.CTk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

if __name__ == "__main__":
    app = WeatherAppGUI()
    app.mainloop()