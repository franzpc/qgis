from qgis.core import QgsApplication, QgsPointXY, QgsGeometry, QgsFeature, QgsVectorLayer, QgsProject, QgsCoordinateTransform
from qgis.gui import QgisInterface
from PyQt5.QtWidgets import QAction
from .scripts.processing_algorithm import CoordinateCalculatorAlgorithm
from .scripts.calculate_line_algorithm import CalculateLineAlgorithm
from .scripts.go_to_xy import GoToXYDialog
from .scripts.from_polygon_to_points import PolygonToPointsAlgorithm
from .scripts.basin_analysis_algorithm import BasinAnalysisAlgorithm

class ArcGeekCalculator:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.actions = []
        self.menu = '&ArcGeek Calculator'
        self.coordinate_algorithm = None
        self.line_algorithm = None
        self.polygon_to_points_algorithm = None
        self.basin_analysis_algorithm = None
        self.go_to_xy_dialog = None

    def initGui(self):
        self.coordinate_algorithm = CoordinateCalculatorAlgorithm()
        self.line_algorithm = CalculateLineAlgorithm()
        self.polygon_to_points_algorithm = PolygonToPointsAlgorithm()
        self.basin_analysis_algorithm = BasinAnalysisAlgorithm()
        
        self.add_action("Calculate Coordinates", self.run_coordinate_calculator)
        self.add_action("Calculate Line from Coordinates and Table", self.run_line_calculator)
        self.add_action("Extract Ordered Points from Polygons", self.run_polygon_to_points)
        self.add_action("Watershed Morphometric Analysis", self.run_basin_analysis)
        self.add_action("Go to XY", self.run_go_to_xy)

    def add_action(self, text, callback):
        action = QAction(text, self.iface.mainWindow())
        action.triggered.connect(callback)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)

    def run_coordinate_calculator(self):
        from qgis import processing
        processing.execAlgorithmDialog(self.coordinate_algorithm)

    def run_line_calculator(self):
        from qgis import processing
        processing.execAlgorithmDialog(self.line_algorithm)

    def run_polygon_to_points(self):
        from qgis import processing
        processing.execAlgorithmDialog(self.polygon_to_points_algorithm)

    def run_basin_analysis(self):
        from qgis import processing
        processing.execAlgorithmDialog(self.basin_analysis_algorithm)

    def run_go_to_xy(self):
        if self.go_to_xy_dialog is None:
            self.go_to_xy_dialog = GoToXYDialog(self, self.iface.mainWindow())
        self.go_to_xy_dialog.show()

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
        if self.go_to_xy_dialog:
            self.go_to_xy_dialog.close()
            self.go_to_xy_dialog = None

    def go_to_xy(self, x, y, coord_type, source_crs, create_point):
        canvas = self.iface.mapCanvas()
        dest_crs = canvas.mapSettings().destinationCrs()
        
        point = QgsPointXY(x, y)
        
        try:
            if source_crs != dest_crs:
                transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
                point = transform.transform(point)
            
            canvas.setCenter(point)
            canvas.zoomScale(5000)  # You can adjust this zoom level
            canvas.refresh()
            
            if create_point:
                self.create_point_marker(point, dest_crs)
        except Exception as e:
            self.iface.messageBar().pushMessage("Error", f"Failed to transform coordinates: {str(e)}", level=1, duration=5)

    def create_point_marker(self, point, crs):
        vl = QgsVectorLayer("Point?crs={}".format(crs.authid()), "Go to XY Point", "memory")
        pr = vl.dataProvider()
        
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPointXY(point))
        pr.addFeature(fet)
        
        vl.updateExtents()
        QgsProject.instance().addMapLayer(vl)