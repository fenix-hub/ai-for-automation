import time
import pandas as pd
import datetime
import math
from dateutil import parser as dtparser
from IPython.display import display, clear_output
import os

class Processor:
    def __init__(self, tomtom_api_client):
        self.ttapi = tomtom_api_client
        self.total_requests = 0
        self.MAX_REQUESTS = 2500

    def is_time_in_slot(self, date, slot):
        """
        Check if a given time falls within a specified time slot.

        This function determines whether the time component of a given datetime object
        is within the time range specified by the slot parameter.

        Parameters:
        date (datetime): A datetime object representing the date and time to check.
        slot (str): A string representing a time slot in the format 'HH:MM-HH:MM'.

        Returns:
        bool: True if the time component of 'date' is within the specified slot, False otherwise.
        """
        from datetime import datetime

        # Parse the slot string
        start_time_str, end_time_str = slot.split('-')
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()

        # Get the time part of the date object
        current_time = date.time()

        # Check if the current time is within the slot
        return start_time <= current_time <= end_time


    def getHistoricDataOnInterval(self, start, end, via, date, slots = None, minute_interval=30):
        # Calculate the number of divisions in an hour based on the minute interval
        total_intervals = (24 * 60) // minute_interval
        route_summaries = pd.DataFrame()
        
        """
        # Total intervals equals to the amount of API Calls
        self.total_requests += total_intervals
        print (f"Total calls: {self.total_requests} (API Calls)")
        if self.total_requests > self.MAX_REQUESTS:
            print(f"Total intervals exceed the maximum number of requests allowed: {self.MAX_REQUESTS}")
        """
        
        for i in range(total_intervals):
            clear_output(wait=True)
            # Calculate the number of hours and minutes for each interval
            total_minutes = i * minute_interval
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            # Update the departure time by adding hours and minutes to the initial date
            departure_time = date.replace(hour=date.hour + hours, minute=date.minute + minutes)
            
            # Only get data for the specified slots
            if slots:
                if not any([self.is_time_in_slot(departure_time, slot) for slot in slots]):
                    continue
            
            # Get route summary from the API
            route_summary = self.ttapi.get_route_summary(start, end, via, departure_time)
            
            # Collect data in the DataFrame
            route_summaries = pd.concat([route_summaries, pd.json_normalize(route_summary)], ignore_index=True)
            
            print(f"Retrieved data: { round((i+1) / total_intervals * 100) }% >> {departure_time}")
            time.sleep(0.2)
        
        # Drop unwanted columns
        route_summaries.drop(['trafficDelayInSeconds', 'trafficLengthInMeters', 'arrivalTime'], axis=1, inplace=True)
        return route_summaries

    # Get route summary for a specific date, from 00:00 to 23:59 with a step of 30 minutes
    # TODO: This function is not used in the current implementation, you can remove it if not needed.Time slots are preferred.
    def getHistoricData(self, start, end, date):
        """
        Retrieves historical route data for a specific date, from 00:00 to 23:59 with a 30-minute interval.

        This function iterates over a 24-hour period in 30-minute increments, querying the TomTom API
        for route summaries at each time point. It collects and processes this data into a DataFrame.

        Parameters:
        start (str): The starting point of the route, typically in coordinate format (e.g., "52.50,13.39").
        end (str): The ending point of the route, typically in coordinate format.
        date (datetime): The base date for which to retrieve historical data.

        Returns:
        pd.DataFrame: A DataFrame containing processed route summaries for the specified date and route.
                      The DataFrame excludes 'trafficDelayInSeconds', 'trafficLengthInMeters', and 'arrivalTime' columns.
        """
        hour_range = range(0, 48)
        route_summaries = pd.DataFrame()

        for i in hour_range:
            clear_output(wait=True)
            minute, hour = math.modf(i / 2)
            # Calculate hours and minutes shift
            hours = round(hour)
            minutes = round(minute * 60)

            # Update an hour
            departure_time = date.replace(hour=date.hour + hours, minute=date.minute + minutes)

            # Get summary
            route_summary = self.ttapi.get_route_summary(start, end, departure_time)

            # Collect data in DataFrame
            route_summaries = pd.concat([route_summaries, pd.json_normalize(route_summary)], ignore_index=True)

            print(f"Retrieved data: { round((i+1) / len(hour_range) * 100) }% >> {departure_time}")
            time.sleep(0.2)

        route_summaries.drop(['trafficDelayInSeconds', 'trafficLengthInMeters', 'arrivalTime'], axis=1, inplace=True)
        return route_summaries
