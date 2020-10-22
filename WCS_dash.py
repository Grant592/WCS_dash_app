#!/usr/bin/env python

import os
import csv
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import base64
import io

def move_files(list_of_files):
    """Move completed files to different directory.
    Make new directory if one doesn't exist"""
    path = os.getcwd()
    if not os.path.exists('completed_files'):
        os.makedirs('completed_files')
        for file in list_of_files:
            os.rename(file, path + str('/completed_files/') + file)
    else:
        for file in list_of_files:
            os.rename(file, path + str('/completed_files/') + file)

def file_importer(path):
    """import a list of files containing GPS export"""
    file_list = [f for f in os.listdir(path)
                 if f.endswith('.csv') if not f.startswith('.')]
    return file_list


class RollingAverage():

    def __init__(self, file_path, periods=[60,240,30]):
        self.results = {}
        self.file = file_path
        self.time_periods = periods
        self.df = None
        self.periods = None

    def calculate_periods(self):
        """Define time periods to be used for rolling analysis.
       (lowest number, highest number, interval) """
        self.periods = [x*10 for x in range(self.time_periods[0], (self.time_periods[1]+1), self.time_periods[2])]

    def extract_name(self):
        """Extract name from GPS export and add to results_dict"""
        stream = io.BytesIO(self.file)
        file_lines = stream.readlines()
        name_string = [str(x, 'utf-8') for x in file_lines[:10]]
        name_string = name_string[7].split('"')
        name = name_string[1]
        self.name = name
        self.results[name] = {}
        self.results[name]['M/min'] = {}
        self.results[name]['HSR/min'] = {}
        self.results[name]['Accel/min'] = {}

    def create_df(self):
        """Create data frame from file"""
        self.df = pd.read_csv(io.StringIO(self.file.decode('utf-8')), skiprows = 8)
        self.df['Timestamp'] = pd.to_datetime(self.df['Timestamp'], dayfirst=True)
        self.df['difference'] = self.df['Odometer'].diff()

        return self.df

    def clean_data(self):
        """Clean up data by removing Odometer data where
        HDOP is greater than 1.5 and #Sats is less than 6"""
        self.df['Odometer'][self.df['HDOP'] > 2.0] = np.nan
        self.df['Odometer'][self.df['#Sats'] <= 6] = np.nan
        self.df['Odometer'][self.df['Velocity'] > 10] = np.nan
        self.df['Odometer'].interpolate(inplace=True)


    def calculate_variables(self):
        """Create masks that filter Odometer where Velocity > 5
        and separate mask where accel > 2"""
        hsr_mask = self.df['Velocity'] >= 5
        accel_mask = self.df['Acceleration'] >= 2
        self.df['diff>5'] = self.df['difference'].where(hsr_mask, 0)
        self.df['diff_accel>2'] = self.df['difference'].where(accel_mask, 0)


    def calculate_results(self):
        for period in self.periods:
            self.results[self.name]['M/min'][period/10] = np.round((self.df['difference'].rolling(period).sum()/(period/10/60)).max(),2)
            self.results[self.name]['HSR/min'][period/10] = np.round((self.df['diff>5'].rolling(period).sum()/(period/10/60)).max(), 2)
            self.results[self.name]['Accel/min'][period/10] = np.round((self.df['diff_accel>2'].rolling(period).sum()/(period/10/60)).max(), 2)

    def plot_heatmap(self):
        for period in self.periods:
            self.df[f'rolling_{int(period/10)}_sum'] = self.df['difference'].rolling(period).sum()/(period/10/60)
            self.df[f'rolling_{int(period/10)}_HSR_sum'] = self.df['diff>5'].rolling(period).sum()/(period/10/60)
            self.df[f'rolling_{int(period/10)}_accel_sum'] = self.df['diff_accel>2'].rolling(period).sum()/(period/10/60)
        heat_map_df = self.df.dropna()
        fig = make_subplots(rows=3, cols=1)

        fig.add_trace(
            go.Heatmap(
                x = heat_map_df['Timestamp'],
                y = heat_map_df.iloc[:,15::3].columns,
                z = heat_map_df.iloc[:,15::3].values.T,
                colorbar = dict(len=0.25, y=.85)
            ), row=1, col=1
        )


        fig.add_trace(
            go.Heatmap(
                x = heat_map_df['Timestamp'],
                y = heat_map_df.iloc[:,16::3].columns,
                z = heat_map_df.iloc[:,16::3].values.T,
                colorbar = dict(len=0.25, y=.50)
            ), row=2, col=1
        )

        fig.add_trace(
            go.Heatmap(
                x = heat_map_df['Timestamp'],
                y = heat_map_df.iloc[:,17::3].columns,
                z = heat_map_df.iloc[:,17::3].values.T,
                colorbar = dict(len=0.25, y=.15)
            ), row=3, col=1
        )
        
        fig.update_layout(title_text=self.name)

        return fig



    def apply_all_calculations(self):
        self.calculate_periods()
        self.extract_name()
        self.create_df()
        self.clean_data()
        self.calculate_variables()
        self.calculate_results()

def main():
    path = input("Enter the path to raw GPS csv exports:  ")
    files = file_importer(path)
    #files = file_importer(os.getcwd())

    master_results = []

    for file in files:
        rolling_calulator = RollingAverage(file)
        rolling_calulator.apply_all_calculations()
        interim = {k: pd.DataFrame(v) for k,v in rolling_calulator.results.items()}
        results_df = pd.concat(interim, axis=1)
        master_results.append(results_df)
  #      rolling_calulator.plot_heatmap()


    output = pd.concat(master_results,axis=1).T
    output.to_csv('rolling_averages.csv')
    move_files(files)

if __name__ == '__main__':
    main()
