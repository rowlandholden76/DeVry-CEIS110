"""
WeatherAppGUI Class
===================

Author:    Rowland Holden
Date:      Feb 23, 2026
Course:    CEIS 101 - Final Project (Enhanced)
Purpose:   Provides a GUI for fetching and analyzing NOAA weather data for a specified
           ZIP code, with visualizations and statistics.

A comprehensive GUI application for fetching, analyzing, and visualizing NOAA weather
data and forecasts. This class creates a multi-tabbed interface using customtkinter that
allows users to:
- Input a ZIP code and fetch weather data from NOAA stations
- View 14-day weather forecasts
- Display historical weather statistics (temperature and humidity)
- Generate and view various data visualizations (line plots, box plots, histograms)
- Examine raw data from both NOAA observations and forecasted data in JSON view

The application uses threading to prevent GUI blocking during data fetching operations
and provides real-time status updates to the user.
Attributes:
    backend (RowlandNoaaWeather): Instance of the backend class for data fetching
        and processing
    tabs
    (ctk.CTkTabview): Tabview container for organizing different data views
    title_label (ctk.CTkLabel): Main title label for the application
    input_frame (ctk.CTkFrame): Frame containing ZIP code input and fetch button
    zip_entry (ctk.CTkEntry): Entry widget for user to input ZIP code
    status_label (ctk.CTkLabel): Label displaying current operation status
    forecast_tab (ctk.CTkFrame): Tab for displaying weather forecast
    hist_stats_tab (ctk.CTkFrame): Tab for displaying historical statistics
    std_plot_tab (ctk.CTkFrame): Tab for displaying standard temperature/humidity plot
    box_plot_tab (ctk.CTkFrame): Tab for displaying box plot comparison
    temp_hist_tab (ctk.CTkFrame): Tab for displaying temperature histogram
    hist_raw_data_tab (ctk.CTkFrame): Tab for displaying raw NOAA data
    forecast_raw_data_tab (ctk.CTkFrame): Tab for displaying raw forecast data
    forecast_data (list): Store for forecast data retrieved from API
    noaa_data (list): Store for NOAA historical weather records
    temp_list (list): Processed temperature values from NOAA data
    humidity_list (list): Processed humidity values from NOAA data
    timestamps (list): Timestamps corresponding to temperature/humidity records

Methods:
    create_tabs(): Initialize all application tabs
    create_frames(): Initialize all frames and containers
    create_widgets(): Initialize all widgets and call setup methods
    clear_previous_data(): Remove all data widgets when resetting for new ZIP code
    start_fetch_thread(): Initiate data fetching in separate thread
    get_data(): Fetch and process weather data from backend
    print_records_message(): Generate user-friendly data summary message
    run_analysis(): Execute data fetching and analysis (runs in thread)
    populate_forecast(): Populate forecast tab with API data
    configure_forecast_data(): Set up forecast tab headers and data
    update_forecast_tab(): Update forecast tab with new data
    update_stats_tab(): Update statistics tab with calculated values
    update_forecast_raw_data_tab(): Display raw forecast JSON data
    update_plots(): Load and display generated plot images
    update_hist_raw_data_tab(): Display formatted NOAA raw data records
    show_results(): Update all GUI elements with new analysis results
    showerror(): Display error message to user
    on_closing(): Handle application shutdown with user confirmation

Output Files:
- weather.png          : Temperature & Humidity over time
- boxplot.png          : Box plot comparison
- temperature_histogram.png : Temperature distribution

Note: The noaa_weather_backend returns all available records from the Noaa stations
    for the various ZIP codes in the requested time window that stations have
    data for.
     The backend is currently hard-coded to fetch data for ZIP code 98204,
     but the GUI is designed to allow dynamic input of ZIP codes in the future.
     The number of cloudy days is currently a placeholder and will be implemented
     in the next step after we have the cleaned data available in the GUI.
"""

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from concurrent.futures import ThreadPoolExecutor
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import customtkinter as ctk
import tkinter.messagebox as messagebox
import json
import gc

from noaa_weather_backend import RowlandNoaaWeather

ctk.set_appearance_mode("System")  # "Light", "Dark", "System"
ctk.set_default_color_theme("blue")


