import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QComboBox, 
                           QSpinBox, QGroupBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import tempfile
import os
import time

class PlotlyFigureManager:
    """Class to handle creation and management of Plotly figures"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.html_path = os.path.join(self.temp_dir, 'plotly_graph.html')
        
    def create_multiplot(self, num_points=10000):
        # Create sample data
        x = np.linspace(0, 10, num_points)
        y1 = np.sin(x)
        y2 = np.cos(x)
        y3 = np.tan(x)
        
        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Sine Wave', 'Cosine Wave', 'Tangent Wave', 'Combined'),
            specs=[[{}, {}], [{}, {}]]
        )
        
        # Add traces
        fig.add_trace(
            go.Scatter(x=x, y=y1, mode='lines', name='Sine'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=x, y=y2, mode='lines', name='Cosine'),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(x=x, y=y3, mode='lines', name='Tangent'),
            row=2, col=1
        )
        
        # Combined plot
        fig.add_trace(
            go.Scatter(x=x, y=y1, mode='lines', name='Sine', showlegend=False),
            row=2, col=2
        )
        fig.add_trace(
            go.Scatter(x=x, y=y2, mode='lines', name='Cosine', showlegend=False),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="Trigonometric Functions",
            showlegend=True
        )
        
        # Save to file
        fig.write_html(self.html_path)
        return self.html_path
    
    def cleanup(self):
        if os.path.exists(self.html_path):
            os.remove(self.html_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Advanced Data Viewer')
        self.setGeometry(100, 100, 1200, 900)
        
        # Initialize PlotlyFigureManager
        self.figure_manager = PlotlyFigureManager()
        
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
        self.points_spinbox.setRange(10, 100000)
        self.points_spinbox.setValue(100000)
        self.points_spinbox.setSingleStep(10)
        controls_layout.addWidget(QLabel("Number of Points:"))
        controls_layout.addWidget(self.points_spinbox)
        
        # Add update button
        self.update_btn = QPushButton("Update Plots")
        self.update_btn.clicked.connect(self.update_plots)
        controls_layout.addWidget(self.update_btn)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Create WebEngine View
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Initialize plots
        self.update_plots()
        
        # Add status bar
        self.statusBar().showMessage('Ready')
    
    def update_plots(self):
        starttime = time.time()
        num_points = self.points_spinbox.value()
        self.statusBar().showMessage('Updating plots...')
        
        # Generate new plots
        html_path = self.figure_manager.create_multiplot(num_points)
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))
        
        endtime = time.time()
        text = f'Plots updated in {endtime - starttime:.2f} seconds'
        self.statusBar().showMessage(text)
    
    def closeEvent(self, event):
        self.figure_manager.cleanup()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()