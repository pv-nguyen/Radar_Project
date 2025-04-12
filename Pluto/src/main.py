import sys
import time
import warnings
from dotenv import load_dotenv
import os

import adi
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from matplotlib import cm
from numpy import arange, cos, log10, pi, sin
from numpy.fft import fft, fft2, fftshift, ifft2, ifftshift
# from PyQt5.QtCore import Qt
# from PyQt5.QtSvg import QSvgWidget
# from PyQt5.QtWidgets import *
from PyQt6.QtWidgets import QApplication
from pyqtgraph.Qt import QtCore, QtGui
from scipy import interpolate, signal

import params
params.init()
from gui import MainWindow
import range_doppler_plot as RD

#Get IP addresses
load_dotenv()
try:
    rpi_ip = os.getenv("rpi_ip")
    sdr_ip = os.getenv('sdr_ip')
except:
    print("Env File not Found")
    rpi_ip = "ip:phaser.local"
    sdr_ip = "ip:192.168.2.1"

#receive and transmit parameters
output_freq = params.output_freq
sample_rate = params.fs     #ADC sample rate of SDR, 600KHz
center_freq = params.center_freq     #Intermediate frequency after downconverting for receive and before upconverting for transmit
signal_freq = params.signal_freq     #Frequency of what we send out
default_chirp_bw = params.default_chirp_bw
ramp_time = params.ramp_time  # 500 microseconds
rx_gain = params.rx_gain
num_slices = params.num_slices        #Water fall plot stuff
fft_size = params.fft_size    #
plot_freq = 100e3   
img_array = np.zeros((num_slices, fft_size))
max_range = 100
min_scale = 0
max_scale = 100
num_chirps = 256

#Instantiate SDR (Pluto) and Phaser objects
my_sdr = adi.ad9361(uri=sdr_ip)
my_phaser = adi.CN0566(uri=rpi_ip, sdr=my_sdr)

#Initialize the two ADAR1000 beamformers
my_phaser.configure(device_mode="rx") #ADAR100s are receive only array
my_phaser.load_gain_cal("Pluto/calibration/gain_cal_val")             #calibration files
my_phaser.load_phase_cal("Pluto/calibration/phase_cal_val")

for i in range(0, 8):
    my_phaser.set_chan_phase(i, 0)  #set all phase to 0

gain_list = [8, 34, 84, 127, 127, 84, 34, 8]  # Blackman taper to reduce sidelobes
for i in range(0, len(gain_list)):
    my_phaser.set_chan_gain(i, gain_list[i], apply_cal=True) 

#Raspberry Pi GPIO
my_phaser._gpios.gpio_tx_sw = 1  # 0 = TX_OUT_2, 1 = TX_OUT_1
my_phaser._gpios.gpio_vctrl_1 = 1 # 1=Use onboard PLL/LO source  (0=disable PLL and VCO, and set switch to use external LO input)
my_phaser._gpios.gpio_vctrl_2 = 1 # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)

#configure SDR rx channels
my_sdr.sample_rate = int(sample_rate)
my_sdr.rx_lo = int(center_freq) #offset for the mixed down intermediate frequency, the RF is at 10 GHz
my_sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
#my_sdr.rx_buffer_size = int(fft_size) 
my_sdr.gain_control_mode_chan0 = "manual"  # manual or slow_attack
my_sdr.gain_control_mode_chan1 = "manual"  # manual or slow_attack
my_sdr.rx_hardwaregain_chan0 = int(rx_gain)  # must be between -3 and 70
my_sdr.rx_hardwaregain_chan1 = int(rx_gain)  # must be between -3 and 70
# Configure Tx
my_sdr.tx_lo = int(center_freq)
my_sdr.tx_enabled_channels = [0, 1]
my_sdr.tx_cyclic_buffer = True  # must set cyclic buffer to true for the tdd burst mode.  Otherwise Tx will turn on and off randomly
my_sdr.tx_hardwaregain_chan0 = -88  # must be between 0 and -88
my_sdr.tx_hardwaregain_chan1 = -0  # must be between 0 and -88rx

