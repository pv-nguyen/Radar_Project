import sys
import time
from dotenv import load_dotenv
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from matplotlib import cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from numpy import arange, cos, log10, pi, sin
from numpy.fft import fft, fft2, fftshift, ifft2, ifftshift
from PyQt6.QtCore import Qt
# from PyQt6.QtSvg import QSvgWidget
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QGridLayout, QLabel, QPushButton, QSlider
from PyQt6.QtGui import QFont
from pyqtgraph.Qt import QtCore, QtGui
from scipy import interpolate, signal
import params

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recording = False
        self.acquire = False
        self.countdown = -1
        self.countdownTimer = QtCore.QTimer()
        self.framesLeft = -1
        self.setWindowTitle("Plots")
        self.UiComponents()
        self.show()
        self.saveFile = ""
        self.countdownTimer.timeout.connect(self.start_countdown)
        
        

    def UiComponents(self):
        #Params for styling graphs
        signal_freq = params.signal_freq
        freq = params.freq
        plot_freq = params.plot_freq
        label_style = {"color": "#FFF", "font-size": "14pt"}
        title_style = {"size": "20pt"}

        widget = QWidget()
        layout = QGridLayout()

        #fft plot 
        self.fft_plot = pg.plot()
        self.fft_plot.setMinimumWidth(600)
        self.fft_curve = self.fft_plot.plot(freq,pen={'color':'y','width':2})
        self.fft_plot.setXRange(signal_freq,signal_freq+plot_freq)
        self.fft_plot.setYRange(-60,0)
        self.fft_plot.setLabel("bottom", text="Frequency", units="Hz", **label_style)
        self.fft_plot.setLabel("left", text="Magnitude", units="dB", **label_style)
        self.fft_plot.setTitle("Received Signal - Frequency Spectrum", **title_style)
        self.fft_threshold = self.fft_plot.plot(freq,pen={'color':'r','width':2}) #cfar threshold on fft plot
        layout.addWidget(self.fft_plot,1,0,1,4)

        #waterfall plot, maps gain to color, frequency spectrum over time
        self.water = pg.PlotWidget()
        self.imageitem = pg.ImageItem()
        self.water.addItem(self.imageitem)
        pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        color = np.array([[68, 1, 84,255], [59, 82, 139,255], [33, 145, 140,255], [94, 201, 98,255], [253, 231, 37,255]], dtype=np.ubyte)
        lut = pg.ColorMap(pos, color).getLookupTable(0.0, 1.0, 256)
        self.imageitem.setLookupTable(lut)
        self.imageitem.setLevels([0,1])
        tr = QtGui.QTransform()
        tr.translate(0,-params.fs/2)
        tr.scale(0.35, params.fs / params.fft_size)
        self.imageitem.setTransform(tr)
        zoom_freq = params.zoom_freq
        self.water.setRange(yRange=(signal_freq, signal_freq + zoom_freq))
        self.water.setTitle("Waterfall Spectrum", **title_style)
        self.water.setLabel("left", "Frequency", units="Hz", **label_style)
        self.water.setLabel("bottom", "Time", units="sec", **label_style)
        self.imageitem.setLevels([-45,0])
        layout.addWidget(self.water,2,0,1,4)
        self.img_array = np.ones((params.num_slices,params.fft_size))*-100


        # self.radarMap = pg.PlotWidget()
        # layout.addWidget(self.radarMap,0,1,4,1)

        self.recognitionLabel = QLabel()
        self.recognitionLabel.setText("test")
        layout.addWidget(self.recognitionLabel,0,0,1,2)

        # self.rangeDoppler = FigureCanvasQTAgg()
        # layout.addWidget(self.rangeDoppler,3,0,2,3)

        self.cfar_bias = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.cfar_bias.setValue(params.bias)
        self.cfar_bias.setMinimum(0)
        self.cfar_bias.setMaximum(100)
        self.cfar_bias.setTickInterval(5)
        self.cfar_bias.setMaximumWidth(200)
        self.cfar_bias.valueChanged.connect(self.get_cfar_values)
        layout.addWidget(self.cfar_bias, 3, 1)
        self.cfar_bias_label = QLabel("CFAR Bias (dB): %0.0f" % (self.cfar_bias.value()))
        self.cfar_bias_label.setMinimumWidth(100)
        self.cfar_bias_label.setMaximumWidth(200)
        layout.addWidget(self.cfar_bias_label, 4, 1)
        
        self.cfar_guard = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.cfar_guard.setValue(params.num_guard_cells)
        self.cfar_guard.setMinimum(1)
        self.cfar_guard.setMaximum(40)
        self.cfar_guard.setTickInterval(4)
        self.cfar_guard.setMaximumWidth(200)
        self.cfar_guard.valueChanged.connect(self.get_cfar_values)
        layout.addWidget(self.cfar_guard, 3, 2)
        self.cfar_guard_label = QLabel("Num Guard Cells: %0.0f" % (self.cfar_guard.value()))
        self.cfar_guard_label.setMinimumWidth(100)
        self.cfar_guard_label.setMaximumWidth(200)
        layout.addWidget(self.cfar_guard_label, 4, 2)
        
        self.cfar_ref = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.cfar_ref.setValue(params.num_ref_cells)
        self.cfar_ref.setMinimum(1)
        self.cfar_ref.setMaximum(100)
        self.cfar_ref.setTickInterval(10)
        self.cfar_ref.setMaximumWidth(200)
        self.cfar_ref.valueChanged.connect(self.get_cfar_values)
        layout.addWidget(self.cfar_ref, 3, 3)
        self.cfar_ref_label = QLabel("Num Ref Cells: %0.0f" % (self.cfar_ref.value()))
        self.cfar_ref_label.setMinimumWidth(100)
        self.cfar_ref_label.setMaximumWidth(200)
        layout.addWidget(self.cfar_ref_label, 4, 3)

        self.apply_cfar = QPushButton("Cfar toggle")
        self.apply_cfar.clicked.connect(self.change_cfar)
        layout.addWidget(self.apply_cfar,3,0,1,1)

        self.get_cfar_values()

        self.DOA = QLabel("Countdown: ")
        self.DOA.setMinimumWidth(150)
        DOA_font = QFont()
        DOA_font.setPointSize(22)
        self.DOA.setFont(DOA_font)
        layout.addWidget(self.DOA,0,4)

        self.dataLabel = QLabel("Data Acquisition: ")
        self.dataLabel.setMinimumWidth(150)
        data_font = QFont()
        data_font.setPointSize(22)
        self.dataLabel.setFont(data_font)
        layout.addWidget(self.dataLabel,5,0)
        
        self.saveDataButtonBW = QPushButton("Boresight Waving")
        self.saveDataButtonBW.setMinimumWidth(20)
        self.saveDataButtonBW.clicked.connect(self.save_boresight_waving)
        layout.addWidget(self.saveDataButtonBW,5,1)

        self.saveDataButtonBS = QPushButton("Boresight Standing")
        self.saveDataButtonBS.setMinimumWidth(20)
        self.saveDataButtonBS.clicked.connect(self.save_boresight_standing)
        layout.addWidget(self.saveDataButtonBS,5,2)

        self.countdownTxt = QLabel("waiting...")
        self.countdownTxt.setMinimumWidth(150)
        DOA_font = QFont()
        DOA_font.setPointSize(50)
        self.countdownTxt.setFont(DOA_font)
        layout.addWidget(self.countdownTxt,1,4)


        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def change_cfar(self,state):
        params.apply_cfar = not params.apply_cfar
    def get_cfar_values(self):
        self.cfar_bias_label.setText("CFAR Bias (dB): %0.0f" % (self.cfar_bias.value()))
        self.cfar_guard_label.setText("Num Guard Cells: %0.0f" % (self.cfar_guard.value()))
        self.cfar_ref_label.setText("Num Ref Cells: %0.0f" % (self.cfar_ref.value()))
        params.bias = self.cfar_bias.value()
        params.num_guard_cells = self.cfar_guard.value()
        params.num_ref_cells = self.cfar_ref.value()
    def save_boresight_waving(self,label):
        self.set_record_flag("data/waving_boresight/wbd.npy")
    def save_boresight_standing(self,label):
        self.set_record_flag("data/standing_boresight/wbs.npy")
    def set_record_flag(self,save_file):
        if not self.recording:
            self.recording = True
            self.framesLeft = params.num_frames
            self.saveFile=save_file
            params.save_file=save_file
            self.countdown = 4
            self.countdownTxt.setText(str(self.countdown))
            self.start_countdown()
    def start_countdown(self):
        self.countdown-=1
        self.countdownTxt.setText(str(self.countdown))
        if self.countdown > 0:
            self.countdownTimer.setSingleShot(True)
            print("Starting countdown timer")
            self.countdownTimer.start(1000)
            return
        else:
            print("Countdown complete, data acquisition starting")
            self.acquire = True

    


    pass

#run gui, just for testing gui by itself
if __name__ == "__main__":
    params.init()

    app = QApplication(sys.argv)
    window = MainWindow()

    def update():
        print("update")
        # pass

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(500)

    
    app.exec()