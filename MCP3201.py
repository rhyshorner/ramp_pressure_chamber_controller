# uses the "spidev" package ('sudo pip3 install spidev')
import spidev
import math
from time import sleep

# change these depending on the Sensor min/4mA - max/20mA outputs.
SENSOR_MIN = 0 # sensor reads 0 MPa at 4mA
SENSOR_MAX = 25 # sensor reads 25 MPa at 20mA

RECEIVER_4mA = 0.3992
RECEIVER_20mA=1.996

class MCP3201(object):
    """
    Functions for reading the MCP3201 12-bit A/D converter using the SPI bus either in MSB- or LSB-mode
    """
    def __init__(self, SPI_BUS, CE_PIN):
        """
        initializes the device, takes SPI bus address (which is always 0 on newer Raspberry models)
        and sets the channel to either CE0 = 0 (GPIO pin BCM 8) or CE1 = 1 (GPIO pin BCM 7)
        """
        if SPI_BUS not in [0, 1]:
            raise ValueError('wrong SPI-bus: {0} setting (use 0 or 1)!'.format(SPI_BUS))
        if CE_PIN not in [0, 1]:
            raise ValueError('wrong CE-setting: {0} setting (use 0 for CE0 or 1 for CE1)!'.format(CE_PIN))
        self._spi = spidev.SpiDev()
        self._spi.open(SPI_BUS, CE_PIN)
        self._spi.max_speed_hz = 976000
        self.SENSOR_MIN = SENSOR_MIN
        self.SENSOR_MAX = SENSOR_MAX
        self.RECEIVER_4mA = RECEIVER_4mA
        self.RECEIVER_20mA = RECEIVER_20mA
        self.pressure_ave = 0

    def readADC_MSB(self):
        """
        Reads 2 bytes (byte_0 and byte_1) and converts the output code from the MSB-mode:
        byte_0 holds two ?? bits, the null bit, and the 5 MSB bits (B11-B07),
        byte_1 holds the remaning 7 MBS bits (B06-B00) and B01 from the LSB-mode, which has to be removed.
        """
        bytes_received = self._spi.xfer2([0x00, 0x00])

        MSB_1 = bytes_received[1]
        MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode

        MSB_0 = bytes_received[0] & 0b00011111  # mask the 2 unknown bits and the null bit
        MSB_0 = MSB_0 << 7  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)

        return MSB_0 + MSB_1


    def readADC_LSB(self):
        """
        Reads 4 bytes (byte_0 - byte_3) and converts the output code from LSB format mode:
        byte 1 holds B00 (shared by MSB- and LSB-modes) and B01,
        byte_2 holds the next 8 LSB bits (B03-B09), and
        byte 3, holds the remaining 2 LSB bits (B10-B11).
        """
        bytes_received = self._spi.xfer2([0x00, 0x00, 0x00, 0x00])

        LSB_0 = bytes_received[1] & 0b00000011  # mask the first 6 bits from the MSB mode
        LSB_0 = bin(LSB_0)[2:].zfill(2)  # converts to binary, cuts the "0b", include leading 0s

        LSB_1 = bytes_received[2]
        LSB_1 = bin(LSB_1)[2:].zfill(8)  # see above, include leading 0s (8 digits!)

        LSB_2 = bytes_received[3]
        LSB_2 = bin(LSB_2)[2:].zfill(8)
        LSB_2 = LSB_2[0:2]  # keep the first two digits

        LSB = LSB_0 + LSB_1 + LSB_2  # concatenate the three parts to the 12-digits string
        LSB = LSB[::-1]  # invert the resulting string
        return int(LSB, base=2)
    
    def filtered_pressure(self):
        self.pressure_ave = round(((self.pressure_ave * 99) + self.scaled_value_to_sensor()) / 100,3)
        # calibration factor
        #pressure_ave = pressure_ave # * calibration factor
        # y = -0.0102x^3 + 0.1286x^2 + 0.4544x + 0.8078, as an example
        return self.pressure_ave


    def convert_to_voltage(self, adc_output, VREF=2.048):
        """
        Calculates analogue voltage from the digital output code (ranging from 0-4095)
        VREF could be adjusted here (standard uses the 3V3 rail from the Rpi)
        """
        return adc_output * (VREF / (2 ** 12 - 1))

    def measured_voltage(self):
        adc_output = self.readADC_MSB()
        adc_voltage = self.convert_to_voltage(adc_output)
#        print("adc_voltage: " + str(adc_voltage))
        return adc_voltage
 
    def scaled_value_to_sensor(self):
        sensor_voltage = self.measured_voltage()
        if sensor_voltage < self.RECEIVER_4mA:
            sensor_voltage = self.RECEIVER_4mA
        elif sensor_voltage > self.RECEIVER_20mA:
            sensor_voltage = self.RECEIVER_20mA
        else:
            sensor_voltage = sensor_voltage
        scaled_value = round(self.SENSOR_MIN+(sensor_voltage-self.RECEIVER_4mA)*(self.SENSOR_MAX-self.SENSOR_MIN)/(self.RECEIVER_20mA-self.RECEIVER_4mA),3)
        return scaled_value


if __name__ == '__main__':
    SPI_bus = 0
    CE = 0
    MCP3201 = MCP3201(SPI_bus, CE)
    
    try:
        while True:
            ADC_output_code = MCP3201.readADC_MSB()
            ADC_voltage = MCP3201.convert_to_voltage(ADC_output_code)
            print("MCP3201 output code (MSB-mode): %d" % ADC_output_code)
            print("MCP3201 voltage: %0.2f V" % ADC_voltage)
            
            sleep(0.1)  # wait minimum of 100 ms between ADC measurements
            
            ADC_output_code = MCP3201.readADC_LSB()
            ADC_voltage = MCP3201.convert_to_voltage(ADC_output_code)
            print("MCP3201 output code (LSB-mode): %d" % ADC_output_code)
            print("MCP3201 voltage: %0.2f V" % ADC_voltage)
            print()
            
            sleep(1)

    except (KeyboardInterrupt):
        print('\n', "Exit on Ctrl-C: Good bye!")

    except:
        print("Other error or exception occurred!")
        raise

    finally:
        print()
