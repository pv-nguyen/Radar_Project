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
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QGridLayout
from pyqtgraph.Qt import QtCore, QtGui
from scipy import interpolate, signal

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plots")
        self.UiComponents()
        self.show()

    def UiComponents(self):
        widget = QWidget()

        layout = QGridLayout()
        self.fft_plot = pg.PlotWidget()

        layout.addWidget(self.fft_plot,0,2)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    pass

app = QApplication(sys.argv)

window = MainWindow()

def update():
    print("update")

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1000)

app.exec()