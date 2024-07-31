import time
import pandas as pd
import datetime
import math
from dateutil import parser as dtparser
from IPython.display import clear_output

class Processor:
    def __init__(self, tomtom_api_client):
        self.ttapi = tomtom_api_client

    def readHistoricData(self, date):
        return pd.read_csv(f"historic_data/{date.strftime('%Y-%m-%d')}.csv")

    def writeHistoricData(self, data, date):
        data.to_csv(f"historic_data/{date.strftime('%Y-%m-%d')}.csv", index=False)

    def readTrafficData(self, date):
        return pd.read_csv(f"traffic_data/{date.strftime('%Y-%m-%d')}.csv")

    def writeTrafficData(self, data, date):
        data.to_csv(f"traffic_data/{date.strftime('%Y-%m-%d')}.csv", index=False)
    
    def readSlottedTrafficData(self, date):
        return pd.read_csv(f"slotted_traffic_data/{date.strftime('%Y-%m-%d')}.csv")
    
    def writeSlottedTrafficData(self, data, date):
        data.to_csv(f"slotted_traffic_data/{date.strftime('%Y-%m-%d')}.csv", index=False)
    
    def readCentroids(self):
        return pd.read_csv("centroids.csv")

    # Get route summary for a specific date, from 00:00 to 23:59 with a step of 30 minutes
    def getHistoricData(self, start, end, date):
        
        hour_range = range(0, 48)
        
        route_summaries = pd.DataFrame()
        for i in hour_range:

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
                
            clear_output(wait=True)
            print(f"Retrieving data: { round((i+1) / len(hour_range) * 100) }% >> {departure_time}")
            time.sleep(0.3)
        
        route_summaries.drop(['trafficDelayInSeconds', 'trafficLengthInMeters', 'arrivalTime'], axis=1, inplace=True)
        return route_summaries

    # Calculate traffic data based on route summaries
    def calculateTrafficData(self, historic_data):
        
        route_analysis_df = pd.DataFrame()

        for index, summary in historic_data.iterrows():
            # Departure time
            datetime = summary['departureTime']
            
            clear_output(wait=True)
            print(f"Computing traffic: { round((index+1) / len(historic_data) * 100) }% >> {datetime}")
            
            # Get length of road
            length_in_meters = summary['lengthInMeters']
            # Calculate free flow speed in km/h
            free_flow_speed = length_in_meters / summary['noTrafficTravelTimeInSeconds']  * 3.6
            # Calculate traffic speed in km/h
            traffic_speed = length_in_meters / summary['travelTimeInSeconds']  * 3.6
            # Calculate traffic density
            density_factor = free_flow_speed / traffic_speed
            avg_vehicle_length = 4.6
            
            # https://www.amsi.org.au/teacher_modules/pdfs/Maths_delivers/Braking5.pdf
            breaking_distance = (traffic_speed ** 2) / 20 # b = m/s 
            
            # The number of vehicles is calculated as the traffic density * length of road divided by the average length of vehicles and recommended breaking distance
            vehicles = round(density_factor * length_in_meters / avg_vehicle_length)
            
            results = {"datetime": datetime, "free_flow_speed": free_flow_speed, "traffic_speed": traffic_speed, "density_factor": density_factor, "number_of_vehicles": vehicles, "points": summary['points']}
            
            # Convert to data frame and append
            route_analysis_df = pd.concat([route_analysis_df, pd.json_normalize(results)], ignore_index=True)

        return route_analysis_df

    # Calculate cumulated traffic data based on slots, for example ["00:00-06:00", "06:00-12:00", "12:00-18:00", "18:00-23:00"]
    def calculateSlottedTraffic(self, traffic_data, slots):
        traffic_data['datetime'] = pd.to_datetime(traffic_data['datetime'])
        
        # transform each slot into a time range
        time_ranges = []
        for slot in slots:
            start_time, end_time = slot.split("-")
            start_time = dtparser.parse(start_time).time()
            end_time = dtparser.parse(end_time).time()
            time_ranges.append((start_time, end_time))
        
        slot_traffic_df = pd.DataFrame()
        for slot in time_ranges:
            # Filter data based on slot
            slot_data = traffic_data[(traffic_data['datetime'].dt.time >= slot[0]) & (traffic_data['datetime'].dt.time < slot[1])]
            # Calculate average traffic speed, density and number of vehicles
            avg_traffic_speed = slot_data['traffic_speed'].mean()
            avg_density_factor = slot_data['density_factor'].mean()
            avg_number_of_vehicles = slot_data['number_of_vehicles'].mean()
            points = slot_data['points'].iat[0]
            # Append to DataFrame
            slot_traffic_df = pd.concat([slot_traffic_df, pd.DataFrame({"slot": f"{slot[0]}-{slot[1]}", "avg_traffic_speed": avg_traffic_speed, "avg_density_factor": avg_density_factor, "avg_number_of_vehicles": avg_number_of_vehicles, "points": points }, index=[0])], ignore_index=True)
        
        return slot_traffic_df