import adi
from dotenv import load_dotenv
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from matplotlib import cm
from numpy import arange, cos, log10, pi, sin
from numpy.fft import fft, fft2, fftshift, ifft2, ifftshift
from PyQt6.QtCore import Qt
from PyQt6.QtSvg import QSvgWidget
from PyQt6.QtWidgets import *
from pyqtgraph.Qt import QtCore, QtGui
from scipy import interpolate, signal

#Environment variables
load_dotenv()


#Get IP addresses
try:
    rpi_ip = os.getenv("rpi_ip")
    sdr_ip = os.getenv('sdr_ip')
except:
    print("Env File not Found")
    rpi_ip = "ip:phaser.local"
    sdr_ip = "ip:192.168.2.1"

#Instantiate SDR (Pluto)
try:
    check_sdr = my_sdr.uri
    print("Already connected to Pluto")
except NameError:
    my_sdr = adi.ad9361(uri=sdr_ip)

#Instantiate Phaser Board (CN0566)
try:
    check_phaser = my_phaser.uri
    print("cn0566 already connected")
except NameError:
    my_phaser = adi.CN0566(uri=rpi_ip, rx_dev=my_sdr)

#Initialize the two ADAR1000 beamformers
my_phaser.configure(device_mode="rx")
my_phaser.load_gain_cal()
my_phaser.load_phase_cal()

for i in range(0, 8):
    my_phaser.set_chan_phase(i, 0)  #set all phase to 0

gain_list = [8, 34, 84, 127, 127, 84, 34, 8]  # Blackman taper
for i in range(0, len(gain_list)):
    my_phaser.set_chan_gain(i, gain_list[i], apply_cal=True) 

#receive and transmit variables
my_sdr.rx_lo = 2.2e9 #offset for the mixed down intermediate frequency, the RF is at 10 GHz
my_sdr.tx_lo = 2.2e9 #Generate output frequency at 2.2 GHz, Phaser will mix
sample_rate = 0.6e6
center_freq = 2.1e9
signal_freq = 100e3
num_slices = 200
fft_size = 1024 * 16
img_array = np.zeros((num_slices, fft_size))

#configure my_sdr.rx_lo = int(center_freq)  # set this to output_freq - (the freq of the HB100)
my_sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
my_sdr.rx_buffer_size = int(fft_size)
my_sdr.gain_control_mode_chan0 = "manual"  # manual or slow_attack
my_sdr.gain_control_mode_chan1 = "manual"  # manual or slow_attack
my_sdr.rx_hardwaregain_chan0 = int(30)  # must be between -3 and 70
my_sdr.rx_hardwaregain_chan1 = int(30)  # must be between -3 and 70
# Configure Tx
my_sdr.tx_lo = int(center_freq)
my_sdr.tx_enabled_channels = [0, 1]
my_sdr.tx_cyclic_buffer = True  # must set cyclic buffer to true for the tdd burst mode.  Otherwise Tx will turn on and off randomly
my_sdr.tx_hardwaregain_chan0 = -88  # must be between 0 and -88
my_sdr.tx_hardwaregain_chan1 = -0  # must be between 0 and -88rx

# Configure the ADF4159 Rampling PLL
output_freq = 12.1e9
BW = 500e6
num_steps = 1000
ramp_time = 1e3  # us
ramp_time_s = ramp_time / 1e6
my_phaser.frequency = int(output_freq / 4)  # Output frequency divided by 4
my_phaser.freq_dev_range = int(
    BW / 4
)  # frequency deviation range in Hz.  This is the total freq deviation of the complete freq ramp
my_phaser.freq_dev_step = int(
    BW / num_steps
)  # frequency deviation step in Hz.  This is fDEV, in Hz.  Can be positive or negative
my_phaser.freq_dev_time = int(
    ramp_time
)  # total time (in us) of the complete frequency ramp
my_phaser.delay_word = 4095  # 12 bit delay word.  4095*PFD = 40.95 us.  For sawtooth ramps, this is also the length of the Ramp_complete signal
my_phaser.delay_clk = "PFD"  # can be 'PFD' or 'PFD*CLK1'
my_phaser.delay_start_en = 0  # delay start
my_phaser.ramp_delay_en = 0  # delay between ramps.
my_phaser.trig_delay_en = 0  # triangle delay
my_phaser.ramp_mode = "continuous_triangular"  # ramp_mode can be:  "disabled", "continuous_sawtooth", "continuous_triangular", "single_sawtooth_burst", "single_ramp_burst"
my_phaser.sing_ful_tri = (
    0  # full triangle enable/disable -- this is used with the single_ramp_burst mode
)
my_phaser.tx_trig_en = 0  # start a ramp with TXdata
my_phaser.enable = 0  # 0 = PLL enable.  Write this last to update all the registers



#beamsteering variables
theta = 0 #0 degrees from boresight, desired steering angle
d = my_phaser.element_spacing #0.14 meters between each antenna element
f = 10.3e9 #frequency
phase_shift = 2 * np.pi * f * d * np.sin(theta) / my_phaser.c #phase shift from one element to next

def update():
    data = my_sdr.rx()
    print("Raw RX data: "+data)
    data = data[0]+data[1] #sums the signals from the two ADAR1000s
    print("Summed RX data: "+ data)



timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

# start the app
sys.exit(App.exec())