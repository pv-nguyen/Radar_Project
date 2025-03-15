import adi
from dotenv import load_dotenv
import os

#Environment variables
load_dotenv()

#Ip addresses
rpi_ip = os.getenv("rpi_ip")
sdr_ip = os.getenv('sdr_ip')

#Software Defined Radio
my_sdr = adi.Pluto(uri=sdr_ip)
# my_sdr.rx_lo = 2.2e9
# my_sdr.tx_lo = 2.2e9

#Phaser Board
my_phaser = adi.CN0566(uri=rpi_ip, rx_dev=my_sdr)

data = my_sdr.rx()
print(data)