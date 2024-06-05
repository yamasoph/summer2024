from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSlider, QScrollArea, QLineEdit, QSpinBox, QMessageBox, QMainWindow, QMdiArea, QMdiSubWindow
from PyQt5.QtCore import Qt
from mirror_command_plot import PlotView
import struct
import csv
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

Noll_Zernikes = ["Tilt Y", "Tilt X", "Power", "Astig 45", "Astig X", "Coma X", "Coma Y", "Trefoil Y", "Trefoil 45", "Primary Spherical", "Secondary Astig Y", "Secondary Astig 45", "Quadrafoil Y", "Quadrafoil 45", "Secondary Coma X", "Secondary Coma Y", "Secondary Trefoil 45", "Secondary Trefoil Y", "Pentafoil 45", "Pentafoil Y", "Secondary Spherical", "Tertiary Astig 45", "Tertiary Astig Y"]
Noll_Zernikes.extend([f"Mode {i+24}" for i in range(96 - len(Noll_Zernikes))])

### Add '/Lib' or '/Lib64' to path 
if (8 * struct.calcsize("P")) == 32:
    print("Use x86 libraries.")
    from Lib.asdk import DM
else:
    print("Use x86_64 libraries.")
    from Lib64.asdk import DM

class ZernikeSliders(QWidget):
    def __init__(self, window):
        super().__init__()
        
        self.window = window
        self.zernikeCount = QSpinBox()
        self.zernikeCount.setRange(1, 96)
        self.zernikeCount.setValue(8)
        self.zernikeSliders = []
        self.zernikeLineEdits = []
        self.zernikeMaxLabels = []

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Zernike Sliders")
        #make area scrollable when there isn't enough room for all sliders
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollArea.setWidget(self.scrollWidget)
        #call function for the amount of zernike modes chosen so that the sliders also represent that
        self.updateSliders(self.zernikeCount.value())
        #create reset button
        resetSliderButton = QPushButton("Reset")
        resetSliderButton.clicked.connect(self.resetSliders)
        #create a send value button to DM
        sendvalueButton = QPushButton("Send to DM")
        sendvalueButton.clicked.connect(self.sendValues)
        #set up the layout to put all these things in a horizontal layout
        zernike_controlLayout = QHBoxLayout()
        zernike_controlLayout.addWidget(QLabel("Zernike Modes: "))
        zernike_controlLayout.addWidget(self.zernikeCount)
        zernike_controlLayout.addWidget(sendvalueButton)
        #put all the widgets in one layout
        layout = QVBoxLayout()
        layout.addLayout(zernike_controlLayout)
        layout.addWidget(self.scrollArea)
        layout.addWidget(resetSliderButton)
        self.setLayout(layout)
        self.zernikeCount.valueChanged.connect(self.zernikeCountChanged)
        
    def zernikeCountChanged(self):
        self.count = self.zernikeCount.value()
        self.updateSliders(self.count)

    def updateSliders(self, count):
        sliderMin = -100
        sliderMax = 100
        for i in reversed(range(self.scrollLayout.count())):
            widget = self.scrollLayout.itemAt(i).widget()
            if widget is not None: #so scrollable area stays normal and not leave dead space
                widget.deleteLater()
        #set up all the empties for all the sliders, value boxes, and labels
        self.zernikeSliders = []
        self.zernikeLineEdits = []
        self.zernikeMaxLabels = []
        self.zernikeModeLabel = []

        for i in range(count):
            #create a max label on the top of each slider
            modeLabel = QLabel(str(Noll_Zernikes[i]))
            modeLabel.setAlignment(Qt.AlignLeft)
            self.zernikeModeLabel.append(modeLabel)
            maxLabel = QLabel(str(sliderMax))
            maxLabel.setAlignment(Qt.AlignRight)
            self.zernikeMaxLabels.append(maxLabel)
            #create a slider for each of the zernikes in the spinbox
            slider = QSlider(Qt.Horizontal)
            slider.setRange(sliderMin, sliderMax)
            slider.setValue(0)
            slider.valueChanged.connect(self.sliderChanged)
            #create value boxes on the bottom just in case if need to be an inputted value instead of a scrollable one
            lineEdit = QLineEdit()
            lineEdit.setFixedWidth(50)
            lineEdit.setAlignment(Qt.AlignCenter)
            lineEdit.setText("0")
            lineEdit.editingFinished.connect(lambda le=lineEdit, sl=slider: self.lineEditChanged(le, sl))
            #connect that if you scroll it it also shows up in the value box
            slider.valueChanged.connect(lambda value, le=lineEdit: le.setText(str(value)))
            #create a vertical layout to put each label, slider, and value box in
            individual_slider_layout = QVBoxLayout()
            individual_slider_layout.addWidget(modeLabel)
            individual_slider_layout.addWidget(maxLabel)
            individual_slider_layout.addWidget(slider)
            individual_slider_layout.addWidget(lineEdit)
            #put each vertical slider layout into another widget
            container = QWidget()
            container.setLayout(individual_slider_layout)
            #make sure that the widget is scrollable
            self.scrollLayout.addWidget(container)
            self.zernikeSliders.append(slider)
            self.zernikeLineEdits.append(lineEdit)

        self.scrollWidget.adjustSize()

    def resetSliders(self):
        #make all sliders go back to zero
        for slider in self.zernikeSliders:
            slider.setValue(0)
        self.sliderChanged()
        self.update_square_colors()

    def sliderChanged(self):
        #change the zernikes values to be the value that each slider says for each specific slider and corresponding zernike
        zernike_values = [slider.value() for slider in self.zernikeSliders]
        #changes the bar chart values as well
        self.window.barchart_tab.updateBarChart(zernike_values)
        self.update_square_colors()

    def lineEditChanged(self, lineEdit, slider):
        #try,except statement for editing the zernike values in case of value entered that is not within range
        try:
            value = int(lineEdit.text())
            slider.setValue(value)
        except ValueError:
            lineEdit.setText(str(slider.value()))

    def calculate_colors_from_zernike(self):
        serialName = self.window.serialName
        zernike_values = np.array([slider.value() / 100.0 for slider in self.zernikeSliders])
        Z2C = []

        try:
            with open('./config/'+serialName+'-Z2C.csv', newline='') as csvfile:
                csvrows = csv.reader(csvfile, delimiter=' ')
                for row in csvrows:
                    x = row[0].split(",")
                    Z2C.append([float(value) for value in x])
        except FileNotFoundError:
            QMessageBox.critical(self, "File Error", "Configuration file not found")
            return

        Z2C = np.array(Z2C)
        #takes the rows and transposes them so that they can all be multiplied by their specific zernike values from the sliders
        actuator_values = Z2C[:len(zernike_values)].T @ zernike_values
        if (np.max(actuator_values)>1) or (np.min(actuator_values) < -1):
            actuator_values = (actuator_values - actuator_values.min()) / (actuator_values.max() - actuator_values.min())  #scales to [0,1]
            actuator_values = 2 * actuator_values - 1  #scales to [-1,1]
        self.colors = actuator_values

    def update_square_colors(self):
        self.calculate_colors_from_zernike()
        self.window.plot_view.ax.clear()
        positions = PlotView.generate_square_positions(self)
        norm = plt.Normalize(vmin=min(self.colors), vmax=max(self.colors))
        colormap = plt.cm.viridis
        for pos, color_value in zip(positions, self.colors):
            normalized_color = norm(color_value)
            color = colormap(normalized_color)
            square = Rectangle((pos[0] - 0.5, pos[1] - 0.5), 1, 1, facecolor=color)
            self.window.plot_view.ax.add_patch(square)
        self.window.plot_view.ax.set_aspect('equal')
        self.window.plot_view.ax.set_xlim((-7,7))
        self.window.plot_view.ax.set_ylim((-1,13))
        self.window.plot_view.ax.set_xticks([])
        self.window.plot_view.ax.set_yticks([])
        self.window.plot_view.canvas.draw()

    def sendValues(self):
        self.calculate_colors_from_zernike()
        dm = self.window.dm
        actuator_values = self.colors
        print(actuator_values, np.max(actuator_values), np.min(actuator_values), np.mean(actuator_values), np.std(actuator_values))
        dm.Send(actuator_values.tolist())
        QMessageBox.information(self, "Success", "Values sent to DM")

