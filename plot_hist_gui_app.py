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


class PlotHistApp_View(QMainWindow):
    def __init__(self):
        super(PlotHistApp_View, self).__init__()
        self.ui = plot_hist_gui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.controller = None
        self.ui.incoming_connections_checkbox.stateChanged.connect(self.directionOfConnections_box)
        self.ui.outgoing_connections_checkbox.stateChanged.connect(self.directionOfConnections_box)
        self.ui.fetch_skiddata_button.clicked.connect(self.fetchSkidData)
        self.ui.plot_hist_button.clicked.connect(self.selectWhatToPlot)
        self.ui.plot_ring_check_box.stateChanged.connect(self.plotRing)
        self.plotCanvas()
        self.show()

    def setController(self, controller):
        self.controller = controller

    def fetchSkidData(self):
        skeleton_id_text = self.ui.enter_skid_textbox.text()
        direction = self.checkedBox()
        filter_nodes_text = self.ui.filter_num_partner_nodes_textbox.text()
        self.controller.fetchSkidData(skeleton_id_text, direction, filter_nodes_text)

    def directionOfConnections_box(self):
        direction = None
        if self.ui.incoming_connections_checkbox.isChecked():
            direction = 'post'
        if self.ui.outgoing_connections_checkbox.isChecked():
            direction = 'pre'
        return direction

    def selectWhatToPlot(self):
        neuron_type1_text = str(self.ui.neuron_type1_box.currentText())
        neuron_type2_text = str(self.ui.neuron_type2_box.currentText())
        pb_glom1 = self.pbGlom1()
        pb_glom2 = self.pbGlom2()
        plot_ring = self.plotRing()
        self.figure.clear()
        self.controller.plotHist(neuron_type1_text, neuron_type2_text, pb_glom1, pb_glom2, plot_ring)
        self.canvas.draw_idle()

    def pbGlom1(self):
        pb_glom1_box_text = str(self.ui.pb_glom1_box.currentText())
        if pb_glom1_box_text == 'None':
            return None
        else:
            return pb_glom1_box_text

    def pbGlom2(self):
        pb_glom2_box_text = str(self.ui.pb_glom2_box.currentText())
        if pb_glom2_box_text == 'None':
            return None
        else:
            return pb_glom2_box_text

    def plotRing(self):
        plot_ring = False
        if self.ui.plot_ring_check_box.isChecked():
            plot_ring = True
        return plot_ring

    def plotCanvas(self):
        self.figure = plt.figure(figsize=(5, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ui.verticalLayout_3.addWidget(self.canvas)
        self.ui.verticalLayout_3.addWidget(self.toolbar)


class PlotHistApp_Controller:

    def __init__(self, model, view):
        self.model = model
        self.view = view

        self.view.setController(self)
        self.model.setController(self)

    def fetchSkidData(self, neuron_id, direction, filter_num_nodes):
        self.model.fetchSkidData(neuron_id, direction, filter_num_nodes)

    def clickBox(self, direction):
        self.model.setDirection(direction)

    def plotHist(self, neuron_type1_text, neuron_type2_text, pb_glom1, pb_glom2, plot_ring):
        self.model.plotHist(neuron_type1_text, neuron_type2_text, pb_glom1, pb_glom2, plot_ring)


class PlotHistApp_Model:
    def __init__(self):
        self.controller = None

    def fetchSkidData(self, neuron_id, direction, filter_num_nodes):
        self.neuron_id = neuron_id
        self.filter_num_nodes = filter_num_nodes
        self.direction = direction
        self.neuron_conn_class = plot_distance_hist.NeuronConnectivity([self.neuron_id])
        self.neuron_conn_class.filter_skid_data(self.direction, int(self.filter_num_nodes))
        self.neuron_conn_class.get_df()

    def plotHist(self, neuron_type1, neuron_type2, pb_glom1, pb_glom2, plot_ring):
        self.neuron_type1 = neuron_type1
        self.neuron_type2 = neuron_type2
        self.pb_glom1 = pb_glom1
        self.pb_glom2 = pb_glom2
        self.plot_ring = plot_ring
        self.neuron_conn_class.plot_hist(neuron_type=self.neuron_type1, neuron_type2=self.neuron_type2,
                                         PB_glom=self.pb_glom1, PB_glom2=self.pb_glom2, ring=plot_ring)

    def setController(self, controller):
        self.controller = controller


if __name__ == '__main__':
    app = QApplication(sys.argv)
    v = PlotHistApp_View()
    m = PlotHistApp_Model()
    c = PlotHistApp_Controller(m,v)
    sys.exit(app.exec_())
