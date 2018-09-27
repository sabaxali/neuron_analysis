from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication
import sys
import numpy as np
import matplotlib.pyplot as plt

import plot_hist_gui
import plot_distance_hist

from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure


class PlotHistApp(QMainWindow):
    def __init__(self):
        super(PlotHistApp, self).__init__()
        self.ui = plot_hist_gui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.fetch_skiddata_button.clicked.connect(self.FetchSkidData)# connect button clicked with action
        self.ui.incoming_connections_checkbox.stateChanged.connect(self.ClickBox)
        self.ui.outgoing_connections_checkbox.stateChanged.connect(self.ClickBox)
        self.ui.plot_hist_button.clicked.connect(self.PlotHist)
        self.ui.plot_ring_check_box.stateChanged.connect(self.PlotRing)
        self.PlotCanvas()

    def PlotCanvas(self):
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ui.verticalLayout_3.addWidget(self.canvas)
        self.ui.verticalLayout_3.addWidget(self.toolbar)

    def FetchSkidData(self):
        self.skeleton_id_text = self.ui.enter_skid_textbox.text()
        self.filter_nodes_text = self.ui.filter_num_partner_nodes_textbox.text()
        self.neuron_conn_class = plot_distance_hist.NeuronConnectivity([self.skeleton_id_text])
        self.neuron_conn_class.filter_skid_data(self.ClickBox(), int(self.filter_nodes_text))
        self.neuron_conn_class.get_df()


    def ClickBox(self):
        if self.ui.incoming_connections_checkbox.isChecked():
            return 'post'
        if self.ui.outgoing_connections_checkbox.isChecked():
            return 'pre'

    def PlotHist(self):
        plt.cla()
        neuron_type1_text = str(self.ui.neuron_type1_box.currentText())
        self.neuron_conn_class.plot_hist(neuron_type=neuron_type1_text, PB_glom=self.PBGlom(), ring=self.PlotRing())
        self.canvas.draw()

    def PBGlom(self):
        pb_glom_box_text = str(self.ui.pb_glom_box.currentText())
        if pb_glom_box_text == 'None':
            return None
        else:
            return pb_glom_box_text

    def PlotRing(self):
        if self.ui.plot_ring_check_box.isChecked():
            return True
        else:
            return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlotHistApp()
    window.show()
    sys.exit(app.exec_())