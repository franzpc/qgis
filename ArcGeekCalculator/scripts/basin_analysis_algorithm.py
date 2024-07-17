from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer, QgsProcessingParameterPoint,
                       QgsProcessingParameterCrs, QgsProcessingParameterField, QgsVectorLayer,
                       QgsRasterLayer, QgsFeature, QgsGeometry, QgsField, QgsProcessingUtils,
                       QgsWkbTypes, QgsRasterBandStats, QgsPoint, QgsPointXY, QgsFields, 
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject,
                       QgsProcessingParameterNumber)
from qgis.gui import QgsMapToolEmitPoint, QgsMapCanvas
import processing
import math
from .basin_processes import calculate_parameters, get_basin_area_interpretation, get_mean_slope_interpretation

class BasinAnalysisAlgorithm(QgsProcessingAlgorithm):
    INPUT_BASIN = 'INPUT_BASIN'
    INPUT_STREAMS = 'INPUT_STREAMS'
    INPUT_DEM = 'INPUT_DEM'
    POUR_POINT = 'POUR_POINT'
    STREAM_ORDER_FIELD = 'STREAM_ORDER_FIELD'
    OUTPUT_CRS = 'OUTPUT_CRS'
    PRECISION = 'PRECISION'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_BASIN, 'Basin layer', [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_STREAMS, 'Stream network', [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterField(self.STREAM_ORDER_FIELD, 'Field containing stream order (Strahler)', optional=False, parentLayerParameterName=self.INPUT_STREAMS))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, 'Digital Elevation Model'))
        self.addParameter(QgsProcessingParameterPoint(self.POUR_POINT, 'Pour Point (outlet)', optional=False))
        self.addParameter(QgsProcessingParameterCrs(self.OUTPUT_CRS, 'Output CRS', optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.PRECISION, 'Decimal precision', type=QgsProcessingParameterNumber.Integer, minValue=0, maxValue=15, defaultValue=4))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output Report', QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        basin_layer = self.parameterAsVectorLayer(parameters, self.INPUT_BASIN, context)
        streams_layer = self.parameterAsVectorLayer(parameters, self.INPUT_STREAMS, context)
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        pour_point = self.parameterAsPoint(parameters, self.POUR_POINT, context, basin_layer.crs())
        stream_order_field = self.parameterAsString(parameters, self.STREAM_ORDER_FIELD, context)
        output_crs = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)
        precision = self.parameterAsInt(parameters, self.PRECISION, context)

        if not basin_layer.isValid() or not streams_layer.isValid() or not dem_layer.isValid():
            feedback.reportError('One or more input layers are invalid')
            return {}

        if basin_layer.crs() != streams_layer.crs() or basin_layer.crs() != dem_layer.crs():
            feedback.reportError('Input layers have different Coordinate Reference Systems (CRS). Please ensure all layers have the same CRS.')
            return {}

        calculation_crs = basin_layer.crs()

        dem_clipped = self.clip_dem_by_basin(dem_layer, basin_layer, context, feedback)
        slope_layer = self.calculate_slope(dem_clipped, context, feedback)
        slope_stats = self.get_slope_statistics(slope_layer, context, feedback)
        
        mean_slope_degrees = slope_stats['MEAN']
        mean_slope_percent = math.tan(math.radians(mean_slope_degrees)) * 100

        results = calculate_parameters(basin_layer, streams_layer, dem_clipped, pour_point, stream_order_field, mean_slope_degrees, feedback)
        results["Mean Slope (degrees)"] = {"value": mean_slope_degrees, "unit": "degrees", "interpretation": get_mean_slope_interpretation(mean_slope_degrees)}
        results["Mean Slope (percent)"] = {"value": mean_slope_percent, "unit": "%", "interpretation": get_mean_slope_interpretation(mean_slope_percent, percent=True)}

        fields = QgsFields()
        fields.append(QgsField("Parameter", QVariant.String))
        fields.append(QgsField("Value", QVariant.Double))
        fields.append(QgsField("Unit", QVariant.String))
        fields.append(QgsField("Interpretation", QVariant.String))

        sink_crs = output_crs if output_crs.isValid() else calculation_crs
        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT, context, fields, QgsWkbTypes.Point, sink_crs)

        transform = QgsCoordinateTransform(calculation_crs, sink_crs, QgsProject.instance()) if sink_crs != calculation_crs else None

        for param, details in results.items():
            feature = QgsFeature()
            feature.setFields(fields)
            
            point = transform.transform(pour_point) if transform else pour_point
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            
            feature.setAttribute("Parameter", param)
            feature.setAttribute("Value", round(details['value'], precision))
            feature.setAttribute("Unit", details['unit'])
            feature.setAttribute("Interpretation", details['interpretation'])
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

    def clip_dem_by_basin(self, dem_layer, basin_layer, context, feedback):
        params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': False,
            'INPUT': dem_layer,
            'MASK': basin_layer,
            'NODATA': None,
            'OPTIONS': '',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }
        result = processing.run("gdal:cliprasterbymasklayer", params, context=context, feedback=feedback)
        return QgsRasterLayer(result['OUTPUT'], 'Clipped DEM')

    def calculate_slope(self, dem_layer, context, feedback):
        params = {
            'INPUT': dem_layer,
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'Z_FACTOR': 1
        }
        result = processing.run("gdal:slope", params, context=context, feedback=feedback)
        return QgsRasterLayer(result['OUTPUT'], 'Slope')

    def get_slope_statistics(self, slope_layer, context, feedback):
        params = {
            'BAND': 1,
            'INPUT': slope_layer,
            'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
        }
        return processing.run("qgis:rasterlayerstatistics", params, context=context, feedback=feedback)

    def createCustomParametersWidgets(self, wrapper):
        from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
        from qgis.PyQt.QtCore import Qt

        def canvasClicked(point, button):
            wrapper.setParameterValue(self.POUR_POINT, point)
            canvas.unsetMapTool(mapTool)
            QApplication.restoreOverrideCursor()
            rubberBand.reset()

        canvas = wrapper.dialog().findChild(QgsMapCanvas)
        mapTool = QgsMapToolEmitPoint(canvas)
        mapTool.canvasClicked.connect(canvasClicked)
        
        rubberBand = QgsRubberBand(canvas, QgsWkbTypes.PointGeometry)
        rubberBand.setColor(Qt.red)
        rubberBand.setWidth(3)
        
        def canvasMoveEvent(e):
            rubberBand.reset()
            rubberBand.addPoint(e.mapPoint())

        mapTool.canvasMoveEvent = canvasMoveEvent
        
        canvas.setMapTool(mapTool)
        QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))

        return []

    def name(self):
        return 'basinanalysis'

    def displayName(self):
        return 'Watershed Morphometric Analysis'

    def group(self):
        return 'ArcGeek Calculator'

    def groupId(self):
        return 'arcgeekcalculator'

    def shortHelpString(self):
        return """
        This algorithm performs a comprehensive analysis of a hydrological basin.
        It calculates various morphometric parameters and provides interpretations.

        Parameters:
            Basin layer: A polygon layer representing the basin boundary
            Stream network: A line layer representing the stream network within the basin
            Stream Order Field: Field containing stream order (Strahler)
            Digital Elevation Model: A raster layer representing the terrain elevation
            Pour Point: A point representing the basin outlet
            Output CRS: Optional. The coordinate reference system for the output
            Decimal precision: Number of decimal places for the results (default: 4)

        Outputs:
            A table with calculated morphometric parameters and their interpretations

        Note: All input layers must have the same Coordinate Reference System (CRS).
        """

    def createInstance(self):
        return BasinAnalysisAlgorithm()