class ZernikeBarChart(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Zernike Bar Chart")
        #make the barchart figure
        self.barchartFig, self.barchartAx = plt.subplots()
        self.barchartCanvas = FigureCanvas(self.barchartFig)
        #make the slider for the barchart
        self.yAxisSlider = QSlider(Qt.Vertical)
        self.yAxisSlider.setRange(1, 200)
        self.yAxisSlider.setValue(10)
        self.yAxisSlider.valueChanged.connect(self.updateYAxisRange_BarChart)
        #make the label for the slider for the barchart
        self.yMinLabel = QLabel("1")
        self.yMinLabel.setAlignment(Qt.AlignCenter)
        self.yMaxLabel = QLabel("200")
        self.yMaxLabel.setAlignment(Qt.AlignCenter)
        #add slider labels and slider together
        sliderLayout = QVBoxLayout()
        sliderLayout.addWidget(self.yMaxLabel)
        sliderLayout.addWidget(self.yAxisSlider)
        sliderLayout.addWidget(self.yMinLabel)
        self.toolbar = NavigationToolbar(self.barchartCanvas, self)
        #put slider next to the barchart on the right
        barchart_layout = QVBoxLayout()
        barchart_layout.addWidget(self.barchartCanvas)
        barchart_layout.addWidget(self.toolbar)
        layout = QHBoxLayout()
        layout.addLayout(barchart_layout)
        layout.addLayout(sliderLayout)
        self.barchartFig.subplots_adjust(bottom=0.2)
        self.setLayout(layout)

    def updateYAxisRange_BarChart(self):
        #create y min and y max so that it matches the slider, set up graph as well
        y_max = self.yAxisSlider.value()
        self.barchartAx.set_ylim([-y_max, y_max])
        self.barchartAx.axhline(0, color='darkgrey', linewidth=0.5, zorder = 0)
        self.barchartAx.grid(color='lightgrey', linestyle='-', linewidth=0.5, zorder=1)
        self.barchartAx.set_yticks(np.linspace(-y_max, y_max, 5))
        self.barchartCanvas.draw()

    def updateBarChart(self, data):
        #update bar chart using data from the zernike sliders values
        self.barchartAx.clear()
        self.barchartAx.bar(range(1, len(data) + 1), data, color='red', zorder=2)
        self.barchartAx.set_xlim(0.5, len(data) + 0.5) 
        self.barchartAx.set_xticks(range(1, len(data) + 1))
        self.barchartAx.set_xticklabels(Noll_Zernikes[:len(data)], rotation=35, ha='right', wrap = True)
        for i, coeff in enumerate(data):
            self.barchartAx.text(i + 1, coeff + 0.1 * max(data), str(coeff), ha='center', va='bottom')

        self.updateYAxisRange_BarChart()


class DMControl(QMainWindow):
    def __init__(self, dm, serialName):
        super().__init__()
        self.dm = dm
        self.serialName = serialName
        #allow the tabs to be moveable
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        self.initUI()

    def initUI(self):
        #create the zernike sliders tab
        zernike_sub = QMdiSubWindow()
        self.zernike_tab = ZernikeSliders(self)
        zernike_sub.setWidget(self.zernike_tab)
        self.mdi.addSubWindow(zernike_sub)
        #zernike barchart tab
        barchart_sub = QMdiSubWindow()
        self.barchart_tab = ZernikeBarChart()
        barchart_sub.setWidget(self.barchart_tab)
        self.mdi.addSubWindow(barchart_sub)
        #plot view tab
        plotview_sub = QMdiSubWindow()
        self.plot_view = PlotView()
        plotview_sub.setWidget(self.plot_view)
        self.mdi.addSubWindow(plotview_sub)
        #set the window itself
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("DM Control")
        self.show()

def main(args):
    print("Please enter the S/N within the following format BXXYYY (see DM backside): ")
    serialName = sys.stdin.readline().rstrip()
    print("Connect the mirror")
    dm = DM(serialName)
    print("Retrieve number of actuators")
    nbAct = int(dm.Get('NBOfActuator'))
    print("Number of actuator for " + serialName + ": " + str(nbAct))
    print("Send 0 on each actuators")
    values = [0.] * nbAct
    dm.Send(values)
    app = QApplication(sys.argv)
    window = DMControl(dm, serialName)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main(sys.argv)
