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

    # Get route summary for a specific date, from 00:00 to 23:59 with a step of 30 minutes
    def getHistoricData(self, start, end, date):
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