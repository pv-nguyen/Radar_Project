import numpy as np

def init():

    #Parameters for sampling, receiving and transmitting
    global output_freq,ramp_time,rx_gain, fs, center_freq, default_chirp_bw, num_chirps, BW, num_steps
    fs=4e6                  #sampling rate
    num_chirps = 1#256
    output_freq = 10e9
    center_freq = 2e9     #Intermediate frequency after downconverting for receive and before upconverting for transmit
    default_chirp_bw = 500e6
    BW = default_chirp_bw
    ramp_time = 300#500         # 500 microseconds
    num_steps = ramp_time#1000
    rx_gain = 40
    
    #Parameters for fft plotting
    global blackman_taper,power,N_frame,signal_freq,plot_freq,freq,fft_size
    blackman_taper = False
    power = 8
    fft_size = 1024*8
    N_frame = fft_size
    signal_freq = 100e3     #Frequency of what we send out
    plot_freq = 100e3
    freq = np.linspace(-fs / 2, fs / 2, int(N_frame))

    global max_range,max_scale,min_scale,mti_filter, max_vel
    #Parameters for 2D FFT Plotting
    mti_filter = True
    max_range = 5#100
    min_scale = 0
    max_scale = 100
    max_vel = 2
    
    #Parameters for Waterfall Plot
    global num_slices, low_level, high_level,zoom_freq
    num_slices = 100        #Water fall plot stuff
    low_level = -45
    high_level = -5
    zoom_freq = 50e3

    #cfar parameters
    global bias,num_guard_cells,num_ref_cells,show_threshold,apply_cfar
    bias = 11 #db
    num_guard_cells = 5
    num_ref_cells = 15
    show_threshold = True
    apply_cfar = False

