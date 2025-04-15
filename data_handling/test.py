import pickle
import os



# with open("data/waving_boresight/wbd_config.pkl","rb+") as f:
#     config = pickle.load(f)
#     print(config)
#     config["data_configs"][0]["num_samples_frame"]=5200
#     config["data_configs"][0]["num_frames"]=5
# with open("data/waving_boresight/wbd_config.pkl","wb+") as f:
#     print(config)
#     pickle.dump(config,f)


gain_cal = "Pluto/calibration/gain_cal_val.pkl"
ph_cal = "Pluto/calibration/phase_cal_val.pkl"

with open(gain_cal,"rb+") as f:
    gains = pickle.load(f)
    print(gains)

with open(ph_cal,"rb+") as f:
    ph = pickle.load(f)
    print(ph)