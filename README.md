CEIS110 - Intro to programming

There are four files here.  
The first one "Turned-in-Final.py" is the actual class final that was turned in. 
  
The second one "Enhanced-Final.py" is what I turned the class final into. There is a huge difference between the two.  
  
The third "Calculator.py" This is one that I did while taking the class. It wasn't an assignment but I wanted to practice.  
&nbsp;&nbsp;&nbsp;&nbsp;To challenge myself I chose to write a calculator that would take an entire expression and print out the  
&nbsp;&nbsp;&nbsp;&nbsp;step by step process of simplifying it. Ultimately concluding at the simplified answer. What makes this  
&nbsp;&nbsp;&nbsp;&nbsp;unique is the challenge I gave myself. Do this without importing any libraries. That means the parsing,  
&nbsp;&nbsp;&nbsp;&nbsp;input verification had to be all done without the aid of regular expressions. It also means that the math  
&nbsp;&nbsp;&nbsp;&nbsp;had to be done without the aid of the math library. It sounds simple? I thought so to, until one gets  
&nbsp;&nbsp;&nbsp;&nbsp;into just how deep the rabit hole goes with brackets(){}[] that may not match or may be unbalanced,  
&nbsp;&nbsp;&nbsp;&nbsp;Expressions that result in a complex number an in valid character in the expression such as a letter "a,"  
&nbsp;&nbsp;&nbsp;&nbsp;and so on. Most of the code in this, is error checking, validation and parsing.  

The fourth is "weaher_GUI.py" this is the gui created for noaa_weather_backend.py. It displays a forecast of the weather, then prints historical statistics
&nbsp;&nbsp;&nbsp;&nbsp;and generates 3 historal plots for different ways of viewing the data. Finally it prints the raw data for both the forecast data
&nbsp;&nbsp;&nbsp;&nbsp;and the historical data. 

NOTE: For the GUI a very large memory leak was found, 10-15MB for each fetch. After testin and working to find it, it was discovered that the leak was not my code, 
&nbsp;&nbsp;&nbsp;&nbsp;but a native C heap leak. This was discovered using psutil and tracemalloc. Tracemalloc showed that the code that I wrote remained flat, 
&nbsp;&nbsp;&nbsp;&nbsp;only minor growth ~1 mb per 15 fetches. psutil showed 10-15mb of growth per fetch. This proved the lead to be native. 
&nbsp;&nbsp;&nbsp;&nbsp;When isolating the leak to see where it was from, it was found to be when the files were open. Given that the GDI objects remained
&nbsp;&nbsp;&nbsp;&nbsp;flat, it was determined that it was a native C heap leak. In trying to find a workaround I discovered that rendering the plots directly 
&nbsp;&nbsp;&nbsp;&nbsp;in the GUI, instead of opening the saved files, was the best way to work around the leak. Now we see minor memory growth (~1–3 MB/fetch) 
&nbsp;&nbsp;&nbsp;&nbsp;observed after many refreshes due to Tkinter/matplotlib internals — stabilizes after ~10–15 fetches. Disabled opening plots for lower baseline use.
