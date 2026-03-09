"""NOAA Weather Data Analyzer
=============================

Author:    Rowland Holden
Date:      Feb 17, 2026 (extended version)
Course:    CEIS 101 - Final Project (Enhanced)

Purpose
-------
Fetch recent weather observations from NOAA's API for Everett, WA (ZIP 98204),
convert temperatures to °F, process relative humidity over the past ~10 days,
count unique cloudy days, generate visualizations, and compute basic
statistics.

Features
--------
- Retrieves observations via `noaa_sdk`.
- Converts temperatures from °C to °F.
- Tracks unique cloudy days using a closure.
- Filters out missing (None) values.
- Produces three plots: time-series, box plot, and histogram.
- Prints raw observations, cloudy-day count, and statistics.
- Basic error handling for API failures.

Output Files
------------
- `weather.png`: Temperature & humidity time-series.
- `boxplot.png`: Box plot comparison.
- `temperature_histogram.png`: Temperature distribution.

Requirements
------------
- Python 3.x
- noaa_sdk (pip install noaa-sdk)
- matplotlib

Note
----
The NOAA API returns all observations in the requested window (typically
several hundred for ~10 days). Results are not guaranteed to cover a full 10
days if station reporting is sparse.
"""

from noaa_sdk import noaa
from collections import defaultdict
from uszipcode import SearchEngine
from typing import Dict, Any, Iterable
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
import datetime
import sys
import gc


