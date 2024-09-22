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
        
    def makePath(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
    
    def write(self, data, path, filename):
        self.makePath(path)
        data.to_csv(f'{path}/{filename}', index=False)
    
    def readHistoricData(self, date, path = "./historic_data"):
        return pd.read_csv(f"{path}/{date.strftime('%Y-%m-%d')}.csv")

    def writeHistoricData(self, data, date, path = "./historic_data"):
        self.makePath(path)
        data.to_csv(f"{path}/{date.strftime('%Y-%m-%d')}.csv", index=False)

    def readTrafficData(self, date, path = "./traffic_data"):
        return pd.read_csv(f"{path}/{date.strftime('%Y-%m-%d')}.csv")

    def writeTrafficData(self, data, date, path = "./traffic_data"):
        self.makePath(path)
        data.to_csv(f"{path}/{date.strftime('%Y-%m-%d')}.csv", index=False)
    
    def readSlottedTrafficData(self, date, path = "./slotted_traffic_data"):
        return pd.read_csv(f"{path}/{date.strftime('%Y-%m-%d')}.csv")
    
    def writeSlottedTrafficData(self, data, date, path = "./slotted_traffic_data"):
        self.makePath(path)
        data.to_csv(f"{path}/{date.strftime('%Y-%m-%d')}.csv", index=False)
    
    def readCentroids(self):
        return pd.read_csv("centroids.csv")

    def readAllSlotted(self, path = "./slotted_traffic_data"):
        # Define the directory containing the CSV files
        # List to hold the DataFrames
        dfs = pd.DataFrame()

        # Loop through all files in the directory
        for filename in os.listdir(path):
            if filename.endswith(".csv"):  # Check for CSV files
                file_path = os.path.join(path, filename)
                df = pd.read_csv(file_path)  # Read each CSV file into a DataFrame
                dfs = pd.concat([dfs, df], ignore_index=True)

        # Concatenate all DataFrames in the list into a single DataF
        return dfs