import numpy as np

def init():

    #Parameters for sampling, receiving and transmitting
    global output_freq,ramp_time,rx_gain, fs, center_freq, default_chirp_bw, num_chirps, BW
    fs=2e6                  #sampling rate
    num_chirps = 256
    num_steps = 1000
    output_freq = 10e9
    center_freq = 2.1e9     #Intermediate frequency after downconverting for receive and before upconverting for transmit
    default_chirp_bw = 500e6
    BW = default_chirp_bw
    ramp_time = 500         # 500 microseconds
    rx_gain = 30
    
    #Parameters for fft plotting
    global N_frame,signal_freq,plot_freq,freq,fft_size
    fft_size = 1024*8
    N_frame = fft_size
    signal_freq = 100e3     #Frequency of what we send out
    plot_freq = 100e3
    freq = np.linspace(-fs / 2, fs / 2, int(N_frame))

    global max_range,max_scale,min_scale
    #Parameters for 2D FFT Plotting]
    max_range = 100
    min_scale = 0
    max_scale = 100
    
    #Parameters for Waterfall Plot
    global num_slices
    num_slices = 100        #Water fall plot stuff

