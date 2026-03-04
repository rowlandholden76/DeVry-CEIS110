"""
NOAA Weather Data Analyzer
==========================

Author:    Rowland Holden
Date:      Feb 17, 2026 (extended version)
Course:    CEIS 101 - Final Project (Enhanced)
Purpose:   Fetch recent weather observations from NOAA's API for Everett, WA (ZIP 98204),
           process temperature (converted to °F) and relative humidity data over the 
           past ~10 days, count unique cloudy days, generate visualizations, and 
           compute basic statistics.

Features:
- Retrieves weather observations using noaa_sdk
- Converts temperatures from °C to °F
- Tracks unique cloudy days using a closure
- Filters out missing (None) values
- Creates three plots: time-series line plot, box plot, temperature histogram
- Prints raw observations, cloudy day count, and detailed statistics
- Includes timestamps on the main plot for better readability - can't read the timestamps though, do much data crammed in
- Basic error handling for API failures

Output Files:
- weather.png          : Temperature & Humidity over time
- boxplot.png          : Box plot comparison
- temperature_histogram.png : Temperature distribution

Requirements:
- Python 3.x
- noaa_sdk (pip install noaa-sdk)
- matplotlib

Note: The NOAA API returns all available observations in the requested time window 
    (typically several hundred for ~10 days, depending on station reporting frequency—e.g., hourly or more frequent). 
    Not guaranteed to cover full 10 days if data is sparse.
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

class RowlandNoaaWeather: # Named as such to ensure it will never conflict with another class name. 

    # ****************** METHODS

    def get_forecast_data(self) -> Dict[str, Any]:
        """Retrieve forecast periods from the National Weather Service API.

            Args:
                None

            Returns:
                Dict[str, Any]: Parsed JSON for forecast periods for the configured ZIP code.

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
            weather_data = noaa_api.get_observations(self.zip_code, "US", start = start_date, end = end_date)

            # Ensure we received data
            first_item = next(weather_data, None)
            if first_item is None:
                raise ValueError("No observations returned for the specified period and location.")
            
            # Reset generator so caller can still iterate fully
            weather_data = noaa_api.get_observations(self.zip_code, "US", start=start_date, end=end_date)
            return weather_data
        
        except noaa.exceptions.NoaaSdkException as e:
            print(f"NOAA API error: {e}")
            print("Possible causes: invalid zip code, network issue, or API downtime.")
            sys.exit(1)
        except ValueError as e:
            print(f"Data error: {e}")
            sys.exit(1)
    
        except Exception as e:
            print(f"Unexpected error while fetching weather data: {type(e).__name__}: {e}")
            print("Check your internet connection or try again later.")
            sys.exit(1)

    # Leave this commented out until sure it is not needed. I originally had this function to generate the 
    # temp and humidity lists but I found it easier to do it in the collect_and_print_data function because we 
    # need to track timestamps for the plots and we only want to track timestamps that have valid data for the plots, 
    # so it is easier to do it in the same place where we are generating the lists for the plots.
    # def generate_lists(self, weather: Dict[str, Any], temp_list: list, humidity_list: list) -> tuple[list, list]:
    #     """Generates two lists - temp_list to hold temps and humidity_list to hold relative humidity
    #         these lists are used for the statistics that are printed
            
    #         Args:
    #             weather: the raw data record to work with
    #             temp_list: the list of temperatures
    #             humidity_list: the list of relative humidity percentages
            
    #         Returns:
    #             tuple[list, list]: returns the two lists with the new data appended
            
    #         Examples:
    #             >>> temp_list, humidity_list = self.generate_lists(weather, temp_list, humidity_list)
    #         """
    #     temp_list.append(weather["temperature"]["value"])
    #     humidity_list.append(weather["relativeHumidity"]["value"])

    #     return temp_list, humidity_list

    def print_data(self, weather: Dict[str, Any]) -> None:
        """prints the current raw records time stamp, temperature, relative humidity and description(cloudy, clear, rainy etc.)
            
            Args:
                weather: the raw data record to work with

            Returns:
                None

            Examples:
                >>> self.print_data(weather)
            """
        print(weather["timestamp"], "\t",
                weather["temperature"]["value"], "°F\t",
                weather["relativeHumidity"]["value"], "\t",
                weather["textDescription"], "\t",)
        
    def extract_date(self, weather: Dict[str, Any]) -> str:
        """Gets the date portion of the timestamp from the current record of the raw data, used to track cloudy days.
            we don't want to count the same cloudy day twice and the raw data has many records involving different readings
            on the same day
            
            Args:
                weather: the raw data record to work with
            
            Returns:
                str: the date portion of the time stamp from the raw data record
            
            Examples:
                >>> cur_date = extract_date(weather)
            """
        pos = weather["timestamp"].find("T") # In the raw data "T" indicates the beginning of the time portion of the time stamp
        new_date = weather["timestamp"][:pos]

        return new_date

    def get_cloudy_days(self) -> int:
        """Return a closure that tracks unique cloudy dates seen in observations.

            Args:
                None

            Returns:
                Callable: A tracking function accepting (weather, current_count) and returning updated cloudy day count.

            Examples:
                >>> tracker = self.get_cloudy_days()
                >>> count = tracker(weather, 0)
            """
        processed_dates = []
        cloudy_days = 0

        def tracking_dates(weather: Dict[str, Any], current_cloudy_days: int) -> int:
            nonlocal cloudy_days # Get access to the counter in get_cloudy_days
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
            temp = (temp * (9/5)) + 32 
            temp = str(temp).strip() 
            temp = float(temp) 
            weather["temperature"]["value"] = temp

        return weather

    def collect_and_print_data(self, weather_data: Iterable[Dict[str, Any]]) -> tuple[int, list, list, defaultdict[str, list[str]]]:
        """Process raw weather observations into lists for plotting and stats.

            Iterates `weather_data`, converts temperatures to °F, filters out
            missing values for plotting, and updates the cloudy-day tracker.

            Args:
                weather_data: Iterable of NOAA observation records.

            Returns:
                tuple[int, list, list, defaultdict]: (cloudy_days, temp_list, humidity_list, timestamps_for_plots)

            Examples:
                >>> cd, temps, hums, stamps = self.collect_and_print_data(weather_data)
            """
        cloudy_days_func = self.get_cloudy_days()
        temp_list = []
        humidity_list = []
        # We need to track timestamps for the plots, but we only want to track the 
        # timestamps that have valid data for the plot, so we will use a dict of lists to track them separately.
        timestamps_for_plots = defaultdict(list, {"temp": [], "humidity": []})

        # Print the weather data and populate the lists for temperature and humidity
        for weather in weather_data:
            weather = self.convert_temp_to_F(weather) # Convert temp to F
               
            # Leave this line commented out until sure it is not needed. 
            #temp_list, humidity_list = self.generate_lists(weather, temp_list, humidity_list)

            if weather["temperature"]["value"] is not None:
                timestamps_for_plots["temp"].append(weather["timestamp"]) # We only want to add timestamps that have valid temp data for plotting
                temp_list.append(weather["temperature"]["value"]) # We need to append the temp value here as well because we are filtering out None values in the clean_data function, so we need to make sure the lists are the same length as the timestamps for plotting. We could do this in the clean_data function but it is easier to do it here.

            if weather["relativeHumidity"]["value"] is not None:
                timestamps_for_plots["humidity"].append(weather["timestamp"]) # We only want to add timestamps that have valid humidity data for plotting
                humidity_list.append(weather["relativeHumidity"]["value"]) # We need to append the humidity value here as well because we are filtering out None values in the clean_data function, so we need to make sure the lists are the same length as the timestamps for plotting. We could do this in the clean_data function but it is easier to do it here.
                
            self.cloudy_days = cloudy_days_func(weather, self.cloudy_days) # This is a closure function called get_cloudy_days
            
            self.print_data(weather)

        print() # Blank line between raw data and processed number info
        print(f"processed {len(temp_list)} valid temperatures found in Noaa observations for zip code {self.zip_code}")
        print(f"processed {len(humidity_list)} valid humidity values found in Noaa observations for zip code {self.zip_code}")

        return self.cloudy_days, temp_list, humidity_list, timestamps_for_plots

    def init_weather_data(self) -> tuple[list, list, defaultdict[str, list[str]]]:
        """Fetch and process observations, returning lists and timestamps for plots.

            Args:
                None

            Returns:
                tuple[list, list, defaultdict]: (temp_list, humidity_list, timestamps_for_plots)

            Examples:
                >>> temps, hums, stamps = self.init_weather_data()
            """
        weather_data = self.get_noaa_data()

        self.cloudy_days, temp_list, humidity_list, timestamps_for_plots = self.collect_and_print_data(weather_data)

        # Lets put a blank line between raw data and readable data
        print()
        print(f"Number of cloudy days in the last 10 days: {self.cloudy_days}")
       

        return temp_list, humidity_list,timestamps_for_plots

    def create_plots(self, temp_list: list, humidity_list: list, timestamps_for_plots: defaultdict[str, list[str]]) -> None:
        """Generate and save the time-series, boxplot and histogram images.

            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
                timestamps_for_plots: the dict of lists that contains the timestamps for the temp and 
                    humidity data that we want to plot

            Returns:
                None

            Examples:
                >>> self.create_plots(temp_list, humidity_list, timestamps_for_plots)
            """
        self.create_standard(temp_list, humidity_list, timestamps_for_plots)
        self.create_box_plot(temp_list, humidity_list)
        self.create_histogram(temp_list)

    def create_standard(self, temp_list: list, humidity_list: list, timestamps_for_plots: defaultdict[str, list[str]]) -> None:
        """Creates a standard plot using the matplotlib.pyplot class. Also saves the plot as a png file
            While we asked for 10 days of data, the noaa API will only return what it has, so we may not get 10 days
            
            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
                timestamps_for_plots: the dict of lists that contains the timestamps for the temp and 
                    humidity data that we want to plot
            
            Returns:
                None

            Examples:
                >>> create_standard(temp_list, humidity_list, timestamps_for_plots)
            """
        # Commented out as this block moved to it's own method to convert the timestamps to 
        # datetime objects for better plotting.
        # Convert string timestamps to datetime objects for better plotting
        # for i in range(len(timestamps_for_plots["temp"])):
        #     timestamps_for_plots["temp"][i] = datetime.datetime.fromisoformat(timestamps_for_plots["temp"][i].replace('Z', '+00:00'))

        # for i in range(len(timestamps_for_plots["humidity"])):
        #     timestamps_for_plots["humidity"][i] = datetime.datetime.fromisoformat(timestamps_for_plots["humidity"][i].replace('Z', '+00:00'))

        plt.figure(figsize=(14, 7))  # Wider figure for time axis
        plt.plot(timestamps_for_plots["temp"], temp_list, label="Temperature (°F)", color="red", linewidth=1.5)
        plt.plot(timestamps_for_plots["humidity"], humidity_list, label="Humidity (%)", color="blue", linewidth=1.5)
        
        plt.legend(loc="upper right")
        plt.title(f"Temperature and Humidity Over Time (ZIP {self.zip_code})")
        plt.xlabel("Observation Time")
        plt.ylabel("Value")
        
        # Smart date formatting: show major ticks nicely (e.g., daily or every few hours)
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=15))  # Limit ~15 labels
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))  # Month-Day Hour:Minute
        
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.grid(True, linestyle='--', alpha=0.5)
        
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

    def calculate_and_print_statistics(self, temp_list: list, humidity_list: list) -> None:
        """Aggregate temperature and humidity statistics and optionally print them.

            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data

            Returns:
                None

            Examples:
                >>> self.calculate_and_print_statistics(temp_list, humidity_list)
            """

        print() # Blank line before statistics
        print("Weather Statistics")
        # Print temp data
        self.print_temp_stats(temp_list)
        print() #Blank line between temp and humidity
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
        print(name) # Print student name

    def convert_time_stamps(self, timestamps_for_plots: defaultdict) -> defaultdict:
        """Convert ISO8601 timestamp strings to datetime objects suitable for plotting.

            Args:
                timestamps_for_plots: the dict of lists that contains the timestamps for the 
                    temp and humidity data that we want to plot

            Returns:
                timestamps_for_plots: the same dict of lists but with the timestamps converted to 
                    datetime objects for better plotting

            Examples:
                >>> self.convert_time_stamps(timestamps_for_plots)
            """
        for key in ["temp", "humidity"]:
            if key in timestamps_for_plots:
                timestamps_for_plots[key] = [
                datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                for ts in timestamps_for_plots[key]
            ]
         # Convert string timestamps to datetime objects for better plotting
        # for i in range(len(timestamps_for_plots["temp"])):
        #     timestamps_for_plots["temp"][i] = datetime.datetime.fromisoformat(timestamps_for_plots["temp"][i].replace('Z', '+00:00'))

        # for i in range(len(timestamps_for_plots["humidity"])):
        #     timestamps_for_plots["humidity"][i] = datetime.datetime.fromisoformat(timestamps_for_plots["humidity"][i].replace('Z', '+00:00'))
        
        return timestamps_for_plots


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
        #leave this commented out until sure it is not needed. I originally had this function to 
        # clean the data but I found it easier to do it in the collect_and_print_data function because we
        # need to track timestamps for the plots and we only want to track timestamps that have valid
        # data for the plots, so it is easier to do it in the same place where we are generating the
        # lists for the plots.
        #temp_list, humidity_list = self.clean_data(temp_list, humidity_list)
        timestamps_for_plots = self.convert_time_stamps(timestamps_for_plots) # We need to convert the time stamps to datetime objects for plotting, we can do this in the create_standard function but it is easier to do it here so we only have to do it once and we can use the converted timestamps for all the plots if we want to.
        self.create_plots(temp_list, humidity_list, timestamps_for_plots)
        self.calculate_and_print_statistics(temp_list, humidity_list)
    
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

if __name__ == "__main__":

    noaa_weather = RowlandNoaaWeather()
    noaa_weather.main()
