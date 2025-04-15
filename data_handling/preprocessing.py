import pickle
import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg
from numpy.fft import fft, fft2, fftshift, ifft2, ifftshift
import os

waving_file = "data/waving_boresight/wbd.npy"
not_waving_file = "data/standing_boresight/wbs.npy"
waving_config_file = waving_file[:-4]+"_config.pkl"
not_waving_config_file = not_waving_file[:-4]+"_config.pkl"
lower_freq = 100e3
upper_freq = 130e3

with open(waving_config_file,"rb") as f:
    waving_configs = pickle.load(f)
with open(not_waving_config_file,"rb") as f:
    not_waving_configs = pickle.load(f)

def show_fft(freq,s_dbfs):
    print(f"Frequency Length: {len(freq)}\nMagnitude Length: {len(s_dbfs)}")
    plt.plot(freq,s_dbfs)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    ax = plt.gca()
    ax.set_xlim([100e3,200e3])
    plt.show()

def get_fft(frame,config):
    global win_funct
    burst_data, rx_bursts, data = separate_data_chirps(frame,config["num_chirps"],config["good_ramp_samples"],config["start_offset_samples"],config["num_samples_frame"],config["fft_size"])
    fs = config["fs"]
    N_frame = config["fft_size"]
    freq = np.linspace(-fs / 2, fs / 2, int(N_frame))

    sp = np.absolute(np.fft.fft(burst_data)) #fft
    sp = np.fft.fftshift(sp)
    s_mag = np.abs(sp) / np.sum(win_funct)
    s_mag = np.maximum(s_mag, 10 ** (-15))
    s_dbfs = 20 * np.log10(s_mag / (2 ** 11))
    # print("Freq bins: ",freq)

    lower, upper = get_freq_bins(config,lower_freq,upper_freq)
    freq = freq[lower:upper]
    s_dbfs = s_dbfs[lower:upper]

    return freq,s_dbfs

def get_freq_bins(config,min,max):
    N_frames = config["fft_size"]
    samp_rate = config["fs"]
    lower_bin = int((min+(samp_rate/2))/(samp_rate/N_frames))
    upper_bin = int((max+(samp_rate/2))/(samp_rate/N_frames))
    return lower_bin, upper_bin
    

def show_waterfall(img,config):
    fig,ax = plt.subplots(figsize=(14, 7))
    # extent = [0, config["num_frames"], 100e3, 200e3]
    cmaps = ['inferno', 'plasma']
    cmn = cmaps[1]
    spectrogram = ax.imshow(img, aspect='auto',
             origin='lower', cmap=plt.colormaps.get_cmap(cmn),
            #  extent=extent
            )
    plt.show()

def get_sample_waterfall(sample,config):
    lower,upper = get_freq_bins(config,lower_freq,upper_freq)
    data_size = upper-lower
    img = np.ones((config["num_frames"],data_size))*-100
    position = config["num_frames"]
    freq_bins = np.ones((config["num_frames"],data_size))*-100
    for frame in sample:
        freq,s_dbfs = get_fft(frame,config)
        img = np.roll(img,1,axis = 0)
        img[0]=s_dbfs
        freq_bins = np.roll(freq_bins,1,axis=0)
        freq_bins[0]=freq
        position-=1
    return freq_bins,img

def separate_data_chirps(sum_data,num_chirps,good_ramp_samples,start_offset_samples,num_samples_frame,fft_size,black_man=False):
    global win_funct
    rx_bursts = np.zeros((num_chirps, good_ramp_samples), dtype=complex)
    for burst in range(num_chirps):
        start_index = start_offset_samples + burst*num_samples_frame
        stop_index = start_index + good_ramp_samples
        # print("stop index: ",stop_index,"\nstart index: ",start_index)
        rx_bursts[burst] = sum_data[start_index:stop_index]
        burst_data = np.ones(fft_size, dtype=complex)*1e-10
        if black_man:
            win_funct = np.blackman(len(rx_bursts[burst]))
        else:
            win_funct = np.ones(len(rx_bursts[burst]))
        burst_data[start_offset_samples:(start_offset_samples+good_ramp_samples)] = rx_bursts[burst]*win_funct
    
    return burst_data, rx_bursts, sum_data


waving_data = np.load(waving_file)
not_waving_data = np.load(not_waving_file)
print(len(waving_data))
processed_data = []
for config in waving_configs["data_configs"]:
    print(config)
    for samples in range(config["data_start"],config["data_start"]+config["data_size"]):
        sample = waving_data[samples]
        freq,img = get_sample_waterfall(sample,config)
        # show_fft(freq[1],img[1])
        # show_waterfall(img,config)
        flattened_data = img.flatten()
        processed_data.append([flattened_data,"Waving"])
        print(len(flattened_data))

for config in not_waving_configs["data_configs"]:
    print(config)
    for samples in range(config["data_start"],config["data_start"]+config["data_size"]):
        sample = not_waving_data[samples]
        freq,img = get_sample_waterfall(sample,config)
        # show_fft(freq[1],img[1])
        # show_waterfall(img,config)
        flattened_data = img.flatten()
        processed_data.append([flattened_data,"Not Waving"])
        print(len(flattened_data))
        
        
print("Number of Samples: ",len(processed_data))

with open('data/preprocessed_data/data.pkl',"xb") as f:
    pickle.dump(processed_data,f)
