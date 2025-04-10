import numpy as np

def init():
    global fs,N_frame,signal_freq,plot_freq,freq,fft_size
    fs=2e6
    fft_size = 1024*8
    N_frame = fft_size
    signal_freq = 100e3     #Frequency of what we send out
    plot_freq = 100e3
    freq = np.linspace(-fs / 2, fs / 2, int(N_frame))