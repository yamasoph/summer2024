#!/usr/bin/python
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt

class PlotView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mirror Command")

        #figure
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        #navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setOrientation(Qt.Horizontal)

        #layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

        #plot the squares in the circle
        self.plot_circular_squares()

    def plot_circular_squares(self):
        self.ax.clear()

        #generate the squares
        positions = self.generate_square_positions(self)

        #plot squares
        self.patches = []
        colors = np.linspace(0.5, 0.5, len(positions))
        for pos, color in zip(positions, colors):
            square = Rectangle((pos[0] - 0.5, pos[1] - 0.5), 1, 1, edgecolor='black', facecolor=plt.cm.viridis(color))
            self.ax.add_patch(square)
            self.patches.append(square)

        #set limits to center around squares
        min_x = min(pos[0] - 0.5 for pos in positions)
        max_x = max(pos[0] + 0.5 for pos in positions)
        min_y = min(pos[1] - 0.5 for pos in positions)
        max_y = max(pos[1] + 0.5 for pos in positions)
        padding = 1  #make sure that there is space between the squares in both axes
        self.ax.set_xlim(min_x - padding, max_x + padding)
        self.ax.set_ylim(min_y - padding, max_y + padding)

        #make sure plot always looks square
        self.ax.set_aspect('equal')
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        #remove spines from graph
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        #add the colorbar
        norm = plt.Normalize(vmin=-1, vmax=1)
        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=norm)
        sm.set_array([])
        ax = self.figure.colorbar(sm, ax=self.ax)
        ax.outline.set_visible(False)

        self.canvas.draw()
    @staticmethod
    def generate_square_positions(self):
        positions = []
        num_squares = [5, 7, 9, 11, 11, 11, 11, 11, 9, 7, 5]
        num_rows = len(num_squares)
        max_num_squares = max(num_squares)
        square_spacing = 1.2  #padding as well

        for row, num in enumerate(num_squares):
            for i in range(num):
                x = (i - num / 2 + 0.5) * square_spacing
                y = (num_rows - row - 1) * square_spacing
                positions.append((x, y))

        return positions

    def _get_patches(self):
        return self.patches






# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Mirror Command")

#         self.plot_view = PlotView()
#         self.setCentralWidget(self.plot_view)

# def main():
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     main()
