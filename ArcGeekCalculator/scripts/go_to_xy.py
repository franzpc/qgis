from qgis.PyQt.QtWidgets import QAction, QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox, QCheckBox
from qgis.core import QgsPointXY, QgsGeometry, QgsFeature, QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.gui import QgsProjectionSelectionWidget
from PyQt5.QtGui import QIcon

class GoToXYDialog(QDialog):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.iface = plugin.iface
        self.setWindowTitle("Go to XY")
        
        self.layout = QVBoxLayout()
        
        self.coord_type = QComboBox()
        self.coord_type.addItems(["Projected Coordinates", "Decimal Degrees"])
        self.coord_type.currentIndexChanged.connect(self.update_input_labels)
        self.layout.addWidget(QLabel("Coordinate Type:"))
        self.layout.addWidget(self.coord_type)
        
        self.label_y = QLabel("Y:")
        self.input_y = QLineEdit()
        self.layout.addWidget(self.label_y)
        self.layout.addWidget(self.input_y)
        
        self.label_x = QLabel("X:")
        self.input_x = QLineEdit()
        self.layout.addWidget(self.label_x)
        self.layout.addWidget(self.input_x)
        
        self.crs_selector = QgsProjectionSelectionWidget()
        self.crs_selector.setCrs(self.iface.mapCanvas().mapSettings().destinationCrs())
        self.layout.addWidget(QLabel("Input CRS:"))
        self.layout.addWidget(self.crs_selector)
        
        self.create_point = QCheckBox("Create point marker")
        self.create_point.setChecked(True)
        self.layout.addWidget(self.create_point)
        
        self.button = QPushButton("Go")
        self.button.clicked.connect(self.go_to_coordinates)
        self.layout.addWidget(self.button)
        
        self.setLayout(self.layout)
        
    def update_input_labels(self):
        coord_type = self.coord_type.currentText()
        if coord_type == "Decimal Degrees":
            self.label_y.setText("Latitude:")
            self.label_x.setText("Longitude:")
            self.crs_selector.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
            self.crs_selector.setEnabled(False)
        else:
            self.label_y.setText("Y:")
            self.label_x.setText("X:")
            self.crs_selector.setEnabled(True)
    
    def get_coordinates(self):
        y = float(self.input_y.text())
        x = float(self.input_x.text())
        coord_type = self.coord_type.currentText()
        crs = self.crs_selector.crs()
        create_point = self.create_point.isChecked()
        return x, y, coord_type, crs, create_point
    
    def go_to_coordinates(self):
        x, y, coord_type, crs, create_point = self.get_coordinates()
        self.plugin.go_to_xy(x, y, coord_type, crs, create_point)