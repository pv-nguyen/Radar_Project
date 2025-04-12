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
        label_style = {"color": "#FFF", "font-size": "14pt"}
        title_style = {"size": "20pt"}

        widget = QWidget()
        layout = QGridLayout()

        self.fft_plot = pg.plot()
        self.fft_plot.setMinimumWidth(600)
        self.fft_curve = self.fft_plot.plot(freq,pen={'color':'y','width':2})
        self.fft_plot.setXRange(signal_freq,signal_freq+plot_freq)
        self.fft_plot.setYRange(-60,0)
        layout.addWidget(self.fft_plot,1,1)

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
        zoom_freq = 35e3
        self.water.setRange(yRange=(signal_freq, signal_freq + zoom_freq))
        self.water.setTitle("Waterfall Spectrum", **title_style)
        self.water.setLabel("left", "Frequency", units="Hz", **label_style)
        self.water.setLabel("bottom", "Time", units="sec", **label_style)
        layout.addWidget(self.water,2,1)
        self.img_array = np.ones((params.num_slices,params.fft_size))*-100


        self.radarMap = pg.PlotWidget()
        layout.addWidget(self.radarMap,1,0,2,1)

        self.recognitionLabel = QLabel()
        self.recognitionLabel.setText("test")
        layout.addWidget(self.recognitionLabel,0,0,1,2)


        self.rangeDoppler = FigureCanvasQTAgg()
        layout.addWidget(self.rangeDoppler,3,0,2,3)


        widget.setLayout(layout)
        self.setCentralWidget(widget)
    pass

#run gui, just for testing gui by itself
if __name__ == "__main__":
    params.init()

    app = QApplication(sys.argv)
    window = MainWindow()

    def update():
        print("update")

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(1000)

    
    app.exec()