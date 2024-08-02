import time
import pandas as pd
import datetime
import math
from dateutil import parser as dtparser
from IPython.display import display, clear_output
import os

class CSVHandler:
    
    def __init__(self):
        pass
        
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

    def readAllSlotted(self):
        # Define the directory containing the CSV files
        directory = 'slotted_traffic_data/'

        # List to hold the DataFrames
        dfs = pd.DataFrame()

        # Loop through all files in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".csv"):  # Check for CSV files
                file_path = os.path.join(directory, filename)
                df = pd.read_csv(file_path)  # Read each CSV file into a DataFrame
                dfs = pd.concat([dfs, df], ignore_index=True)

        # Concatenate all DataFrames in the list into a single DataF
        return dfs