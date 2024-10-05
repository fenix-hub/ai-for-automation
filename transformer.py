import time
import pandas as pd
import datetime
import math
from dateutil import parser as dtparser
from IPython.display import display, clear_output
import os

class Transformer:
    
    def __init__(self):
        pass

    # Calculate traffic data based on route summaries
    def calculateTrafficData(self, historic_data):
        route_analysis_df = pd.DataFrame()
        
        for index, summary in historic_data.iterrows():
            clear_output(wait=True)
            
            # Departure time
            datetime = summary['departureTime']
            
            # Get length of road
            length_in_meters = summary['lengthInMeters']
            # Calculate free flow speed in km/h

            if summary['noTrafficTravelTimeInSeconds'] != 0:
             free_flow_speed = length_in_meters / summary['noTrafficTravelTimeInSeconds'] * 3.6
            else:
             free_flow_speed = float('inf')

            # Calculate traffic speed in km/h
            if summary['travelTimeInSeconds'] != 0:
               traffic_speed = length_in_meters / summary['travelTimeInSeconds'] * 3.6
            else:
             traffic_speed = 0  # O un altro valore di fallback (ad esempio, una velocità predefinita)

            # Calculate traffic density
            #density_factor = free_flow_speed / traffic_speed
            if traffic_speed != 0:
             density_factor = free_flow_speed / traffic_speed
            else:
             density_factor = 0  # O un valore di fallback appropriato

            avg_vehicle_length = 4.6
            
            # https://www.amsi.org.au/teacher_modules/pdfs/Maths_delivers/Braking5.pdf
            breaking_distance = (traffic_speed ** 2) / 20 # b = m/s 
            
            # The number of vehicles is calculated as the traffic density * length of road divided by the average length of vehicles and recommended breaking distance
            vehicles = round(density_factor * length_in_meters / avg_vehicle_length)
            
            results = {"datetime": datetime, "free_flow_speed": free_flow_speed, "traffic_speed": traffic_speed, "density_factor": density_factor, "number_of_vehicles": vehicles, "points": summary['points']}
            
            # Convert to data frame and append
            route_analysis_df = pd.concat([route_analysis_df, pd.json_normalize(results)], ignore_index=True)
            print(f"Computing traffic: { round((index+1) / len(historic_data) * 100) }% >> {datetime}")
        
        return route_analysis_df



    # this function accepts arrays like ["00:00-06:00", "06:00-12:00", "12:00-18:00", "18:00-23:00"]
    def parseTimeSlot(self, slot):
        start_time, end_time = slot.split("-")
        return (dtparser.parse(start_time).time(), dtparser.parse(end_time).time())

    # Calculate cumulated traffic data based on slots, for example ["00:00-06:00", "06:00-12:00", "12:00-18:00", "18:00-23:00"]
    def calculateSlottedTraffic(self, traffic_data, slots):
        traffic_data['datetime'] = pd.to_datetime(traffic_data['datetime'])
        
        # transform each slot into a time range
        time_ranges = []
        for slot in slots:
            time_ranges.append(self.parseTimeSlot(slot))
        
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
    
    def _aggregateSlottedTrafficBySlot(self, slot_traffic_data, slot):
        time_slot = self.parseTimeSlot(slot)
        slot_data = slot_traffic_data[(slot_traffic_data['slot'].str.contains(time_slot[0].strftime('%H:%M')))]
        avg_traffic_speed = slot_data['avg_traffic_speed'].mean()
        avg_density_factor = slot_data['avg_density_factor'].mean()
        avg_number_of_vehicles = slot_data['avg_number_of_vehicles'].mean()
        points = slot_data['points'].iat[0]
        return pd.DataFrame({"slot": str(slot), "avg_traffic_speed": avg_traffic_speed, "avg_density_factor": avg_density_factor, "avg_number_of_vehicles": avg_number_of_vehicles, "points": points}, index=[0])
    
    def getAggregatedTrafficData(self, slot_traffic_data, slots):
        aggregated_data = pd.DataFrame()
        for slot in slots:
            agg = self._aggregateSlottedTrafficBySlot(slot_traffic_data, slot)
            aggregated_data = pd.concat([aggregated_data, agg], ignore_index=True)
        return aggregated_data