# Configure the ADF4159 (Local Oscillator) Rampling PLL, We implement the chirp in the ADF4159 to do stretch processing
vco_freq = int(output_freq + signal_freq + center_freq)
BW = default_chirp_bw
num_steps = 1000
ramp_time_s = ramp_time / 1e6
my_phaser.frequency = int(vco_freq / 4)  # Output frequency divided by 4
my_phaser.freq_dev_range = int( BW / 4 )  # frequency deviation range in Hz.  This is the total freq deviation of the complete freq ramp
my_phaser.freq_dev_step = int( ( BW / 4 ) / num_steps )  # frequency deviation step in Hz.  This is fDEV, in Hz.  Can be positive or negative
my_phaser.freq_dev_time = int( ramp_time )  # total time (in us) of the complete frequency ramp
my_phaser.delay_word = 4095  # 12 bit delay word.  4095*PFD = 40.95 us.  For sawtooth ramps, this is also the length of the Ramp_complete signal
my_phaser.delay_clk = "PFD"  # can be 'PFD' or 'PFD*CLK1'
my_phaser.delay_start_en = 0  # delay start
my_phaser.ramp_delay_en = 0  # delay between ramps.
my_phaser.trig_delay_en = 0  # triangle delay
my_phaser.ramp_mode = "single_sawtooth_burst"  # ramp_mode can be:  "disabled", "continuous_sawtooth", "continuous_triangular", "single_sawtooth_burst", "single_ramp_burst"
my_phaser.sing_ful_tri = ( 0 )  # full triangle enable/disable -- this is used with the single_ramp_burst mode
my_phaser.tx_trig_en = 1 # start a ramp with TXdata, allows chirp synchronization
my_phaser.enable = 0  # 0 = PLL enable.  Write this last to update all the registers

#TDD controller
sdr_pins = adi.one_bit_adc_dac(sdr_ip)
sdr_pins.gpio_tdd_ext_sync = True # If set to True, this enables external capture triggering using the L24N GPIO on the Pluto.  When set to false, an internal trigger pulse will be generated every second
tdd = adi.tddn(sdr_ip)
sdr_pins.gpio_phaser_enable = True
tdd.enable = False         # disable TDD to configure the registers
tdd.sync_external = True
tdd.startup_delay_ms = 0
PRI_ms = ramp_time/1e3 + 1.0
tdd.frame_length_ms = PRI_ms    # each chirp is spaced this far apart
tdd.burst_count = num_chirps       # number of chirps in one continuous receive buffer

tdd.channel[0].enable = True
tdd.channel[0].polarity = False
tdd.channel[0].on_raw = 0
tdd.channel[0].off_raw = 10
tdd.channel[1].enable = True
tdd.channel[1].polarity = False
tdd.channel[1].on_raw = 0
tdd.channel[1].off_raw = 10
tdd.channel[2].enable = True
tdd.channel[2].polarity = False
tdd.channel[2].on_raw = 0
tdd.channel[2].off_raw = 10
tdd.enable = True

# From start of each ramp, how many "good" points do we want?
# For best freq linearity, stay away from the start of the ramps
ramp_time = int(my_phaser.freq_dev_time)
ramp_time_s = ramp_time / 1e6
begin_offset_time = 0.10 * ramp_time_s   # time in seconds
print("actual freq dev time = ", ramp_time)
good_ramp_samples = int((ramp_time_s-begin_offset_time) * sample_rate)
start_offset_time = tdd.channel[0].on_ms/1e3 + begin_offset_time
start_offset_samples = int(start_offset_time * sample_rate)

# size the fft for the number of ramp data points
power=8
fft_size = int(2**power)
num_samples_frame = int(tdd.frame_length_ms/1000*sample_rate)
while num_samples_frame > fft_size:     
    power=power+1
    fft_size = int(2**power) 
    if power==18:
        break
