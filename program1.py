import time
import sys
import pickle
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow,  QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QLabel, QCheckBox, QDialogButtonBox, QFileDialog
from PyQt5.QtCore import QFileInfo, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from dashboard.device import Device
from psu_ctrl import MainWindow

nPoints = 240
channelLabels = ["Channel 0", "Channel 1", "Channel 2", "Channel 3", "Channel 4", "Channel 5", "Channel 6", "Channel 7",
                 "Channel 8", "Channel 9", "Channel 10", "Channel 11", "Channel 12", "Channel 13", "Channel 14", "Channel 15"]

_pickradius = 5  # Points (Pt). How close the click needs to be to trigger an event.
_map_legend_to_ax = {}  # Will map legend lines to original lines.

class MonitorWindow(QWidget):
    def __init__(self, device):
        super(MonitorWindow, self).__init__()
        self.values = []
        self.setupMeters()
        self.windowTimer = QTimer(self, timeout=self.updateValue, interval=100)
        self.windowTimer.start()
    def setupMeters(self):
        layout = QVBoxLayout()
        for i in range(16):
            hLayout = QHBoxLayout()
            label = QLabel(f"Channel {i:02d} : ")
            hLayout.addWidget(label)
            value = QLabel(f"{0.0:f} V")
            hLayout.addWidget(value)
            self.values.append(value)
            layout.addLayout(hLayout)
        self.setLayout(layout)
        self.setWindowTitle("PSU Monitor")
    def updateValue(self):
        for i in range(16):
            self.values[i].setText(f"{device.analog_read(i):2.4f} V")

class RecordDialog(QDialog):
    def __init__(self, parent=None):
        super(RecordDialog, self).__init__(parent)
        self.setWindowTitle("Channels to record")
        record_label = QLabel("Select channels to record", self)
    
        self.channelCheckboxes = []
        for channelLabel in range(len(channelLabels)): #make 16 check boxes that will save as 1 or 0 if clicked or not
            channelCheckbox = QCheckBox(f"Channel {channelLabel}")
            channelCheckbox.setChecked(False)
            self.channelCheckboxes.append(channelCheckbox)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)

        # Connect the buttons to the appropriate slots
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(record_label)
        for channelLabel in range(len(channelLabels)):
            mainLayout.addWidget(self.channelCheckboxes[channelLabel])
        mainLayout.addWidget(button_box)

