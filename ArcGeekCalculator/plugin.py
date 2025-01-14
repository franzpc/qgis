import os
from qgis.core import QgsApplication, QgsMapLayer, QgsWkbTypes, Qgis, QgsLayerTreeNode
from qgis.gui import QgisInterface
from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtGui import QIcon
from .scripts.coordinate_algorithm import CoordinateCalculatorAlgorithm
from .scripts.calculate_line_geometry import CalculateLineGeometryAlgorithm
from .scripts.calculate_polygon_geometry import CalculatePolygonGeometryAlgorithm
from .scripts.go_to_xy import GoToXYDialog
from .scripts.from_polygon_to_points import PolygonToPointsAlgorithm
from .scripts.basin_analysis_algorithm import BasinAnalysisAlgorithm
from .scripts.watershed_stream import WatershedAnalysisAlgorithm
from .scripts.lines_to_ordered_points import LinesToOrderedPointsAlgorithm
from .scripts.watershed_basin import WatershedBasinDelineationAlgorithm
from .scripts.calculate_line_algorithm import CalculateLineAlgorithm
from .scripts.land_use_change_algorithm import LandUseChangeDetectionAlgorithm
from .scripts.weighted_sum_tool import WeightedSumTool
from .scripts.optimized_parcel_division import OptimizedParcelDivisionAlgorithm
from .scripts.dam_flood_simulation import DamFloodSimulationAlgorithm
from .scripts.export_to_csv import ExportToCSVAlgorithm
from .scripts.kriging_analysis import KrigingAnalysisAlgorithm
from .scripts.satellite_index_calculator import SatelliteIndexCalculatorAlgorithm
from .scripts.basemap_manager import BasemapManager
from .scripts.screen_capture import ScreenCaptureDialog, run_screen_capture
from .scripts.calculate_angles_algorithm import CalculateAnglesAlgorithm
from .scripts.global_cn_calculator import GlobalCNCalculator
from .scripts.contour_export_algorithm import ContourExportAlgorithm

