#!/usr/bin/python

import sys
import time
import struct
import numpy as np
import pandas as pd
import csv

# Add '/Lib' or '/Lib64' to path
if (8 * struct.calcsize("P")) == 32:
    print("Use x86 libraries.")
    from Lib.asdk import DM
else:
    print("Use x86_64 libraries.")
    from Lib64.asdk import DM

file_path = r"C:\Users\SPL\Desktop\alpao_usb\Python3\ZernikeMags.csv"
zernike_data = pd.read_csv(file_path, header=None)

def convert_to_percentages(zernike_data):
    ranges = zernike_data.iloc[1, :].str.extract(r'\[(-?\d+),(-?\d+)\]')
    ranges.columns = ['min', 'max']
    ranges = ranges.astype(float)
    values = zernike_data.iloc[2:, :].astype(float).values
    max_vals = ranges['max'].values
    percentages = (values / max_vals)
    return percentages

def main(args):
    print("Please enter the S/N within the following format BXXYYY (see DM backside): ")
    serialName = input().strip()
    print("Connect the mirror")
    dm = DM(serialName)
    print("Retrieve number of actuators")
    nbAct = int(dm.Get('NBOfActuator'))
    print(f"Number of actuators for {serialName}: {nbAct}")
    print("Send 0 on each actuator")
    values = [0.] * nbAct
    dm.Send(values)

    zernike_percentages = convert_to_percentages(zernike_data)
    Z2C = []
    try:
        with open('./config/' + serialName + '-Z2C.csv', newline='') as csvfile:
            csvrows = csv.reader(csvfile, delimiter=' ')
            for row in csvrows:
                x = row[0].split(",")
                Z2C.append([float(value) for value in x])
    except FileNotFoundError:
        print("File Error", "Configuration file not found")
    Z2C = np.array(Z2C)

    counter = 0
    counter_max = 5 #maximum of iterations to go through
    while counter < counter_max:
        for i in range(counter_max):
            zernike_values = Z2C[:len(zernike_percentages[i])].T @ zernike_percentages[i]

            if (np.max(zernike_values)>1) or (np.min(zernike_values) < -1):
                zernike_values = (zernike_values - zernike_values.min()) / (zernike_values.max() - zernike_values.min())  #scales to [0,1]
                zernike_values = 2 * zernike_values - 1  #scales to [-1,1]
            
            dm.Send(zernike_values)
            time.sleep(5) #can go to around 0.005 seconds
            counter += 1
            if counter > counter_max:
                break
    print("Send 0 on all actuators")
    dm.Reset()

if __name__ == "__main__":
    main(sys.argv)