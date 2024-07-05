from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer, QgsProcessingParameterPoint,
                       QgsProcessingParameterCrs, QgsProcessingParameterField, QgsVectorLayer,
                       QgsRasterLayer, QgsFeature, QgsGeometry, QgsField, QgsProcessingUtils,
                       QgsWkbTypes, QgsRasterBandStats, QgsPoint, QgsPointXY, QgsFields, QgsCoordinateReferenceSystem)
import processing
import math
from .basin_processes import calculate_parameters, get_basin_area_interpretation, get_mean_slope_interpretation, \
    get_form_factor_interpretation, get_elongation_ratio_interpretation, get_circularity_ratio_interpretation, \
    get_drainage_density_interpretation, get_stream_frequency_interpretation, get_compactness_coefficient_interpretation, \
    get_length_of_overland_flow_interpretation, get_constant_channel_maintenance_interpretation, get_ruggedness_number_interpretation, \
    get_time_of_concentration_interpretation, get_bifurcation_ratio_interpretation, get_drainage_intensity_interpretation, \
    get_relief_interpretation, get_drainage_texture_interpretation, get_infiltration_number_interpretation, get_fitness_ratio_interpretation

class BasinAnalysisAlgorithm(QgsProcessingAlgorithm):
    INPUT_BASIN = 'INPUT_BASIN'
    INPUT_STREAMS = 'INPUT_STREAMS'
    INPUT_DEM = 'INPUT_DEM'
    POUR_POINT = 'POUR_POINT'
    STREAM_ORDER_FIELD = 'STREAM_ORDER_FIELD'
    OUTPUT_CRS = 'OUTPUT_CRS'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_BASIN, 'Basin layer', [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_STREAMS, 'Stream network', [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterField(self.STREAM_ORDER_FIELD, 'Field containing stream order (Strahler)', optional=False, parentLayerParameterName=self.INPUT_STREAMS))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, 'Digital Elevation Model'))
        self.addParameter(QgsProcessingParameterPoint(self.POUR_POINT, 'Pour Point (outlet)'))
        self.addParameter(QgsProcessingParameterCrs(self.OUTPUT_CRS, 'Output CRS', optional=True))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output Report', QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        # Load input layers
        basin_layer = self.parameterAsVectorLayer(parameters, self.INPUT_BASIN, context)
        streams_layer = self.parameterAsVectorLayer(parameters, self.INPUT_STREAMS, context)
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        pour_point = self.parameterAsPoint(parameters, self.POUR_POINT, context, basin_layer.crs())
        stream_order_field = self.parameterAsString(parameters, self.STREAM_ORDER_FIELD, context)
        output_crs = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)

        if not basin_layer.isValid():
            feedback.reportError('Invalid basin layer')
            return {}
        if not streams_layer.isValid():
            feedback.reportError('Invalid streams layer')
            return {}
        if not dem_layer.isValid():
            feedback.reportError('Invalid DEM layer')
            return {}

        # Ensure all layers have the same CRS
        if basin_layer.crs() != streams_layer.crs() or basin_layer.crs() != dem_layer.crs():
            feedback.reportError('Input layers have different Coordinate Reference Systems (CRS). Please ensure all layers have the same CRS.')
            return {}

        # Reproject layers if output CRS is specified
        if output_crs.isValid() and output_crs != basin_layer.crs():
            basin_layer = self.reproject_layer(basin_layer, output_crs, context, feedback)
            streams_layer = self.reproject_layer(streams_layer, output_crs, context, feedback)
            dem_layer = self.reproject_raster(dem_layer, output_crs, context, feedback)

        # Clip DEM by basin mask
        dem_clipped = self.clip_dem_by_basin(dem_layer, basin_layer, context, feedback)

        # Calculate slope
        slope_layer = self.calculate_slope(dem_clipped, context, feedback)

        # Get slope statistics
        slope_stats = self.get_slope_statistics(slope_layer, context, feedback)
        mean_slope_degrees = slope_stats['MEAN']
        mean_slope_percent = math.tan(math.radians(mean_slope_degrees)) * 100

        # Calculate morphometric parameters
        results = calculate_parameters(basin_layer, streams_layer, dem_clipped, pour_point, stream_order_field, mean_slope_degrees, feedback)
        results["Mean Slope (degrees)"] = {"value": mean_slope_degrees, "unit": "degrees", "interpretation": get_mean_slope_interpretation(mean_slope_degrees)}
        results["Mean Slope (percent)"] = {"value": mean_slope_percent, "unit": "%", "interpretation": get_mean_slope_interpretation(mean_slope_percent, percent=True)}

        # Create output layer and add calculated parameters
        fields = QgsFields()
        fields.append(QgsField("Parameter", QVariant.String))
        fields.append(QgsField("Value", QVariant.Double))
        fields.append(QgsField("Unit", QVariant.String))
        fields.append(QgsField("Interpretation", QVariant.String))
        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT, context, fields, QgsWkbTypes.Point, output_crs if output_crs.isValid() else basin_layer.crs())

        for param, details in results.items():
            feature = QgsFeature()
            feature.setFields(fields)
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(pour_point)))
            feature.setAttribute("Parameter", param)
            feature.setAttribute("Value", round(details['value'], 5))
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

    def reproject_layer(self, layer, crs, context, feedback):
        params = {
            'INPUT': layer,
            'TARGET_CRS': crs,
            'OUTPUT': 'memory:'
        }
        result = processing.run("native:reprojectlayer", params, context=context, feedback=feedback)
        return QgsVectorLayer(result['OUTPUT'], layer.name(), 'memory')

    def reproject_raster(self, raster_layer, crs, context, feedback):
        params = {
            'INPUT': raster_layer,
            'TARGET_CRS': crs,
            'RESAMPLING': 0,
            'OUTPUT': 'memory:'
        }
        result = processing.run("gdal:warpreproject", params, context=context, feedback=feedback)
        return QgsRasterLayer(result['OUTPUT'], raster_layer.name())

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

        Outputs:
            A table with calculated morphometric parameters and their interpretations
        """

    def createInstance(self):
        return BasinAnalysisAlgorithm()