class ArcGeekCalculator:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.actions = []
        self.menu = '&ArcGeek Calculator'
        self.algorithms = {}
        self.go_to_xy_dialog = None
        self.plugin_dir = os.path.dirname(__file__)
        self.context_menu_actions = []
        self.map_tool = None

    def run_basemap_manager(self):
        dialog = BasemapManager(self.iface)
        dialog.exec_()

    def run_screen_capture(self):
        run_screen_capture(self.iface)

    def initGui(self):
        self.algorithms = {
            'coordinate': CoordinateCalculatorAlgorithm(),
            'line': CalculateLineGeometryAlgorithm(),
            'polygon': CalculatePolygonGeometryAlgorithm(),
            'polygon_to_points': PolygonToPointsAlgorithm(),
            'basin_analysis': BasinAnalysisAlgorithm(),
            'watershed_stream': WatershedAnalysisAlgorithm(),
            'lines_to_ordered_points': LinesToOrderedPointsAlgorithm(),
            'watershed_basin': WatershedBasinDelineationAlgorithm(),
            'calculate_line': CalculateLineAlgorithm(),
            'land_use_change': LandUseChangeDetectionAlgorithm(),
            'weighted_sum': WeightedSumTool(),
            'optimized_parcel_division': OptimizedParcelDivisionAlgorithm(),
            'dam_flood_simulation': DamFloodSimulationAlgorithm(),
            'export_to_csv': ExportToCSVAlgorithm(),
            'kriging_analysis': KrigingAnalysisAlgorithm(),
            'satellite_index': SatelliteIndexCalculatorAlgorithm(),
            'angles': CalculateAnglesAlgorithm(),
            'global_cn': GlobalCNCalculator(),
            'contour_export': ContourExportAlgorithm(),
            'basemap_manager': BasemapManager(self.iface)
        }

        self.add_action("Calculate Point Coordinates", self.run_algorithm('coordinate'), os.path.join(self.plugin_dir, "icons/calculate_xy.png"))
        self.add_action("Calculate Line Geometry", self.run_algorithm('line'), os.path.join(self.plugin_dir, "icons/calculate_length.png"))
        self.add_action("Calculate Polygon Geometry", self.run_algorithm('polygon'), os.path.join(self.plugin_dir, "icons/calculate_area.png"))
        self.add_action("Calculate Angles", self.run_algorithm('angles'), os.path.join(self.plugin_dir, "icons/calculate_angles.png"))
        self.add_action("Extract Ordered Points from Polygons", self.run_algorithm('polygon_to_points'), os.path.join(self.plugin_dir, "icons/order_point.png"))
        self.add_action("Lines to Ordered Points", self.run_algorithm('lines_to_ordered_points'), os.path.join(self.plugin_dir, "icons/lines_to_points.png"))
        self.add_action("Azimuth and Distance from Coordinates and Table", self.run_algorithm('calculate_line'), os.path.join(self.plugin_dir, "icons/calculate_line.png"))
        self.add_action("Export to CSV (Excel compatible)", self.run_algorithm('export_to_csv'), os.path.join(self.plugin_dir, "icons/export_csv.png"))
        self.add_separator()
        self.add_action("Stream Network with Order", self.run_algorithm('watershed_stream'), os.path.join(self.plugin_dir, "icons/watershed_network.png"))
        self.add_action("Watershed Basin Delineation", self.run_algorithm('watershed_basin'), os.path.join(self.plugin_dir, "icons/watershed_basin.png"))
        self.add_action("Watershed Morphometric Analysis", self.run_algorithm('basin_analysis'), os.path.join(self.plugin_dir, "icons/watershed_morfo.png"))
        self.add_action("Global Curve Number", self.run_algorithm('global_cn'), os.path.join(self.plugin_dir, "icons/global_cn.png"))
        self.add_separator()
        self.add_action("Land Use Change Detection", self.run_algorithm('land_use_change'), os.path.join(self.plugin_dir, "icons/land_use_change.png"))
        self.add_action("Weighted Sum", self.run_algorithm('weighted_sum'), os.path.join(self.plugin_dir, "icons/weighted_sum.png"))
        self.add_action("Dam Flood Simulation", self.run_algorithm('dam_flood_simulation'), os.path.join(self.plugin_dir, "icons/dam_flood.png"))
        self.add_action("Kriging Analysis", self.run_algorithm('kriging_analysis'), os.path.join(self.plugin_dir, "icons/kriging.png"))
        self.add_separator()
        self.add_action("Export Contours to 3D CAD", self.run_algorithm('contour_export'), os.path.join(self.plugin_dir, "icons/contour_export3DCAD.png"))
        self.add_action("Optimized Parcel Division", self.run_algorithm('optimized_parcel_division'), os.path.join(self.plugin_dir, "icons/parcel_division.png"))
        self.add_separator()
        self.add_action("Manage Basemaps (Google, Bing, Esri)", self.run_basemap_manager, os.path.join(self.plugin_dir, "icons/basemap.png"))
        self.add_action("Screen Capture", self.run_screen_capture, os.path.join(self.plugin_dir, "icons/screen_capture.png"))
        self.add_action("Satellite Index Calculator", self.run_algorithm('satellite_index'), os.path.join(self.plugin_dir, "icons/satellite_index.png"))
        self.add_separator()
        self.add_action("Go to XY", self.run_go_to_xy, os.path.join(self.plugin_dir, "icons/gotoXY.png"))

        # QGIS version
        version = Qgis.QGIS_VERSION_INT

        # Disconnect previous connections before reconnecting
        try:
            self.iface.layerTreeView().contextMenuAboutToShow.disconnect(self.add_layer_menu_items)
        except:
            pass

        # For QGIS 3.0 and later versions
        if version >= 30000:
            self.iface.layerTreeView().contextMenuAboutToShow.connect(self.add_layer_menu_items)
        # For earlier versions of QGIS (if necessary)
        else:
            self.iface.layerTreeView().layerTreeContextMenuAboutToShow.connect(self.add_layer_menu_items)

        # Connect to the map canvas context menu
        self.iface.mapCanvas().contextMenuAboutToShow.connect(self.add_map_menu_items)

    def add_action(self, text, callback, icon_path=None):
        if icon_path and os.path.exists(icon_path):
            action = QAction(QIcon(icon_path), text, self.iface.mainWindow())
        else:
            action = QAction(text, self.iface.mainWindow())
        action.triggered.connect(callback)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)

    def add_separator(self):
        separator = QAction(self.iface.mainWindow())
        separator.setSeparator(True)
        self.iface.addPluginToMenu(self.menu, separator)
        self.actions.append(separator)

    def run_algorithm(self, algorithm_name):
        def callback():
            from qgis import processing
            processing.execAlgorithmDialog(self.algorithms[algorithm_name])
        return callback

    def run_go_to_xy(self):
        if self.go_to_xy_dialog is None:
            self.go_to_xy_dialog = GoToXYDialog(self.iface, self.iface.mainWindow())
        self.go_to_xy_dialog.show()

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
        if self.go_to_xy_dialog:
            self.go_to_xy_dialog.close()
            self.go_to_xy_dialog = None

        # Disconnect the layer tree context menu signal
        try:
            self.iface.layerTreeView().contextMenuAboutToShow.disconnect(self.add_layer_menu_items)
        except:
            pass

        # Disconnect the map canvas context menu signal
        try:
            self.iface.mapCanvas().contextMenuAboutToShow.disconnect(self.add_map_menu_items)
        except:
            pass

    def add_layer_menu_items(self, menu):
        # Safely clear previous actions
        for action in self.context_menu_actions[:]:
            try:
                if action in menu.actions():
                    menu.removeAction(action)
                self.context_menu_actions.remove(action)
            except RuntimeError:
                self.context_menu_actions.remove(action)
            except Exception as e:
                print(f"Error removing action: {str(e)}")

        # Get the current node
        current_node = self.iface.layerTreeView().currentNode()
        
        # Check if the current node is a layer (not a group)
        if isinstance(current_node, QgsLayerTreeNode) and current_node.nodeType() == QgsLayerTreeNode.NodeLayer:
            # Use currentLayer() method which is available in both QGIS 3.34 and 3.38
            layer = self.iface.layerTreeView().currentLayer()
            if layer and layer.type() == QgsMapLayer.VectorLayer:
                geometry_type = layer.geometryType()

                if geometry_type == QgsWkbTypes.PointGeometry:
                    action = QAction(QIcon(os.path.join(self.plugin_dir, "icons/calculate_xy.png")), "Calculate XY Coordinates", menu)
                    action.triggered.connect(lambda: self.run_algorithm('coordinate')())
                    self.add_action_to_menu(menu, action)
                elif geometry_type == QgsWkbTypes.LineGeometry:
                    action = QAction(QIcon(os.path.join(self.plugin_dir, "icons/calculate_length.png")), "Calculate Length", menu)
                    action.triggered.connect(lambda: self.run_algorithm('line')())
                    self.add_action_to_menu(menu, action)
                elif geometry_type == QgsWkbTypes.PolygonGeometry:
                    action = QAction(QIcon(os.path.join(self.plugin_dir, "icons/calculate_area.png")), "Calculate Area and Perimeter", menu)
                    action.triggered.connect(lambda: self.run_algorithm('polygon')())
                    self.add_action_to_menu(menu, action)

    def add_action_to_menu(self, menu, action):
        # Find a suitable position to insert the action
        insert_position = 0
        for i, existing_action in enumerate(menu.actions()):
            if existing_action.isSeparator() or existing_action.menu():
                insert_position = i
                break
        
        # Insert the action at the found position
        menu.insertAction(menu.actions()[insert_position] if insert_position < len(menu.actions()) else None, action)
        self.context_menu_actions.append(action)

    def add_map_menu_items(self, menu):
        action = QAction(QIcon(os.path.join(self.plugin_dir, "icons/gotoXY.png")), "Go to XY", menu)
        action.triggered.connect(self.run_go_to_xy)
        menu.addAction(action)