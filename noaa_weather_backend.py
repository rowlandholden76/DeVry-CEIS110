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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Dict, Any, Iterable
import datetime
import sys

class RowlandNoaaWeather: # Named as such to ensure it will never conflict with another class name. 

    # ****************** FUNCTIONS

    # Use the noaa api to get weather data
    def get_noaa_data(self) -> tuple[Iterable[Dict[str, Any]], str]:
        """collects raw data from the Noaa API
            
            Args:
                None
            
            Returns:
                tuple[Iterable[Dict[str, Any]], str]: Generator - we are only using the Iterable side though, so we are using Dict, the other
                is the zip code. Need this so we can print the valid records processed message. 
            
            Examples:
                >>> raw_data = self.get_noaa_data()
                >>> weather_data = self.get_noaa_data()
            """
        
        # API likes a start date and end date - calc those here. 
        today = datetime.datetime.now()
        past = today - datetime.timedelta(days=10)
        start_date = past.strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        zip_code = "98204"  # Everett Washington Zip Code for API

        # Initialize NOAA API
        noaa_api = noaa.NOAA()

        # Try catch block for the API call
        try:
        # Fetch weather data for the specified date range and location
            weather_data = noaa_api.get_observations(zip_code, "US", start = start_date, end = end_date)

            # Ensure we received data
            first_item = next(weather_data, None)
            if first_item is None:
                raise ValueError("No observations returned for the specified period and location.")
            
            # Reset generator so caller can still iterate fully
            weather_data = noaa_api.get_observations(zip_code, "US", start=start_date, end=end_date)
            return weather_data, zip_code
        
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

    def generate_lists(self, weather: Dict[str, Any], temp_list: list, humidity_list: list) -> tuple[list, list]:
        """Generates two lists - temp_list to hold temps and humidity_list to hold relative humidity
            these lists are used for the statistics that are printed
            
            Args:
                weather: the raw data record to work with
                temp_list: the list of temperatures
                humidity_list: the list of relative humidity percentages
            
            Returns:
                tuple[list, list]: returns the two lists with the new data appended
            
            Examples:
                >>> temp_list, humidity_list = self.generate_lists(weather, temp_list, humidity_list)
            """
        temp_list.append(weather["temperature"]["value"])
        humidity_list.append(weather["relativeHumidity"]["value"])

        return temp_list, humidity_list

    def print_data(self, weather: Dict[str, Any]) -> None:
        """prints the current raw records time stamp, temperature, relative humidity and description(cloudy, clear, rainy etc.)
            
            Args:
                weather: the raw data record to work with
            
            Returns:
                None
            
            Examples:
                >>> print_data(weather)
            """
        print(weather["timestamp"], "\t",
                weather["temperature"]["value"], " °F\t",
                weather["relativeHumidity"]["value"], "\t",
                weather["textDescription"], "\t",)
        
    def extract_date(self, weather: Dict[str, Any]) -> str:
        """Gets the date portion of the timestamp from the current record of the raw data, used to track cloudy days.
            we don't want to cound the same cloudy day twice and the raw data has many records involving different readings
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
        """a wrapper function for Tracking days. need this o make processed dates persistent across calls so it will
            remember the dates it has already in the list. I find how this works to be increadable. 
            
            Args:
                None
            
            Returns:
                int: the number of cloudy days that tracking dates returned

            Examples:
                >>> In your calling function you do two things
                        1. initalize this function to a variable(do this outside of the loop you are using to count the days)
                            get_cloudy_days_func = get_cloudy_days()
                        2. inside the loop you call the variable with the arguments
                            num_of_cloudy_days = get_cloudy_days_func(weather, num_of_cloudy_days)
            """
        processed_dates = []

        def tracking_dates(weather: Dict[str, Any], current_cloudy_days: int) -> int:
            nonlocal processed_dates # Get access to the list in get_cloudy_days
            cur_date = self.extract_date(weather)
            cloudy_days = current_cloudy_days # ensure the origional data is not overwritten

            # Count cloudy days
            if "cloudy" in weather["textDescription"].lower(): 
                if cur_date not in processed_dates:
                    cloudy_days += 1
                    processed_dates.append(cur_date)

            return cloudy_days

        return tracking_dates

    def convert_temp_to_F(self, weather: Dict[str, Any]) -> Dict[str, Any]:
        """convert C to F in the raw data so when it prints it is in F
            NOTE: This works directly with the raw data changing it place, it is not immutabile
            
            Args:
                weather: the raw data record we are working with
            
            Returns:
                Dict[str, Any]: the modified raw data record

            Examples:
                >>> weather = convert_temp_to_F(weather)
            """
        temp = weather["temperature"]["value"] 
        if temp != None: temp = (temp * (9/5)) + 32 
        weather["temperature"]["value"] = temp

        return weather

    def collect_and_print_data(self, weather_data: Iterable[Dict[str, Any]], zip_code: int) -> tuple[int, list, list, list]:
        """Collects the data to the two lists, temp_list and humidity_list. Gets the number of cloudy days.
            and converts the temps in the raw data to F
            
            Args:
                weather: the raw data record we are working with
                zip_code: Zip code that the collected data represents
            
            Returns:
                tuple[int, list, list, list]: the two lists that were generated

            Examples:
                >>> weather = convert_temp_to_F(weather)
            """
        cloudy_days = 0
        cloudy_days_func = self.get_cloudy_days()
        temp_list = []
        humidity_list = []
        timestamps_for_plots = []

        # Print the weather data and populate the lists for temperature and humidity
        for weather in weather_data:
            weather = self.convert_temp_to_F(weather) # Convert temp to F
            timestamps_for_plots.append(weather["timestamp"])
               
            temp_list, humidity_list = self.generate_lists(weather, temp_list, humidity_list)

            cloudy_days = cloudy_days_func(weather, cloudy_days) # This is a closure function called get_cloudy_days
            
            self.print_data(weather)

        print() # Blank line between raw data and processed number info
        print(f"processed {len(temp_list)} valid temperatures found in Noaa observations for zip code {zip_code}")
        print(f"processed {len(humidity_list)} valid humidity values found in Noaa observations for zip code {zip_code}")

        return cloudy_days, temp_list, humidity_list, timestamps_for_plots

    def init_weather_data(self) -> tuple[list, list]:
        """Initialize and collect the raw data, build the lists temp_list and humidiy_list
            convert C to F and print the raw data
            
            Args:
                None
            
            Returns:
                tuple[list, list]: the two lists that were generated

            Examples:
                >>> init_weather_data()
            """
        weather_data, zip_code = self.get_noaa_data()

        cloudy_days, temp_list, humidity_list, timestamps_for_plots = self.collect_and_print_data(weather_data, zip_code)

        # Lets put a blank line between raw data and readable data
        print()
        print(f"Number of cloudy days in the last 10 days: {cloudy_days}")
       

        return temp_list, humidity_list,timestamps_for_plots

    def clean_data(self, temp_list: list, humidity_list: list) -> tuple[list, list]:
        """Cleaning the data by getting rid of any "None" values in the raw data. This will ensure accruate plotting later
            
            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
            
            Returns:
                tuple[list, list]: the two lists that were filtered

            Examples:
                >>> temp_list, humidity_list = clean_data(temp_list, humidity_list)
            """
        start_humid_len = len(humidity_list)
        start_temp_len = len(temp_list)

        humidity_list = list(filter(None, humidity_list))
        temp_list = list(filter(None, temp_list))
        end_humid_len = len(humidity_list)
        end_temp_len = len(temp_list)

        Hum_rec_removed = start_humid_len - end_humid_len
        temp_rec_removed = start_temp_len - end_temp_len

        print() # Blank line before showing how many records were removed
        print(f"Removed {temp_rec_removed} temperature values")
        print(f"Removed {Hum_rec_removed} humidity values")

        return temp_list, humidity_list

    def create_plots(self, temp_list: list, humidity_list: list, timestamps_for_plots: list) -> None:
        """Calls functions to create a standard, box and histogram plot
            
            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
            
            Returns:
                None

            Examples:
                >>> create_plots(temp_list, humidity_list)
            """
        self.create_standard(temp_list, humidity_list, timestamps_for_plots)
        self.create_box_plot(temp_list, humidity_list)
        self.create_histogram(temp_list)

    def create_standard(self, temp_list: list, humidity_list: list, timestamps_for_plots: list) -> None:
        """Creates a standard plot using the matplotlib.pyplot class. Also saves the plot as a png file
            While we asked for 10 days of data, the noaa API will only return what it has, so we may not get 10 days
            
            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
            
            Returns:
                None

            Examples:
                >>> create_standard(temp_list, humidity_list)
            """
        # Convert string timestamps to datetime objects for better plotting
        dt_timestamps = [datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps_for_plots]

        plt.figure(figsize=(14, 7))  # Wider figure for time axis
        plt.plot(dt_timestamps, temp_list, label="Temperature (°F)", color="red", linewidth=1.5)
        plt.plot(dt_timestamps, humidity_list, label="Humidity (%)", color="blue", linewidth=1.5)
        
        plt.legend(loc="upper right")
        plt.title("Temperature and Humidity Over Time (ZIP 98204)")
        plt.xlabel("Observation Time")
        plt.ylabel("Value")
        
        # Smart date formatting: show major ticks nicely (e.g., daily or every few hours)
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=15))  # Limit ~15 labels
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))  # Month-Day Hour:Minute
        
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()  # Prevents label cutoff
        plt.savefig("weather.png", dpi=150)  # Higher dpi for clearer saved image

    def create_box_plot(self, temp_list: list, humidity_list: list) -> None:
        """Creates a box plot using the matplotlib.pyplot class. Also saves the plot as a png file
            
            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
            
            Returns:
                None

            Examples:
                >>> create_box_plot(temp_list, humidity_list)
            """
        # Create a box plot
        plt.figure()
        box_data = [temp_list, humidity_list]
        plt.boxplot(box_data, tick_labels=["Temperature", "Humidity"])
        plt.suptitle("Box Plot")
        plt.savefig("boxplot.png")  # Save the box plot as an image file

    def create_histogram(self, temp_list: list) -> None:
        """Creates a histogram of temperature distribution using the matplotlib.pyplot class. Also saves the plot as a png file
            
            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
            
            Returns:
                None

            Examples:
                >>> create_histogram(temp_list, humidity_list)
            """
        # Create a histogram for temperature
        plt.figure()
        plt.hist(temp_list, bins=10, color="red", alpha=0.7)
        plt.suptitle("Temperature Distribution")
        plt.xlabel("Temperature (°F)")
        plt.ylabel("Frequency")
        plt.savefig("temperature_histogram.png")  # Save the histogram as an image file

    def print_temp_stats(self, temp_list: list) -> None:
        """Outputs temperature statistics
            
            Args:
                temp_list: temperatures that were in the raw data
            
            Returns:
                None

            Examples:
                >>> print_temp_stats(temp_list)
            """
        ave_temp = sum(temp_list) / len(temp_list)
        low_temp = min(temp_list)
        high_temp = max(temp_list)

        print(f"The average temperature was: {round(ave_temp, 1)}°F")
        print(f"The lowest temperature was: {round(low_temp, 1)}°F")
        print(f"The highest temperature was: {round(high_temp, 1)}°F")

    def print_humidity_stats(self, humidity_list: list) -> None:
        """Outputs humidity statistics
            
            Args:
                humidity_list: humidity values that were in the raw data
            
            Returns:
                None

            Examples:
                >>> print_humidity_stats(humidity_list)
            """
        ave_humidity = sum(humidity_list) / len(humidity_list)
        low_humidity = min(humidity_list)
        high_humidity = max(humidity_list)

        print(f"The average humidity was: {round(ave_humidity, 1)}%")
        print(f"The lowest humidity was: {round(low_humidity, 1)} %")
        print(f"The highest humidity was: {round(high_humidity, 1)}%")

    def calculate_and_print_statistics(self, temp_list: list, humidity_list: list) -> None:
        """calls print_temp_stats and print_humidity_stats for calculation and printing. Labels these "Weather Statistics"
            
            Args:
                temp_list: temperatures that were in the raw data
                humidity_list: humidity values that were in the raw data
            
            Returns:
                None

            Examples:
                >>> calculate_and_print_statistics(temp_list, humidity_list)
            """

        print() # Blank line before statistics
        print("Weather Statistics")
        # Print temp data
        self.print_temp_stats(temp_list)
        print() #Blank line between temp and humidity
        # Print humidity data
        self.print_humidity_stats(humidity_list)

    def print_student_name(self) -> None:
        """Prints the students name at the beginning of output
            
            Args:
                None
            
            Returns:
                None

            Examples:
                >>> print_student_name()
            """
        name = "Rowland Holden"
        print(name) # Print student name

    def main(self) -> None:
        """Main entry point for the program. I have always felt that the main entry point of the program shouldn't do any real
            work other than calling functions or methods. Sometimes assign variables to pass to calls but that is 
            about it
            
            Args:
                None
            
            Returns:
                None

            Examples:
                >>> main()
            """
        self.print_student_name()
        temp_list, humidity_list, timestamps_for_plots = self.init_weather_data()
        temp_list, humidity_list = self.clean_data(temp_list, humidity_list)
        self.create_plots(temp_list, humidity_list, timestamps_for_plots)
        self.calculate_and_print_statistics(temp_list, humidity_list)
    
    def __init__(self):
        """called automatically when class is instanced. 
            
            Args:
                None
            
            Returns:
                None

            Examples:
                >>> weather_app = HoldenRowlandFinalCeis101NoaaWeather()
            """
        pass


# ********************* SCRIPT

if __name__ == "__main__":
    noaa_weather = RowlandNoaaWeather()
    noaa_weather.main()
