## This is incomplete, I was trying to create a simulation of a pressure sensor in operation for testing"

import math
from time import sleep

# change these depending on the Sensor min/4mA - max/20mA outputs.
SENSOR_MIN = 0 # sensor reads 0 MPa at 4mA
SENSOR_MAX = 25 # sensor reads 25 MPa at 20mA


class SIMULATEDMCP3201(object):

    def __init__(self):
        self.SENSOR_MIN = SENSOR_MIN
        self.SENSOR_MAX = SENSOR_MAX
        self.pressure_ave = 0
        pass

    def filtered_pressure(self, pump_amount=0):
        self.pressure_ave = self.pressure_ave + pump_amount
        return self.pressure_ave


if __name__ == '__main__':

    MCP3201 = SIMULATEDMCP3201()
    
    try:
        while True:
            #ADC_output_code = MCP3201.readADC_MSB()
            print("fix this with some reading.")
            sleep(1)

    except (KeyboardInterrupt):
        print('\n', "Exit on Ctrl-C: Good bye!")

    except:
        print("Other error or exception occurred!")
        raise

    finally:
        print()