print("fft_size =", fft_size)

# Pluto receive buffer size needs to be greater than total time for all chirps
total_time = tdd.frame_length_ms * num_chirps   # time in ms
print("Total Time for all Chirps:  ", total_time, "ms")
buffer_time = 0
power=12
while total_time > buffer_time:     
    power=power+1
    buffer_size = int(2**power) 
    buffer_time = buffer_size/my_sdr.sample_rate*1000   # buffer time in ms
    if power==23:
        break     # max pluto buffer size is 2**23, but for tdd burst mode, set to 2**22
print("buffer_size:", buffer_size)
my_sdr.rx_buffer_size = buffer_size
print("buffer_time:", buffer_time, " ms")

# # %%
# """ Create a sinewave waveform for Pluto's transmitter
# """
N = int(2**18)
fc = int(signal_freq)
ts = 1 / float(sample_rate)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = 1 * (i + 1j * q)

#ramp parameters
fs = int(my_sdr.sample_rate)
N_frame = fft_size
c = 3e8
slope = BW / ramp_time_s
freq = np.linspace(-fs / 2, fs / 2, int(N_frame))
dist = (freq - signal_freq) * c / (2 * slope)

#doppler spectrum
wavelength = c / output_freq
PRI_s = PRI_ms / 1e3
PRF = 1 / PRI_s
num_bursts = tdd.burst_count
max_doppler_freq = PRF / 2
max_doppler_vel = max_doppler_freq * wavelength / 2

# transmit data from Pluto
my_sdr._ctx.set_timeout(30000)
my_sdr._rx_init_channels()
my_sdr.tx([iq, iq])



def get_data():
    global win_funct

    #Burst signal from the Raspberry PI, hand over handling of synchronizing reading data buffer and chirp to PLUTO Sdr
    my_phaser._gpios.gpio_burst = 0 
    my_phaser._gpios.gpio_burst = 1
    my_phaser._gpios.gpio_burst = 0

    data = my_sdr.rx()
    print("Raw RX data: ")
    print(data)
    sum_data = data[0]+data[1] #sums the signals from the two ADAR1000s
    print("Summed RX data: ")
    print(sum_data)

    # select just the linear portion of the last chirp
    rx_bursts = np.zeros((num_chirps, good_ramp_samples), dtype=complex)
    for burst in range(num_chirps):
        start_index = start_offset_samples + burst*num_samples_frame
        stop_index = start_index + good_ramp_samples
        rx_bursts[burst] = sum_data[start_index:stop_index]
        burst_data = np.ones(fft_size, dtype=complex)*1e-10
        #win_funct = np.blackman(len(rx_bursts[burst]))
        win_funct = np.ones(len(rx_bursts[burst]))
        burst_data[start_offset_samples:(start_offset_samples+good_ramp_samples)] = rx_bursts[burst]*win_funct

    return burst_data, rx_bursts
    # win_funct = np.blackman(len(data))
    # y = data * win_funct
    # sp = np.absolute(np.fft.fft(y))

    # np.save("get_Data_256Chrip.npy",burst_data)

def update_fft(burst_data):
    
    sp = np.absolute(np.fft.fft(burst_data)) #fft
    print("fft data: ")
    print(sp)
    sp = np.fft.fftshift(sp)
    s_mag = np.abs(sp) / np.sum(win_funct)
    s_mag = np.maximum(s_mag, 10 ** (-15))
    s_dbfs = 20 * np.log10(s_mag / (2 ** 11))
    window.fft_curve.setData(freq,s_dbfs)

    
#Create PyQt6 window
app = QApplication(sys.argv)
window = MainWindow()

def update():
    global range_doppler
    print("get data")
    burst_data,rx_bursts=get_data()
    update_fft(burst_data)
    RD.update_2DFFT(rx_bursts)
    print("updated")

#Connect timer signal to call update function
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(10)

app.exec()