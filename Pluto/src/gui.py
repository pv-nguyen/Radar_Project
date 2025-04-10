import sys
import time
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
# from PyQt6.QtSvg import QSvgWidget
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QGridLayout, QLabel
from pyqtgraph.Qt import QtCore, QtGui
from scipy import interpolate, signal
import params

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plots")
        self.UiComponents()
        self.show()
        

    def UiComponents(self):

        signal_freq = params.signal_freq
        freq = params.freq
        plot_freq = params.plot_freq

        widget = QWidget()
        layout = QGridLayout()

        self.fft_plot = pg.plot()
        self.fft_plot.setMinimumWidth(600)
        self.fft_curve = self.fft_plot.plot(freq,pen={'color':'y','width':2})
        self.fft_plot.setXRange(signal_freq,signal_freq+plot_freq)
        self.fft_plot.setYRange(-60,0)
        layout.addWidget(self.fft_plot,1,1)

        self.water = pg.PlotWidget()
        layout.addWidget(self.water,2,1)

        self.radarMap = pg.PlotWidget()
        layout.addWidget(self.radarMap,1,0,2,1)

        self.recognitionLabel = QLabel()
        self.recognitionLabel.setText("test")
        layout.addWidget(self.recognitionLabel,0,0,1,2)


        widget.setLayout(layout)
        self.setCentralWidget(widget)
    pass

#run gui, just for testing gui by itself, will be called from main
# app = QApplication(sys.argv)


# params.init()
# window = MainWindow()

# def update():
#     print("update")

# timer = QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(1000)

# app.exec()