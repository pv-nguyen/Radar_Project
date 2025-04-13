import matplotlib.pyplot as plt
import numpy as np
from PyQt6.QtWidgets import QApplication
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
from matplotlib import cm
from numpy import arange, cos, log10, pi, sin
from numpy.fft import fft, fft2, fftshift, ifft2, ifftshift
import sys
import params
from gui import MainWindow
from PyQt6.QtWidgets import QApplication
from pyqtgraph.Qt import QtCore, QtGui



if __name__ == "__main__":
    params.init()

radar_data = np.load("Pluto/data/FFT2D_256Chirps.npy")
# print(radar_data)

c = 3e8
PRI_ms = params.ramp_time /1e3 + 1.0
wavelength = c / params.output_freq
PRI_s = PRI_ms / 1e3
PRF = 1 / PRI_s
num_bursts = params.num_chirps
max_doppler_freq = PRF / 2
max_doppler_vel = max_doppler_freq * wavelength / 2
ramp_time_s = params.ramp_time / 1e6
slope = params.BW / ramp_time_s
dist = (params.freq - params.signal_freq) * c / (2 * slope)
max_range = params.max_range
max_vel = params.max_vel

rx_bursts_fft = np.fft.fftshift(abs(np.fft.fft2(radar_data)))
rx_bursts_fft = np.log10(rx_bursts_fft).T
rx_bursts_fft = np.clip(rx_bursts_fft,params.min_scale,params.max_scale)

fig,ax = plt.subplots(figsize=(14, 7))
extent = [-max_doppler_vel, max_doppler_vel, dist.min(), dist.max()]
cmaps = ['inferno', 'plasma']
cmn = cmaps[0]
range_doppler = ax.imshow(rx_bursts_fft, aspect='auto',
        extent=extent, origin='lower', cmap=plt.colormaps.get_cmap(cmn),
        )

ax.set_title('Range Doppler Spectrum', fontsize=24)
ax.set_xlabel('Velocity [m/s]', fontsize=22)
ax.set_ylabel('Range [m]', fontsize=22)

ax.set_xlim([-max_vel, max_vel])
ax.set_ylim([0, max_range])
ax.set_yticks(np.arange(0, max_range, max_range/20))
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)

def update_2DFFT(radar_data):
    rx_bursts = radar_data
    if params.mti_filter == True:
        rx_chirps = []
        rx_chirps = rx_bursts
        num_samples = len(rx_chirps[0])
        # create 2 pulse canceller MTI array
        Chirp2P = np.ones([params.num_chirps, num_samples]) * 1j
        for chirp in range(params.num_chirps-1):
            chirpI = rx_chirps[chirp,:]
            chirpI1 = rx_chirps[chirp+1,:]
            chirp_correlation = np.correlate(chirpI, chirpI1, 'valid')
            angle_diff = np.angle(chirp_correlation, deg=False)  # returns radians
            Chirp2P[chirp:] = chirpI1 - chirpI * np.exp(-1j*angle_diff[0])
        rx_bursts = Chirp2P
        
    rx_bursts_fft = np.fft.fftshift(abs(np.fft.fft2(rx_bursts)))
    rx_bursts_fft = np.log10(rx_bursts_fft).T
    rx_bursts_fft = np.clip(rx_bursts_fft,params.min_scale,params.max_scale)
    range_doppler.set_data(rx_bursts_fft)
    plt.show(block=False)
    plt.pause(0.05)


if __name__ == "__main__":
    plt.show()
    # app = QApplication(sys.argv)
    # window = MainWindow()

    # def update():
    #     print("update")
        

    # timer = QtCore.QTimer()
    # timer.timeout.connect(update)
    # timer.start(1000)


    # app.exec()