class ApplicationWindow(QMainWindow):
    def __init__(self, device):
        super(ApplicationWindow, self).__init__()
        self.setWindowTitle("PSU Monitor") #adds a title to the window
        self.mainWidget = self.setupMain()
        self.setCentralWidget(self.mainWidget)
        self.device = device

    def setupMain(self):
        self.isSaving = False
        self.index = 0
        self.version = 0
        self.startTime = time.time()
        self.voltage_values = np.full((len(channelLabels),nPoints), fill_value=np.nan)
        self.time_values = np.full((nPoints), fill_value=np.nan)

        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        toolbar = NavigationToolbar(self.canvas, self)

        axis = self.canvas.figure.subplots()
        axis.set_title("Voltage vs Time")
        axis.set_xlabel("Time(s)")
        axis.set_ylabel("Voltage (V)")
        self.lines = []
        self.colors = ["deeppink", "magenta", "darkviolet", "indigo", "darkslateblue", "midnightblue", "blue", "dodgerblue", "lightskyblue", "lightblue", "teal",  "mediumseagreen", "darkgreen", "darkolivegreen", "yellowgreen", "khaki"]
        for iChannel in range(len(channelLabels)):
            line, = axis.plot(self.time_values,self.voltage_values[iChannel], linestyle = 'none', label=channelLabels[iChannel], color = self.colors[iChannel], marker='.')
            self.lines.append(line)
        self.canvasTimer = self.canvas.new_timer()
        self.canvasTimer.add_callback(self.updateCanvas)
        self.canvasTimer.start()
        legend = axis.legend(loc = 'upper right', fontsize = 7, ncols = 2)
        for legendLine, axLine in zip(legend.get_lines(), self.lines):
            legendLine.set_picker(_pickradius)  # Enable picking on the legend line.
            _map_legend_to_ax[legendLine] = axLine

        self.canvas.mpl_connect('pick_event', self.onLegendPick)

        recordStop_button = QPushButton("Record") #create button called Record that opens second window
        recordStop_button.clicked.connect(self.startRecording)

        findLines_button = QPushButton("Find") #create button called Record that opens second window
        findLines_button.clicked.connect(self.findLines)

        monitor_button = QPushButton("Monitor")
        monitor_button.clicked.connect(self.monitor)

        # ---- layout ----
        widget = QWidget()
        vBoxLayout = QVBoxLayout()
        hBoxLayout = QHBoxLayout()
        vBoxLayout.addWidget(self.canvas)
        hBoxLayout.addWidget(toolbar)
        hBoxLayout.addWidget(recordStop_button)
        hBoxLayout.addWidget(findLines_button)
        hBoxLayout.addWidget(monitor_button)
        vBoxLayout.addLayout(hBoxLayout)
        widget.setLayout(vBoxLayout)
        widget.recordStop_button = recordStop_button

        return widget
    
    def updateCanvas(self):
        self.index += 1 #start incrementing to index
        self.index = self.index%nPoints
        self.time_values[self.index] = time.time() - self.startTime
        for iChannel in range(len(channelLabels)):
            self.voltage_values[iChannel, self.index] = device.analog_read(iChannel)
            if self.lines[iChannel].get_visible():
                self.lines[iChannel].set_data(self.time_values, self.voltage_values[iChannel])
            self.lines[iChannel].figure.canvas.draw()
        if self.isSaving:
            if self.index == nPoints-1:
                self.data = np.vstack((self.time_values.transpose(), self.voltage_values[self.checks, :]))
                self.fileName = f"{self.fileInfo.absolutePath()}/{self.fileInfo.baseName()}_{self.version:03d}.pkl"
                self.version += 1
                with open(self.fileName, 'wb') as file:
                    pickle.dump(self.data, file)
                print("saved file" + self.fileName)

    def stopRecording(self):
        self.mainWidget.recordStop_button.clicked.disconnect()
        self.isSaving = False
        with open(f"{self.fileInfo.absolutePath()}/{self.fileInfo.baseName()}_{(self.version + 1):03d}.pkl", 'wb') as file:
            pickle.dump(np.vstack((self.time_values.transpose(), self.voltage_values[self.checks, :])), file)
        print("saved file : " + f"{self.fileInfo.absolutePath()}/{self.fileInfo.baseName()}_{(self.version+1):03d}.pkl")
        self.version = 0 #reset for next trial if window still open
        self.mainWidget.recordStop_button.setText("Record")
        self.mainWidget.recordStop_button.clicked.connect(self.startRecording)
        
    def startRecording(self):
        recordDialog = RecordDialog()
        result = recordDialog.exec_()
        if result == QDialog.Accepted:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            defaultFileType = "Pickle File (*.pkl)"
            _fileName, _ = QFileDialog.getSaveFileName(self, "Save data", ".", defaultFileType, options=options)
            if _fileName:
                self.fileInfo = QFileInfo(_fileName)
                self.isSaving = True
                self.checks = [checkbox.isChecked() for checkbox in recordDialog.channelCheckboxes]
                self.mainWidget.recordStop_button.clicked.disconnect()
                self.mainWidget.recordStop_button.setText("Stop")
                self.mainWidget.recordStop_button.clicked.connect(self.stopRecording)

    def findLines(self):
        axis = self.canvas.figure.get_axes()[0]
        xmin, xmax = np.nanmin(self.time_values), np.nanmax(self.time_values)
        ymin, ymax = np.nanmin(self.voltage_values), np.nanmax(self.voltage_values)
        if not xmin == xmax:
            axis.set_xlim(xmin, xmax)
        if not ymin == ymax:
            axis.set_ylim(ymin, ymax)

    def onLegendPick(self, event):
        # On the pick event, find the original line corresponding to the legend proxy line, and toggle its visibility.
        legendLine = event.artist
        # Do nothing if the source of the event is not a legend line.
        if legendLine not in _map_legend_to_ax:
            return
        ax_line = _map_legend_to_ax[legendLine]
        visible = not ax_line.get_visible()
        ax_line.set_visible(visible)
        # Change the alpha on the line in the legend, so we can see what lines have been toggled.
        legendLine.set_alpha(1.0 if visible else 0.2)
        self.canvas.draw()
    def monitor(self):
        self.second_window = MonitorWindow(self.device)
        self.second_window.show()

if __name__ == "__main__":
    device = Device('/dev/comedi0')
    app = QApplication(sys.argv)
    app_window = ApplicationWindow(device)
    app_window.show()
    sys.exit(app.exec_())