class RowlandNoaaWeather:
    """Primary application class for NOAA weather analysis."""

    # ****************** METHODS

    def get_forecast_data(self) -> Dict[str, Any]:
        """Retrieve forecast periods from the National Weather Service API.

        Args:
            None

        Returns:
            Dict[str, Any]: Parsed JSON for forecast periods for the configured
                ZIP code.

        Examples:
            >>> forecast_data = self.get_forecast_data()
        """
        # Step 1: Get the forecast URL for the given zip code
        zipcode = self.zip_search.by_zipcode(self.zip_code)
        lat, lon = zipcode.lat, zipcode.lng

        headers = {"User-Agent": "(rowlandholden7@gmail.com)"}

        with requests.Session() as session:
            data_point_url = f"https://api.weather.gov/points/{lat},{lon}"
            data_request = session.get(data_point_url, headers=headers)
            data_request.raise_for_status()  # Raise an exception for HTTP errors
            forecast_url = data_request.json()["properties"]["forecast"]

            # Step 2: Get the forecast
            forecast_request = session.get(forecast_url, headers=headers)
            forecast_request.raise_for_status()  # Raise an exception for HTTP errors
            forecast_data = forecast_request.json()["properties"]["periods"]

        return forecast_data

    def get_noaa_data(self) -> Iterable[Dict[str, Any]]:
        """Collect raw observations from NOAA for the configured ZIP code.

        The method requests observations for roughly the previous 10 days
        and returns an iterable (generator) of observation dicts.

        Args:
            None

        Returns:
            Iterable[Dict[str, Any]]: Generator of observation records.

        Examples:
            >>> raw_data = list(self.get_noaa_data())
        """

        # API likes a start date and end date - calc those here.
        today = datetime.datetime.now()
        past = today - datetime.timedelta(days=10)
        start_date = past.strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        # Initialize NOAA API
        noaa_api = noaa.NOAA()

        # Try catch block for the API call
        try:
            # Fetch weather data for the specified date range and location
            weather_data = noaa_api.get_observations(
                self.zip_code, "US", start=start_date, end=end_date
            )

            # Ensure we received data
            first_item = next(weather_data, None)
            if first_item is None:
                raise ValueError(
                    "No observations returned for the specified period and location."
                )

            # Reset generator so caller can still iterate fully
            weather_data = noaa_api.get_observations(
                self.zip_code, "US", start=start_date, end=end_date
            )
            return weather_data

        except noaa.exceptions.NoaaSdkException as e:
            print(f"NOAA API error: {e}")
            print("Possible causes: invalid zip code, network issue, or API downtime.")
            sys.exit(1)
        except ValueError as e:
            print(f"Data error: {e}")
            sys.exit(1)

        except Exception as e:
            print(
                f"Unexpected error while fetching weather data: {type(e).__name__}: {e}"
            )
            print("Check your internet connection or try again later.")
            sys.exit(1)

    # Leave this commented out until sure it is not needed. I originally had this
    # function to generate the
    # temp and humidity lists but I found it easier to do it in the
    # collect_and_print_data function because we
    # need to track timestamps for the plots and we only want to track timestamps that
    # have valid data for the plots,
    # so it is easier to do it in the same place where we are generating the lists for
    # the plots.
    # def generate_lists(self, weather: Dict[str, Any], temp_list: list, humidity_list:
    # list) -> tuple[list, list]:
    #     """Generates two lists - temp_list to hold temps and humidity_list to hold
    # relative humidity
    #         these lists are used for the statistics that are printed

    #         Args:
    #             weather: the raw data record to work with
    #             temp_list: the list of temperatures
    #             humidity_list: the list of relative humidity percentages

    #         Returns:
    #             tuple[list, list]: returns the two lists with the new data appended

    #         Examples:
    #             >>> temp_list, humidity_list = self.generate_lists(weather, temp_list,
    # humidity_list)
    #         """
    #     temp_list.append(weather["temperature"]["value"])
    #     humidity_list.append(weather["relativeHumidity"]["value"])

    #     return temp_list, humidity_list

    def print_data(self, weather: Dict[str, Any]) -> None:
        """Print timestamp, temperature, humidity and textual description.

            Args:
                weather: the raw data record to work with

            Returns:
                None

            Examples:
                >>> self.print_data(weather)
        """
        print(
            weather["timestamp"],
            "\t",
            weather["temperature"]["value"],
            "°F\t",
            weather["relativeHumidity"]["value"],
            "\t",
            weather["textDescription"],
            "\t",
        )

    def extract_date(self, weather: Dict[str, Any]) -> str:
        """Return the date portion of a record timestamp for cloudy-day tracking.
        This prevents counting multiple records from the same date as separate
        cloudy days.

            Args:
                weather: the raw data record to work with

            Returns:
                str: the date portion of the time stamp from the raw data record

            Examples:
                >>> cur_date = extract_date(weather)
        """
        # In the raw data 'T' separates the date and time portions of the
        # ISO8601 timestamp
        pos = weather["timestamp"].find("T")
        new_date = weather["timestamp"][:pos]

        return new_date

    def get_cloudy_days(self) -> int:
        """Return a closure that tracks unique cloudy dates seen in observations.

        Args:
            None

        Returns:
            Callable: Tracking function that accepts (weather, current_count) and
            returns updated cloudy-day count.

        Examples:
            >>> tracker = self.get_cloudy_days()
            >>> count = tracker(weather, 0)
        """
        processed_dates = []
        cloudy_days = 0

        def tracking_dates(weather: Dict[str, Any], current_cloudy_days: int) -> int:
            nonlocal cloudy_days  # Get access to the counter in get_cloudy_days
            cur_date = self.extract_date(weather)

            # Count cloudy days
            if "cloudy" in weather["textDescription"].lower():
                if cur_date not in processed_dates:
                    cloudy_days += 1
                    processed_dates.append(cur_date)

            return cloudy_days

        return tracking_dates

    def convert_temp_to_F(self, weather: Dict[str, Any]) -> Dict[str, Any]:
        """Convert the temperature in an observation from °C to °F in-place.

        Args:
            weather: the raw data record we are working with

        Returns:
            Dict[str, Any]: the modified raw data record (same object passed in)

        Examples:
            >>> weather = self.convert_temp_to_F(weather)
        """
        temp = weather["temperature"]["value"]
        if temp is not None:
            temp = (temp * (9 / 5)) + 32
            temp = str(temp).strip()
            temp = float(temp)
            weather["temperature"]["value"] = temp

        return weather

    def collect_and_print_data(
        self, weather_data: Iterable[Dict[str, Any]]
    ) -> tuple[int, list, list, defaultdict[str, list[str]]]:
        """Process raw weather observations into lists for plotting and stats.

        Iterates `weather_data`, converts temperatures to °F, filters out
        missing values for plotting, and updates the cloudy-day tracker.

        Args:
            weather_data: Iterable of NOAA observation records.

        Returns:
            tuple[int, list, list, defaultdict]:
                (cloudy_days, temp_list, humidity_list, timestamps_for_plots)

        Examples:
            >>> cd, temps, hums, stamps = self.collect_and_print_data(weather_data)
        """
        cloudy_days_func = self.get_cloudy_days()
        temp_list = []
        humidity_list = []
        # We need to track timestamps for the plots, but we only want to track the
        # timestamps that have valid data for the plot, so we will use a dict of lists
        # to track them separately.
        timestamps_for_plots = defaultdict(list, {"temp": [], "humidity": []})

        # Print the weather data and populate the lists for temperature and humidity
        for weather in weather_data:
            weather = self.convert_temp_to_F(weather)  # Convert temp to F

            # Leave this line commented out until sure it is not needed.
            # temp_list, humidity_list = self.generate_lists(weather, temp_list,
            # humidity_list)

            if weather["temperature"]["value"] is not None:
                # Add timestamp and temp value only when temp data is valid
                timestamps_for_plots["temp"].append(weather["timestamp"])
                temp_list.append(weather["temperature"]["value"])

            if weather["relativeHumidity"]["value"] is not None:
                # Add timestamp and humidity value only when humidity data is valid
                timestamps_for_plots["humidity"].append(weather["timestamp"])
                humidity_list.append(weather["relativeHumidity"]["value"])

            # Update cloudy day count via closure returned by get_cloudy_days
            self.cloudy_days = cloudy_days_func(weather, self.cloudy_days)

            #self.print_data(weather)

        return self.cloudy_days, temp_list, humidity_list, timestamps_for_plots

    def get_unique_days(self, timestamps: list) -> int:
        """Calulates the number of unique days represented in the timestamps of the noaa
        data records. This is used to provide more accurate information about how many
        days of data were fetched. This information is displyed to the user in the GUI
        in the statistics tab.

        Args:
            None

        Returns:
            int: Number of unique days represented in the timestamps of the
                NOAA data records.

        Examples:
            get_unique_days()
        """
        unique_days = set()
        for timestamp in timestamps:
            day = timestamp.split("T")[0]  # Extract the date part (YYYY-MM-DD)
            unique_days.add(day)
        return len(unique_days)

    def init_weather_data(self) -> tuple[list, list, defaultdict[str, list[str]]]:
        """Fetch and process observations, returning lists and timestamps for plots.

        Args:
            None

        Returns:
            tuple[list, list, defaultdict]:
                (temp_list, humidity_list, timestamps_for_plots)

        Examples:
            >>> temps, hums, stamps = self.init_weather_data()
        """
        weather_data = self.get_noaa_data()

        self.cloudy_days, temp_list, humidity_list, timestamps_for_plots = (
            self.collect_and_print_data(weather_data)
        )

        unique_days = self.get_unique_days(timestamps_for_plots)
        print()
        print(f"Number of days in historical data: {unique_days}")
        # Lets put a blank line between raw data and readable data
        print()
        print(f"Number of cloudy days in the last {unique_days} days: {self.cloudy_days}")

        return temp_list, humidity_list, timestamps_for_plots

    def create_plots(
        self,
        temp_list: list,
        humidity_list: list,
        timestamps_for_plots: defaultdict[str, list[str]],
    ) -> None:
        """Generate and save time-series, boxplot and histogram images.

        Args:
            temp_list: temperatures from the raw data.
            humidity_list: humidity values from the raw data.
            timestamps_for_plots: dict-of-lists containing timestamps for the
                temp and humidity values used for plotting.

        Returns:
            None

        Examples:
            >>> self.create_plots(temp_list, humidity_list, timestamps_for_plots)
        """
        self.create_standard(temp_list, humidity_list, timestamps_for_plots)
        self.create_box_plot(temp_list, humidity_list)
        self.create_histogram(temp_list)

    def create_standard(
        self,
        temp_list: list,
        humidity_list: list,
        timestamps_for_plots: defaultdict[str, list[str]],
    ) -> None:
        """Create the main time-series plot and save it as a PNG file.

        Note: The NOAA API may not return a full 10 days of data depending on
        station reporting frequency.

            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
                timestamps_for_plots: dict of lists with timestamps to plot

            Returns:
                None

            Examples:
                >>> create_standard(temp_list, humidity_list, timestamps_for_plots)
        """
        # Commented out as this block moved to it's own method to convert the timestamps
        # to
        # datetime objects for better plotting.
        # Convert string timestamps to datetime objects for better plotting
        # for i in range(len(timestamps_for_plots["temp"])):
        #     timestamps_for_plots["temp"][i] =
        # datetime.datetime.fromisoformat(timestamps_for_plots["temp"][i].replace('Z',
        # '+00:00'))

        # for i in range(len(timestamps_for_plots["humidity"])):
        #     timestamps_for_plots["humidity"][i] = datetime.datetime.fromisoformat(time
        # stamps_for_plots["humidity"][i].replace('Z', '+00:00'))

        plt.figure(figsize=(14, 7))  # Wider figure for time axis
        plt.plot(
            timestamps_for_plots["temp"],
            temp_list,
            label="Temperature (°F)",
            color="red",
            linewidth=1.5,
        )
        plt.plot(
            timestamps_for_plots["humidity"],
            humidity_list,
            label="Humidity (%)",
            color="blue",
            linewidth=1.5,
        )

        plt.legend(loc="upper right")
        plt.title(f"Temperature and Humidity Over Time (ZIP {self.zip_code})")
        plt.xlabel("Observation Time")
        plt.ylabel("Value")

        # Smart date formatting: show major ticks nicely (e.g., daily or every few
        # hours)
        plt.gca().xaxis.set_major_locator(
            mdates.AutoDateLocator(maxticks=15)
        )  # Limit ~15 labels
        plt.gca().xaxis.set_major_formatter(
            mdates.DateFormatter("%m-%d %H:%M")
        )  # Month-Day Hour:Minute

        plt.xticks(rotation=45, ha="right", fontsize=9)
        plt.grid(True, linestyle="--", alpha=0.5)

        plt.tight_layout()  # Prevents label cutoff
        plt.savefig("weather.png", dpi=150)  # Higher dpi for clearer saved image
        plt.close()  # Close the plot to free memory
        gc.collect()  # Force garbage collection to free memory used by the plot

    def create_box_plot(self, temp_list: list, humidity_list: list) -> None:
        """Creates a box plot comparing temperature and humidity distributions.

        Args:
            temp_list: temperatures that were in the raw data
            humidity_list: humidity values that were in the raw data

        Returns:
            None

        Examples:
            >>> self.create_box_plot(temp_list, humidity_list)
        """
        # Create a box plot
        plt.figure()
        box_data = [temp_list, humidity_list]
        plt.boxplot(box_data, tick_labels=["Temperature", "Humidity"])
        plt.suptitle(f"Box Plot (ZIP {self.zip_code})")
        plt.savefig("boxplot.png")  # Save the box plot as an image file
        plt.close()  # Close the plot to free memory
        gc.collect()  # Force garbage collection to free memory used by the plot

    def create_histogram(self, temp_list: list) -> None:
        """Creates a histogram of temperature distribution and saves it to disk.

        Args:
            temp_list: temperatures that were in the raw data

        Returns:
            None

        Examples:
            >>> self.create_histogram(temp_list)
        """
        # Create a histogram for temperature
        plt.figure()
        plt.hist(temp_list, bins=10, color="red", alpha=0.7)
        plt.suptitle(f"Temperature Distribution (ZIP {self.zip_code})")
        plt.xlabel("Temperature (°F)")
        plt.ylabel("Frequency")
        plt.savefig("temperature_histogram.png")  # Save the histogram as an image file
        plt.close()  # Close the plot to free memory
        gc.collect()  # Force garbage collection to free memory used by the plot

    def print_temp_stats(self, temp_list: list) -> None:
        """Compute basic temperature statistics (avg, min, max).

        Args:
            temp_list: temperatures that were in the raw data

        Returns:
            None

        Examples:
            >>> self.print_temp_stats(temp_list)
        """
        ave_temp = sum(temp_list) / len(temp_list)
        low_temp = min(temp_list)
        high_temp = max(temp_list)

        print(f"The average temperature was: {round(ave_temp, 1)}°F")
        print(f"The lowest temperature was: {round(low_temp, 1)}°F")
        print(f"The highest temperature was: {round(high_temp, 1)}°F")

    def print_humidity_stats(self, humidity_list: list) -> None:
        """Compute basic humidity statistics (avg, min, max).

        Args:
            humidity_list: humidity values that were in the raw data

        Returns:
            None

        Examples:
            >>> self.print_humidity_stats(humidity_list)
        """
        ave_humidity = sum(humidity_list) / len(humidity_list)
        low_humidity = min(humidity_list)
        high_humidity = max(humidity_list)

        print(f"The average humidity was: {round(ave_humidity, 1)}%")
        print(f"The lowest humidity was: {round(low_humidity, 1)} %")
        print(f"The highest humidity was: {round(high_humidity, 1)}%")

    def calculate_and_print_statistics(
        self, temp_list: list, humidity_list: list
    ) -> None:
        """Aggregate temperature and humidity statistics and optionally print them.

        Args:
            temp_list: temperatures that were in the raw data
            humidity_list: humidity values that were in the raw data

        Returns:
            None

        Examples:
            >>> self.calculate_and_print_statistics(temp_list, humidity_list)
        """

        print()  # Blank line before statistics
        print(f"Historical Weather Statistics for the last {self.cloudy_days} days")
        print("---------------------------------------------------------------------------------")
        # Print temp data
        self.print_temp_stats(temp_list)
        print()  # Blank line between temp and humidity
        # Print humidity data
        self.print_humidity_stats(humidity_list)

    def print_student_name(self) -> None:
        """Print or return the student's name used in program output.

        Args:
            None

        Returns:
            None

        Examples:
            >>> self.print_student_name()
        """
        name = "Rowland Holden"
        print(name)  # Print student name

    def convert_time_stamps(self, timestamps_for_plots: defaultdict) -> defaultdict:
        """Convert ISO8601 timestamp strings to datetime objects suitable for plotting.

        Args:
            timestamps_for_plots: the dict of lists that contains the timestamps for the
                temp and humidity data that we want to plot

        Returns:
           timestamps_for_plots: the same dict but with timestamps converted to
                datetime objects for plotting

        Examples:
            >>> self.convert_time_stamps(timestamps_for_plots)
        """
        for key in ["temp", "humidity"]:
            if key in timestamps_for_plots:
                timestamps_for_plots[key] = [
                    datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    for ts in timestamps_for_plots[key]
                ]
        # Convert string timestamps to datetime objects for better plotting
        # for i in range(len(timestamps_for_plots["temp"])):
        #     timestamps_for_plots["temp"][i] =
        # datetime.datetime.fromisoformat(timestamps_for_plots["temp"][i].replace('Z',
        # '+00:00'))

        # for i in range(len(timestamps_for_plots["humidity"])):
        #     timestamps_for_plots["humidity"][i] = datetime.datetime.fromisoformat(time
        # stamps_for_plots["humidity"][i].replace('Z', '+00:00'))

        return timestamps_for_plots

    def print_forecast_data(self, forecast_data: Dict[str, Any]) -> None:
        """Print the forecast periods retrieved from the National Weather Service API.

        Args:
            forecast_data: Dict containing forecast periods for the configured ZIP code.

        Returns:
            None

        Examples:
            >>> self.print_forecast_data(forecast_data)
        """
        print()  # Blank line before forecast data
        print("Forecast:")
        print("---------------------------------------------------------------------------------")

        for period in forecast_data:
            chance = (
                period["probabilityOfPrecipitation"]["value"] or 0
            )  # default to 0 if None

            day = period["name"]
            temp = f"{period['temperature']}°F"
            desc = period["shortForecast"]

            line = f"{day:<17} {temp:<18} {desc:<45} {chance}%\n"
            print(line)

    def print_record_stats(self, temp_list: list, humidity_list: list) -> None:
        """Print record high and low temperatures for the configured ZIP code.

        Args:
            temp_list: List of temperature values.
            humidity_list: List of humidity values.

        Returns:
            None
        Examples:
            >>> self.print_record_stats()
        """
        print()  # Blank line between raw data and processed number info
        print(
            f"processed {len(temp_list)} valid temperatures found in "
            f"Noaa observations for zip code {self.zip_code}"
        )
        print(
            f"processed {len(humidity_list)} valid humidity values found in "
            f"Noaa observations for zip code {self.zip_code}"
        )
        print() 

    def main(self) -> None:
        """Main entry point for the program; orchestrates fetch, process and plot steps.

        Args:
            None

        Returns:
            None

        Examples:
            >>> app = RowlandNoaaWeather()
            >>> app.main()
        """
        self.print_student_name()
        temp_list, humidity_list, timestamps_for_plots = self.init_weather_data()
        # leave this commented out until sure it is not needed. I originally had this
        # function to
        # clean the data but I found it easier to do it in the collect_and_print_data
        # function because we
        # need to track timestamps for the plots and we only want to track timestamps
        # that have valid
        # data for the plots, so it is easier to do it in the same place where we are
        # generating the
        # lists for the plots.
        # temp_list, humidity_list = self.clean_data(temp_list, humidity_list)
        # Convert timestamps to datetime objects for plotting. Doing it here keeps
        # converted values available for all plot routines.
        timestamps_for_plots = self.convert_time_stamps(timestamps_for_plots)
        self.create_plots(temp_list, humidity_list, timestamps_for_plots)
        self.calculate_and_print_statistics(temp_list, humidity_list)
        self.print_forecast_data(self.get_forecast_data())
        self.print_record_stats(temp_list, humidity_list)

    def __init__(self, zip_entry: str = "98204") -> None:
        """Called when creating the `RowlandNoaaWeather` instance.

        Args:
            zip_entry: ZIP code used to fetch NOAA observations (default "98204").

        Returns:
            None

        Examples:
            >>> weather_app = RowlandNoaaWeather()
        """
        self.cloudy_days = 0
        self.zip_code = zip_entry
        self.zip_search = SearchEngine(simple_zipcode=True)


# ********************* SCRIPT

def main() -> None:
    """Module-level entry point to run the backend as a script or console command.

    This wrapper allows packaging tools to expose the backend via
    `console_scripts` by pointing to `noaa_weather_backend:main`.
    """
    noaa_weather = RowlandNoaaWeather()
    noaa_weather.main()


if __name__ == "__main__":
    main()