class WeatherAppGUI(ctk.CTk):
    def __init__(self) -> None:
        """Creates the window title and size. Creates an instance variable for tabview
        that will hold the tabs that are later created. The tabview is not packed here
        because we do not want it to be at the top of the window. We will create an
        input area for this and that is what we want at the top of the window. we are
        also creating an instance variable for the backend class that will be used to
        fetch and analyze the data. We create the backend instance here because we want
        to be able to access it in all methods of the class, and we only want to create
        one instance of it that can be reused when fetching new data for different zip
        codes. From here we also call the create_widgets method that will create all the
        widgets for the GUI, it also calls the methods to create the tabs and frames,
        and we set the protocol for when the user tries to close the window to call the
        on_closing method that will ask the user if they are sure they want to quit and
        then destroy the window if they confirm.

        Args:
            None

        Returns:
            None

        Examples:
            super().__init__() # Calls the parent class constructor
        """
        super().__init__()

        self.title("Weather Analyzer – Rowland Holden")
        self.geometry("1000x850")
        self.minsize(900, 700)

        self.backend = RowlandNoaaWeather()
        # 1 worker = sequential fetches (prevents thread buildup if user
        # clicks fetch multiple times quickly)
        self.executor = ThreadPoolExecutor(max_workers=1)

        # The tab view will never be destroyed when reseting for new zip, create it
        # here.
        self.tabs = ctk.CTkTabview(self)
        # Create a textbox for the json data that can be accessed in the
        # update_forecast_raw_data_tab
        # method to display the raw forecast data, we will create it here and just
        # update the text in it when we need to
        # display new data, this way we do not have to worry about destroying and
        # recreating it when fetching new data for
        # different zip codes.
        self.forecast_raw_textbox = None

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_tabs(self) -> None:
        """Creates all the tabs and assigns them to instance variables so they can be
        accessed later when populating the tabs with data and plots.

        Args:
            None

        Returns:
            None

        Examples:
            create_tabs()
        """
        self.forecast_tab = self.tabs.add("Forecast")
        self.hist_stats_tab = self.tabs.add("Historical Statistics")
        self.std_plot_tab = self.tabs.add("Standard Plot")
        self.box_plot_tab = self.tabs.add("Box Plot")
        self.temp_hist_tab = self.tabs.add("Temperature Histogram")
        self.hist_raw_data_tab = self.tabs.add("Historical Raw Data")
        self.forecast_raw_data_tab = self.tabs.add("Forecast Raw Data")

    def create_frames(self) -> None:
        """Creates all the frames and assigns them to instance variables so they can be
        accessed later when populating the tabs with data and plots also places them the
        appropriate tab .

        Args:
            None

        Returns:
            None

        Examples:
            create_frames()
        """
        # Input Frame for ZIP code and Fetch button
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10)
        self.input_frame.grid_columnconfigure(2, weight=1)

        # Now pack the tabs so the input frame is at the top of the window
        self.tabs.pack(expand=True, fill="both", padx=30, pady=10)

        # Forecast frame header
        self.forecast_header_frame = ctk.CTkFrame(self.forecast_tab)
        self.forecast_header_frame.pack(pady=5, padx=20, fill="x")
        # Forecast Frame for displaying weather forecast
        self.forecast_frame = ctk.CTkFrame(self.forecast_tab)
        self.forecast_frame.pack(pady=5, padx=20, fill="both", expand=True)

        # Statistics frame header to be seperate from the grid
        self.stats_frame_header = ctk.CTkFrame(self.hist_stats_tab)
        self.stats_frame_header.pack(pady=(10, 0))
        # Statistics Frame for displaying weather statistics
        self.stats_frame = ctk.CTkFrame(self.hist_stats_tab)
        self.stats_frame.grid_columnconfigure((0, 1), weight=1)
        self.stats_frame.pack(pady=15, padx=10)

        # Plot Frames for displaying generated plots
        self.std_plot_frame = ctk.CTkScrollableFrame(self.std_plot_tab)
        self.std_plot_frame.pack(pady=10, fill="both", expand=True)

        self.box_plot_frame = ctk.CTkFrame(self.box_plot_tab)
        self.box_plot_frame.pack(pady=10, fill="both", expand=True)

        self.temp_hist_frame = ctk.CTkFrame(self.temp_hist_tab)
        self.temp_hist_frame.pack(pady=10, fill="both", expand=True)

        # Raw data header frame
        self.hist_raw_data_header_frame = ctk.CTkFrame(self.hist_raw_data_tab)
        self.hist_raw_data_header_frame.pack(pady=(10, 0))
        # Raw Data Frames for displaying raw data in text format
        self.hist_raw_data_frame = ctk.CTkFrame(
            self.hist_raw_data_tab, width=900, height=400
        )
        self.hist_raw_data_frame.grid_columnconfigure(3, weight=1)
        self.hist_raw_data_frame.pack(pady=10, padx=30, fill="both", expand=True)

        # Forecast raw data frame
        self.forecast_raw_data_frame = ctk.CTkFrame(
            self.forecast_raw_data_tab, width=900, height=400
        )
        self.forecast_raw_data_frame.pack(pady=10, padx=30, fill="both", expand=True)

    def create_widgets(self) -> None:
        """Creates all widgets and assigns them to instance variables so they can be
        accessed later when populating the tabs with data and plots. This method also
        calls `create_tabs` and `create_frames` to initialize those containers and then
        places widgets on the appropriate tab.

        The GUI is reset when fetching new data for a different ZIP code. To avoid
        recreating static widgets (for example: frames, window header, input area, and
        status label) this method only creates widgets that were removed during the
        reset process.

        Args:
            None

        Returns:
            None

        Examples:
            create_widgets()
        """
        # Title Label
        if not hasattr(self, "title_label"):
            self.title_label = ctk.CTkLabel(
                self,
                text="NOAA Weather Data Analyzer",
                font=ctk.CTkFont("Arial", size=24, weight="bold"),
            )
            self.title_label.pack(pady=20)

        # Create Tabs
        self.create_tabs()
        # Create Frames
        self.create_frames()

        # -----INPUT WIDGETS-----
        # input section for zip code and fetch button
        zip_label = ctk.CTkLabel(
            self.input_frame, text="Enter ZIP Code:", font=("Arial", 13)
        )
        zip_label.grid(row=0, column=0, sticky="w", pady=5)

        self.zip_entry = ctk.CTkEntry(
            self.input_frame, width=100, placeholder_text="e.g. 98204"
        )
        self.zip_entry.grid(row=0, column=1, sticky="w", pady=5, padx=(10, 20))

        fetch_button = ctk.CTkButton(
            self.input_frame, text="Fetch & Analyze", command=self.start_fetch_thread
        )
        fetch_button.grid(row=0, column=2, sticky="w", pady=5)

        # -----FORECAST WIDGETS-----
        # Forecast header
        forecast_label = ctk.CTkLabel(
            self.forecast_header_frame,
            text="14 Day Weather Forecast",
            font=ctk.CTkFont("Arial", size=20, weight="bold"),
        )
        forecast_label.pack(pady=(0, 10))
        # Forecast textbox for the forecast data that is going to be printed. We create
        # it here so we can just update the text in
        # it when fetching new data for different zip codes instead of having to destroy
        # and recreate it every time.
        self.forecast_textbox = ctk.CTkTextbox(
            self.forecast_frame,
            font=ctk.CTkFont(
                family="Courier", size=13, weight="normal"
            ),  # or "Courier New", "Courier"
            width=900,
            height=400,
            wrap="none",  # no word wrap
        )
        self.forecast_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        # -----STATISTICS WIDGETS-----
        # Statistics textbox and labels for the statistics data that is going to be
        # printed. We create them here so we can
        # just update the text in them when fetching new data for different zip codes
        # instead of having to destroy and recreate them every time.
        # Statistics Header
        self.stats_label = ctk.CTkLabel(
            self.stats_frame_header,
            text="Weather Statistics",
            font=ctk.CTkFont("Arial", size=20, weight="bold"),
        )
        self.stats_label.pack(pady=10)
        # Records count label
        self.records_label = ctk.CTkLabel(
            self.stats_frame_header,
            text="",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
        )
        self.records_label.pack(pady=(5, 10))
        # Cloudy days count
        self.cloudy_label = ctk.CTkLabel(
            self.stats_frame_header,
            text="",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
        )
        self.cloudy_label.pack(pady=(5, 10))
        # Temperature stats
        self.temp_stats = ctk.CTkLabel(
            self.stats_frame, text="", justify="center", anchor="w"
        )
        self.temp_stats.grid(row=0, column=0, padx=40, pady=10, sticky="w")
        # Humidity stats
        self.humid_stats = ctk.CTkLabel(
            self.stats_frame, text="", justify="center", anchor="w"
        )
        self.humid_stats.grid(row=0, column=1, padx=40, pady=10, sticky="w")

        # -------PLOT WIDGETS-------
        # We are using a matplotlib figure canvas to display the plots instead of an
        # image label because it is more efficient and uses less memory
        # than loading the plot images as separate files and then displaying them in
        # image labels. This was causing a native memory leak that was
        # not being resolved by garbage collection, even after closing the figures and
        # deleting the image objects, the memory used by the images was not being freed.
        # By using a matplotlib figure canvas, we can directly render the plots onto the
        # canvas without having to save them as image files and load them back into the
        # GUI,
        # which helps to prevent the memory leak and reduce the overall memory usage of
        # the application. We create the figure and canvas here so we can just update
        # the
        # figure with new plots when fetching new data for different zip codes instead
        # of having to destroy and recreate the canvas and figure every time.

        # ------------ STANDARD PLOT WIDGETS-------------
        # Message Label
        self.std_msg_label = ctk.CTkLabel(
            self.std_plot_frame,
            text="",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            justify="center",
        )
        self.std_msg_label.pack(pady=10, padx=20)
        # Direct creation of standard plot cavas widget
        self.std_fig = Figure(figsize=(9, 7), dpi=100)
        self.std_subplot = self.std_fig.add_subplot(111)
        self.std_canvas = FigureCanvasTkAgg(self.std_fig, master=self.std_plot_frame)
        # --------------Enable the menu on the plot canvases for saving and manipulating
        # the plots--------
        # Standard Plot toolbar
        self.std_toolbar = NavigationToolbar2Tk(self.std_canvas, self.std_plot_frame)
        self.std_toolbar.update()  # Required
        self.std_toolbar.pack(side="top", fill="x")

        self.std_canvas.get_tk_widget().pack(fill="both", expand=True)
        # -------------BOX PLOT WIDGETS-------------
        # Message Label
        self.box_msg_label = ctk.CTkLabel(
            self.box_plot_frame,
            text="",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            justify="center",
        )
        self.box_msg_label.pack(pady=10, padx=20)
        # Direct creation of box plot canvas widget
        self.box_fig = Figure(figsize=(7, 5), dpi=100)
        self.box_subplot = self.box_fig.add_subplot(111)
        self.box_canvas = FigureCanvasTkAgg(self.box_fig, master=self.box_plot_frame)
        # --------------Enable the menu on the plot canvases for saving and manipulating
        # the plots--------
        # Box Plot toolbar
        self.box_toolbar = NavigationToolbar2Tk(self.box_canvas, self.box_plot_frame)
        self.box_toolbar.update()
        self.box_toolbar.pack(side="top", fill="x")

        self.box_canvas.get_tk_widget().pack(fill="both", expand=True)
        # -------------TEMPERATURE HISTOGRAM WIDGETS-------------
        # Message Label
        self.temp_hist_msg_label = ctk.CTkLabel(
            self.temp_hist_frame,
            text="",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            justify="center",
        )
        self.temp_hist_msg_label.pack(pady=10, padx=20)
        # Direct creation of temperature histogram canvas widget
        self.fig_hist = Figure(figsize=(7, 5), dpi=100)
        self.hist_subplot = self.fig_hist.add_subplot(111)
        self.hist_canvas = FigureCanvasTkAgg(self.fig_hist, master=self.temp_hist_frame)
        # --------------Enable the menu on the plot canvases for saving and manipulating
        # the plots--------
        # Histogram toolbar
        self.hist_toolbar = NavigationToolbar2Tk(self.hist_canvas, self.temp_hist_frame)
        self.hist_toolbar.update()
        self.hist_toolbar.pack(side="top", fill="x")

        self.hist_canvas.get_tk_widget().pack(fill="both", expand=True)
        # -------  END PLOT SECTION -------

        # Raw Forecast Data header
        self.forecast_raw_data_lable = ctk.CTkLabel(
            self.forecast_raw_data_frame,
            text="Raw Forecast Data (JSON format)",
            font=ctk.CTkFont("Arial", size=20, weight="bold"),
        )
        self.forecast_raw_data_lable.pack(pady=10, padx=10)

        # Noaa raw data header
        raw_data_text = ctk.CTkLabel(
            self.hist_raw_data_header_frame,
            text="Raw NOAA Data:",
            font=ctk.CTkFont("Arial", size=20, weight="bold"),
        )
        raw_data_text.pack(pady=(20, 10))

        # Noaa Raw data text box, we create it here so we can just update the text in it
        # when fetching new data for different zip codes
        # instead of having to destroy and recreate it every time
        self.hist_raw_textbox = ctk.CTkTextbox(
            self.hist_raw_data_frame,
            font=ctk.CTkFont(
                family="Courier", size=13, weight="normal"
            ),  # or "Courier New", "Courier"
            width=900,
            height=400,
            wrap="none",  # no word wrap
        )
        self.hist_raw_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        # ------FORECAST RAW DATA WIDGETS-----
        # Data textbox for displaying the raw forecast data in json format, we create it
        # here so we can just update the text in it when
        # fetching new data for different zip codes instead of having to destroy and
        # recreate it every time.
        self.forecast_raw_textbox = ctk.CTkTextbox(
            self.forecast_raw_data_frame,
            font=ctk.CTkFont(family="Arial", size=14),
            width=900,
            height=200,
        )
        self.forecast_raw_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        # Status Label for displaying messages to the user
        self.status_label = ctk.CTkLabel(
            self, text="Ready", font=ctk.CTkFont("Arial", size=12), text_color="green"
        )
        self.status_label.pack(pady=(10, 15))

    def clear_previous_data(self) -> None:
        """Destroys all the widgets that are displaying data and plots so that when
        fetching new data for a different zip code, the old data and plots are removed
        from the GUI before the new data and plots are displayed.

        Args:
            None

        Returns:
            None

        Examples:
            clear_previous_data()
        """
        # Clear Forecast Frame
        if hasattr(self, "forecast_textbox") and self.forecast_textbox is not None:
            self.forecast_textbox.delete("1.0", "end")

        # Clear Statistics Frame
        if hasattr(self, "records_label") and self.records_label is not None:
            self.records_label.configure(text="")  # Clear the records message
        if hasattr(self, "cloudy_label") and self.cloudy_label is not None:
            self.cloudy_label.configure(text="")  # Clear the cloudy message
        if hasattr(self, "temp_stats") and self.temp_stats is not None:
            self.temp_stats.configure(text="")  # Clear the temp stats message
        if hasattr(self, "humid_stats") and self.humid_stats is not None:
            self.humid_stats.configure(text="")  # Clear the humidity stats message

        # ------ CLEAR PLOT FRAMES ------
        # Standard Plot Frame
        if hasattr(self, "std_msg_label") and self.std_msg_label is not None:
            self.std_msg_label.configure(text="")  # Clear the standard plot message
        if hasattr(self, "std_img_label") and self.std_img_label is not None:
            self.std_img_label.configure(image=None)
            self.std_img_label.image = (
                None  # Clear the reference to the image to allow garbage collection
            )
        # Box Plot Frame
        if hasattr(self, "box_msg_label") and self.box_msg_label is not None:
            self.box_msg_label.configure(text="")  # Clear the box plot message
        if hasattr(self, "box_img_label") and self.box_img_label is not None:
            self.box_img_label.configure(image=None)
            self.box_img_label.image = (
                None  # Clear the reference to the image to allow garbage collection
            )
        # Temperature Histogram Frame
        if (
            hasattr(self, "temp_hist_msg_label")
            and self.temp_hist_msg_label is not None
        ):
            self.temp_hist_msg_label.configure(
                text=""
            )  # Clear the temperature histogram message
        if (
            hasattr(self, "temp_hist_img_label")
            and self.temp_hist_img_label is not None
        ):
            self.temp_hist_img_label.configure(image=None)
            self.temp_hist_img_label.image = (
                None  # Clear the reference to the image to allow garbage collection
            )

        # Clear Forecast Raw Data Frame
        if (
            hasattr(self, "forecast_raw_textbox")
            and self.forecast_raw_textbox is not None
        ):
            self.forecast_raw_textbox.delete("1.0", "end")

        # Clear Raw Data Frames
        if hasattr(self, "hist_raw_textbox") and self.hist_raw_textbox is not None:
            self.hist_raw_textbox.delete("1.0", "end")

        # Force garbage collection to free memory used by the destroyed widgets
        gc.collect()

    def start_fetch_thread(self) -> None:
        """Activated when the user clicks the "Fetch & Analyze" button. It updates the
        status label to indicate that data is being fetched, clears any previous data
        and plots from the GUI, and starts a new thread to fetch and analyze the data to
        avoid blocking the GUI.

        Args:
            None

        Returns:
            None

        Examples:
            start_fetch_thread()
        """
        # Update stuatus label to indicate data fetching
        self.status_label.configure(text="Fetching data...", text_color="orange")
        self.update_idletasks()  # Ensure the status label updates immediately

        # Clear Previous Data and Plots
        self.clear_previous_data()

        # recreate any missing widgets from data clearing
        # self.create_widgets()

        # Start a new thread to fetch data to avoid blocking the GUI
        self.executor.submit(self.run_analysis)  # submit to pool instead of new thread
        # fetch_thread = threading.Thread(target=self.run_analysis, daemon=True)
        # fetch_thread.start()

    def get_data(self) -> None:
        """Gets the data from the backend for both noaa data(for history) and forecast
        data, converts the temperatures to fahrenheit for all records in noaa data, and
        then initializes the weather data by calling the init_weather_data method in the
        backend which returns the temp_list, humidity_list, and timestamps that are used
        for the statistics and plots. The reason we have a separate method for this is
        because we need to call it in the run_analysis method which is running in a
        separate thread, and we want to keep the code organized and modular by
        separating the data fetching and processing logic from the GUI update logic in
        the run_analysis method.

        Args:
            None

        Returns:
            None

        Examples:
            get_data()
        """
        self.forecast_data = self.backend.get_forecast_data()
        self.noaa_data = list(self.backend.get_noaa_data())

        # Convert temperatures to Fahrenheit for all records in noaa_data
        for weather in self.noaa_data:
            self.backend.convert_temp_to_F(weather)

        self.temp_list, self.humidity_list, self.timestamps = (
            self.backend.init_weather_data()
        )

    def print_records_message(self) -> str:
        """Prints a uuser-friendly message indicating how many records were fetched from
        the NOAA stations and how many unique days of data are represented in those
        records. This is used on all historical data tabs.

        Args:
            None

        Returns:
            str: the message to be displayed to the user

        Examples:
            print_records_message()
        """
        num_records = len(self.noaa_data)
        unique_days = self.backend.get_unique_days(self.timestamps)
        message = (
            f"Fetched {num_records} records across {unique_days}"
            f" days from NOAA stations for ZIP code {self.backend.zip_code}."
        )
        return message

    def generate_plots(self) -> None:
        """This is called to keep matplotlib.pyplot thread safe. It passes this call
        onto create_plots in the backend which generates the plots and saves them as
        image files. We couldn't call create_plots directly in the run_analysis method
        because that method is running in a separate thread and matplotlib is not thread
        safe. We also couldn't scehdule create_plots to run in the main thread using
        after because it requires a number of arguments and the arguments can not be
        passed in the after method, so we created this generate_plots method that is
        called in the main thread using after and it calls the create_plots method in
        the backend with the necessary arguments to generate the plots.

        Args:
            None

        Returns:
            None

        Examples:
            generate_plots()
        """
        self.backend.create_plots(self.temp_list, self.humidity_list, self.timestamps)
        gc.collect()  # Force garbage collection to free memory used by the plots

    def run_analysis(self) -> None:
        """Responsible for starting the data fetching and plot creation. It first checks
        if the user has entered a ZIP code, if not it uses a default ZIP code. Then it
        calls the get_data method to fetch and process the data,

        Args:
            None

        Returns:
            None

        Examples:
            run_analysis()
        """
        if self.zip_entry.get().strip() == "":
            self.backend.zip_code = "98204"  # Default ZIP code if none provided
        else:
            self.backend.zip_code = self.zip_entry.get().strip()

        try:
            self.get_data()

            # Schedule the plot generation to run in the main thread after data
            # is fetched and processed
            self.after(0, self.generate_plots)
            self.after(
                0, self.show_results
            )  # Schedule the GUI update to run in the main thread

        except Exception as e:
            # Handle any exceptions that occur during data fetching or analysis
            self.after(0, self.showerror, str(e))

    def configure_forecast_data(self) -> None:
        """Creates the headers on the forecast tab, and then calls the populate_forecast
        method to populate the tab with the forecast data received from the API.

        Args:
            None

        Returns:
            None

        Examples:
            configure_forecast_data()
        """

        # Fixed-width columns
        header_line = (
                f"{'Date':<17} {'Temperature (°F)':<18} "
                f"{'Description':<45} {'Chance of Rain'}\n"
            )
        header_seperator = "-" * 95 + "\n"
        self.forecast_textbox.insert("end", header_line)
        self.forecast_textbox.insert("end", header_seperator)

        for i, period in enumerate(self.forecast_data):
            chance = (
                period["probabilityOfPrecipitation"]["value"] or 0
            )  # default to 0 if None

            day = period["name"]
            temp = f"{period['temperature']}°F"
            desc = period["shortForecast"]

            line = f"{day:<17} {temp:<18} {desc:<45} {chance}%\n"
            self.forecast_textbox.insert("end", line)

            # Find start of "chance" column (adjust numbers based on your formatting)
            # Assuming chance starts around column 70–75 (after day + temp + desc)
            chance_col_start = 17 + 18 + 45 + 1  # approximate — test and adjust
            chance_start = f"{i+3}.{chance_col_start}"
            chance_end = f"{i+3}.end"
            if chance >= 60:
                tag = "red"
            elif chance >= 30:
                tag = "orange"
            else:
                tag = "green"
            self.forecast_textbox.tag_add(tag, chance_start, chance_end)

        # Configure the tags (do this once, after all inserts)
        self.forecast_textbox.tag_config("red", foreground="red")
        self.forecast_textbox.tag_config("orange", foreground="orange")
        self.forecast_textbox.tag_config("green", foreground="green")

        # Lock read-only and scroll to top
        self.forecast_textbox.see("1.0")

    def update_forecast_tab(self) -> None:
        """Called from `show_results`. Updates the forecast tab by calling
        `configure_forecast_data` which creates the headers and populates the tab
        with the forecast data received from the API.
        Args:
            None

        Returns:
            None

        Examples:
            update_forecast_tab()
        """
        self.configure_forecast_data()

    def update_stats_tab(self) -> None:
        """Called from `show_results`. Creates labels to display historical statistics
        including average, minimum, and maximum temperature and humidity.
        Args:
            None

        Returns:
            None

        Examples:
            update_stats_tab()
        """
        message = self.print_records_message()
        self.records_label.configure(text=message)
        self.cloudy_label.configure(
            text=(
                f"Cloudy days in last {self.backend.get_unique_days(self.timestamps)} days: "
                f"{self.backend.cloudy_days}"
            )
        )
        self.temp_stats.configure(
            text="Temperature Statistics\n"
            + f"Avg: {round(sum(self.temp_list)/len(self.temp_list), 1)}°F\n"
            + f"Min: {round(min(self.temp_list), 1)}°F\n"
            + f"Max: {round(max(self.temp_list), 1)}°F"
        )

        self.humid_stats.configure(
            text="Humidity Statistics\n"
            + f"Avg: {round(sum(self.humidity_list)/len(self.humidity_list), 1)}%\n"
            + f"Min: {round(min(self.humidity_list), 1)}%\n"
            + f"Max: {round(max(self.humidity_list), 1)}%"
        )

    def update_forecast_raw_data_tab(self) -> None:
        """Called from `show_results`. Creates a textbox and populates it with the
        raw forecast data (JSON) received from the API so the user can inspect it.
        Args:
            None

        Returns:
            None

        Examples:
            update_forecast_raw_data_tab()
        """
        if self.forecast_raw_textbox is None:
            self.forecast_raw_textbox = ctk.CTkTextbox(
                self.forecast_raw_data_frame,
                font=ctk.CTkFont(family="Arial", size=14),
                width=900,
                height=200,
            )
            self.forecast_raw_textbox.pack(pady=10, padx=10, fill="both", expand=True)
        else:
            self.forecast_raw_textbox.delete("1.0", "end")

        self.forecast_raw_textbox.insert(
            "1.0", json.dumps(self.forecast_data, indent=4)
        )

    def update_plots(self) -> None:
        """Called from `show_results`. Checks for plot image files and creates image
        labels to display the plots on their respective tabs. Also displays a
        message above the plots indicating how many records were fetched and how
        many unique days of data are represented; the message appears on all
        three plot tabs.
        Args:
            None

        Returns:
            None

        Examples:
            update_plots()
        """
        message = self.print_records_message()
        for plot_name in ["weather.png", "boxplot.png", "temperature_histogram.png"]:
            try:
                # with Image.open(plot_name) as img:
                #     img.thumbnail((700, 500))  # reasonable max size
                #     photo = ImageTk.PhotoImage(img)

                if plot_name == "weather.png":
                    self.std_msg_label.configure(text=message)
                    self.std_msg_label.configure(text=message)
                    self.std_subplot.clear()
                    self.std_subplot.plot(
                        self.timestamps["temp"],
                        self.temp_list,
                        label="Temperature (°F)",
                        color="red",
                        linewidth=1.5,
                    )
                    self.std_subplot.plot(
                        self.timestamps["humidity"],
                        self.humidity_list,
                        label="Humidity (%)",
                        color="blue",
                        linewidth=1.5,
                    )
                    self.std_subplot.legend(loc="upper right")
                    title_text = (
                        f"Temperature and Humidity Over Time (ZIP "
                        f"{self.backend.zip_code})"
                    )
                    self.std_subplot.set_title(title_text)
                    self.std_subplot.set_xlabel("Observation Time")
                    self.std_subplot.set_ylabel("Value")
                    self.std_subplot.xaxis.set_major_locator(
                        mdates.AutoDateLocator(maxticks=15)
                    )
                    self.std_subplot.xaxis.set_major_formatter(
                        mdates.DateFormatter("%m-%d %H:%M")
                    )
                    self.std_subplot.tick_params(axis="x", rotation=45, labelsize=9)
                    self.std_subplot.grid(True, linestyle="--", alpha=0.5)
                    self.std_canvas.draw()
                elif plot_name == "boxplot.png":
                    self.box_msg_label.configure(text=message)
                    self.box_subplot.clear()
                    self.box_subplot.boxplot(
                        [self.temp_list, self.humidity_list],
                        tick_labels=["Temperature (°F)", "Humidity (%)"],
                        patch_artist=True,
                        boxprops=dict(facecolor="lightblue", color="blue"),
                        medianprops=dict(color="red"),
                    )
                    title_text = (
                        f"Temperature and Humidity Distribution (ZIP "
                        f"{self.backend.zip_code})"
                    )
                    self.box_subplot.set_title(title_text)
                    self.box_canvas.draw()
                    # self.box_msg_label.configure(text=message)  # Update the message
                    # above the box plot
                    # self.box_img_label.configure(image=photo)
                    # self.box_img_label.image = photo  # Keep a reference to prevent
                    # garbage collection
                elif plot_name == "temperature_histogram.png":
                    self.temp_hist_msg_label.configure(
                        text=message
                    )  # Update the message above the temperature histogram
                    self.hist_subplot.clear()
                    self.hist_subplot.hist(
                        self.temp_list,
                        bins=10,
                        color="salmon",
                        edgecolor="black",
                        alpha=0.7,
                    )
                    self.hist_subplot.set_title(
                        f"Temperature Distribution (ZIP {self.backend.zip_code})"
                    )
                    self.hist_subplot.set_xlabel("Temperature (°F)")
                    self.hist_subplot.set_ylabel("Frequency")
                    self.hist_canvas.draw()
                    # self.temp_hist_img_label.configure(image=photo)
                    # self.temp_hist_img_label.image = photo  # Keep a reference to
                    # prevent garbage collection

                    # self.hist_msg_label.configure(text=message)
                    # self.ax_hist.clear()
                    # self.ax_hist.hist(self.temp_list, bins=10, color="red", alpha=0.7)
                    # self.ax_hist.set_title(f"Temperature Distribution (ZIP
                    # {self.backend.zip_code})")
                    # self.ax_hist.set_xlabel("Temperature (°F)")
                    # self.ax_hist.set_ylabel("Frequency")
                    # self.canvas_hist.draw()

                # img.close()  # Close the image file after loading it into the label
            except Exception:
                pass

    def update_hist_raw_data_tab(self) -> None:
        """Called from show_results, it updates the historical raw data tab by first
        creating the headers for the raw data display by calling the
        create_raw_data_headers method, and then it creates labels for each record in
        the noaa data to display the timestamp, temperature, humidity, and description
        for each record in a grid format under the respective headers.

        Args:
            None

        Returns:
            None

        Examples:
            update_hist_raw_data_tab()
        """

        # Fixed-width columns
        header_line = (
            f"{'Date':<26} {'Temperature':<14} {'Humidity':<14} {'Description'}\n"
        )
        header_seperator = "-" * 90 + "\n"
        self.hist_raw_textbox.insert("end", header_line)
        self.hist_raw_textbox.insert("end", header_seperator)

        # create headers
        # self.create_raw_data_headers()

        for record in self.noaa_data:

            ts = record["timestamp"][: record["timestamp"].find("T")]
            temp = (
                f"{record['temperature']['value']:.2f} °F"
                if record["temperature"]["value"] is not None
                else "N/A"
            )
            humid = (
                f"{record['relativeHumidity']['value']:.1f}%"
                if record["relativeHumidity"]["value"] is not None
                else "N/A"
            )
            desc = record["textDescription"] or "N/A"

            # Fixed-width columns
            line = f"{ts:<26} {temp:<14} {humid:<14} {desc}\n"
            self.hist_raw_textbox.insert("end", line)

    def show_results(self) -> None:
        """Called from run_analysis after the data fetching and analysis is complete, it
        updates the GUI with the new data and plots by calling the respective update
        methods for each tab. It also updates the status label to indicate that the
        analysis is complete.

        Args:
            None

        Returns:
            None

        Examples:
            show_results()
        """
        # Update GUI with new data and plots
        self.update_forecast_tab()
        self.update_stats_tab()
        self.update_plots()
        self.update_hist_raw_data_tab()
        self.update_forecast_raw_data_tab()

        # Update status label to indicate success
        self.status_label.configure(text="Analysis complete", text_color="green")

    def showerror(self, message: str) -> None:
        """Called from run_analysis if an exception occurs during data fetching or
        analysis, it displays an error message to the user in a message box and updates
        the status label to indicate that an error occurred.

        Args:
            None

        Returns:
            None

        Examples:
            showerror("An error occurred")
        """
        messagebox.showerror("Error", f"An error occurred: {str(message)}")
        self.status_label.configure(text="Error fetching data.", text_color="red")

    def on_closing(self) -> None:
        """Called when the user attempts to close the application, it prompts the user
        with a confirmation dialog and closes the application if the user confirms.

        Args:
            None

        Returns:
            None

        Examples:
            on_closing()
        """
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.executor.shutdown(
                wait=True
            )  # Cleanly shutdown the thread pool to free resources
            self.destroy()


if __name__ == "__main__":
    app = WeatherAppGUI()
    app.mainloop()


# Module-level entry point for packaging/console_scripts
def main() -> None:
    """Start the Weather GUI application (console entry point).

    This function allows packaging tools to create a `console_scripts`
    entry point that launches the GUI.
    """
    app = WeatherAppGUI()
    app.mainloop()
