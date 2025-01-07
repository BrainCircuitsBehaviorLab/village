import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QComboBox, 
                           QSpinBox, QGroupBox)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np

class MatplotlibFigureManager:
    """Class to handle creation and management of Matplotlib figures"""
    
    def __init__(self):
        self.fig = plt.figure(figsize=(10, 8))
        
    def create_multiplot(self, num_points=50):
        self.fig.clear()
        
        # Create sample data
        x = np.linspace(0, 10, num_points)
        y1 = np.sin(x)
        y2 = np.cos(x)
        y3 = np.tan(x)
        
        # Create subplots
        ax1 = self.fig.add_subplot(221)
        ax2 = self.fig.add_subplot(222)
        ax3 = self.fig.add_subplot(223)
        ax4 = self.fig.add_subplot(224)
        
        # Plot data
        ax1.plot(x, y1, label='Sine')
        ax1.set_title('Sine Wave')
        ax1.grid(True)
        
        ax2.plot(x, y2, label='Cosine')
        ax2.set_title('Cosine Wave')
        ax2.grid(True)
        
        ax3.plot(x, y3, label='Tangent')
        ax3.set_title('Tangent Wave')
        ax3.grid(True)
        
        # Combined plot
        ax4.plot(x, y1, label='Sine')
        ax4.plot(x, y2, label='Cosine')
        ax4.set_title('Combined')
        ax4.grid(True)
        ax4.legend()
        
        self.fig.tight_layout()
        return self.fig

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Advanced Data Viewer')
        self.setGeometry(100, 100, 1000, 800)
        
        # Initialize MatplotlibFigureManager
        self.figure_manager = MatplotlibFigureManager()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create top controls
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout()
        
        # Add data selection combo box
        self.data_selector = QComboBox()
        self.data_selector.addItems(['Trigonometric', 'Random', 'Custom'])
        controls_layout.addWidget(QLabel("Data Type:"))
        controls_layout.addWidget(self.data_selector)
        
        # Add points spinbox
        self.points_spinbox = QSpinBox()
        self.points_spinbox.setRange(10, 200)
        self.points_spinbox.setValue(50)
        self.points_spinbox.setSingleStep(10)
        controls_layout.addWidget(QLabel("Number of Points:"))
        controls_layout.addWidget(self.points_spinbox)
        
        # Add update button
        self.update_btn = QPushButton("Update Plots")
        self.update_btn.clicked.connect(self.update_plots)
        controls_layout.addWidget(self.update_btn)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Create canvas and toolbar
        self.canvas = FigureCanvas(self.figure_manager.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Initialize plots
        self.update_plots()
        
        # Add status bar
        self.statusBar().showMessage('Ready')
    
    def update_plots(self):
        num_points = self.points_spinbox.value()
        self.statusBar().showMessage('Updating plots...')
        
        # Generate new plots
        self.figure_manager.create_multiplot(num_points)
        self.canvas.draw()
        
        self.statusBar().showMessage('Plots updated')

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()