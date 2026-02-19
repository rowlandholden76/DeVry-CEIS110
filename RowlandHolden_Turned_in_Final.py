# Name: Rowland Holden
# Date: 6/10/2024
# Purpose: Final Project - Gather weather data and create a plot

from noaa_sdk import noaa
import matplotlib.pyplot as plt
import datetime

name = "Rowland Holden"
print(name)

today = datetime.datetime.now()
past = today - datetime.timedelta(days=10)
startDate = past.strftime("%Y-%m-%d")
endDate = today.strftime("%Y-%m-%d")

# get noaa data from their API
n = noaa.NOAA()
observations = n.get_observations("98204", "US", start=startDate, end=endDate)

# create two lists to store temperature and humidity values
temp = []
humidity = []

for obs in observations:
    temp.append(obs["temperature"]["value"])
    humidity.append(obs["relativeHumidity"]["value"])

    print(obs["timestamp"], "\t",
          obs["temperature"]["value"], "\t", 
          obs["relativeHumidity"]["value"], "\t",
          obs["textDescription"])

# print temperature vs humidity
temp = list(filter(None, temp))
humidity = list(filter(None, humidity))

plt.figure()
plt.plot(temp, label="Temperature")
plt.plot(humidity, label="Humidity")
plt.legend()
plt.suptitle("Temperature vs Humidity")
plt.savefig("weather.png")

# create a box plot
plt.figure()
box_data = [temp, humidity]
plt.boxplot(box_data, labels=["temperature", "Humidity"])
plt.suptitle("Box Plot")
plt.savefig("boxplot.png")

# print statistics of weather data
avg_temp = sum(temp) / len(temp)
low_temp = min(temp)
high_temp = max(temp)
print("Weather Statistics")
print("The average temperature was:", round(avg_temp,1))
print("The lowest temperature was:", low_temp)
print("The highest temperature was:", high_temp)

