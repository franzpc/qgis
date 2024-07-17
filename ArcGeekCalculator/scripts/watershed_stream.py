import os
import tempfile
import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber, QgsProcessingParameterFeatureSink,
                       QgsVectorLayer, QgsRasterLayer, QgsField, QgsWkbTypes, QgsProcessingParameterCrs, 
                       QgsProcessingException, QgsFeatureSink, QgsSpatialIndex)

class WatershedAnalysisAlgorithm(QgsProcessingAlgorithm):
    INPUT_DEM = 'INPUT_DEM'
    THRESHOLD = 'THRESHOLD'
    OUTPUT_CRS = 'OUTPUT_CRS'
    OUTPUT_STREAMS = 'OUTPUT_STREAMS'
    SMOOTH_ITERATIONS = 'SMOOTH_ITERATIONS'
    SMOOTH_OFFSET = 'SMOOTH_OFFSET'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, 'Input DEM'))
        self.addParameter(QgsProcessingParameterNumber(self.THRESHOLD, 'Flow Accumulation Threshold', 
                                                       type=QgsProcessingParameterNumber.Integer, minValue=0, defaultValue=1000))
        self.addParameter(QgsProcessingParameterCrs(self.OUTPUT_CRS, 'Output CRS', optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.SMOOTH_ITERATIONS, 'Smooth Iterations',
                                                       type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=1))
        self.addParameter(QgsProcessingParameterNumber(self.SMOOTH_OFFSET, 'Smooth Offset',
                                                       type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=0.5, defaultValue=0.25))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_STREAMS, 'Output Stream Network'))

    def processAlgorithm(self, parameters, context, feedback):
        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if not dem.isValid():
            raise QgsProcessingException(self.tr('Invalid input DEM'))
        
        threshold = self.parameterAsInt(parameters, self.THRESHOLD, context)
        output_crs = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)
        smooth_iterations = self.parameterAsInt(parameters, self.SMOOTH_ITERATIONS, context)
        smooth_offset = self.parameterAsDouble(parameters, self.SMOOTH_OFFSET, context)
        
        if output_crs.isValid() and output_crs != dem.crs():
            dem = self.reproject_raster(dem, output_crs, context, feedback)
        
        temp_dir = tempfile.mkdtemp()
        
        filled_dem = processing.run("grass7:r.fill.dir", {
            'input': dem,
            'output': os.path.join(temp_dir, 'filled_dem.tif'),
            'direction': os.path.join(temp_dir, 'flow_direction.tif'),
            'areas': os.path.join(temp_dir, 'problem_areas.tif'),
            'format': 0
        }, context=context, feedback=feedback)['output']
        
        flow_accumulation = processing.run("grass7:r.watershed", {
            'elevation': filled_dem,
            'accumulation': os.path.join(temp_dir, 'flow_accumulation.tif'),
            'drainage': os.path.join(temp_dir, 'drainage_direction.tif'),
            'threshold': dem.rasterUnitsPerPixelX(),
            '-s': True,
            '-m': True
        }, context=context, feedback=feedback)['accumulation']
        
        streams = processing.run("grass7:r.stream.extract", {
            'elevation': filled_dem,
            'accumulation': flow_accumulation,
            'threshold': threshold,
            'stream_vector': os.path.join(temp_dir, 'streams.gpkg'),
            'stream_raster': os.path.join(temp_dir, 'streams.tif'),
            'direction': os.path.join(temp_dir, 'stream_direction.tif'),
            'GRASS_OUTPUT_TYPE_PARAMETER': 2
        }, context=context, feedback=feedback)['stream_vector']
        
        # Apply smoothing
        smoothed_streams = processing.run("native:smoothgeometry", {
            'INPUT': streams,
            'ITERATIONS': smooth_iterations,
            'OFFSET': smooth_offset,
            'MAX_ANGLE': 180,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']
        
        ordered_streams = self.calculate_stream_orders(smoothed_streams, context, feedback)
        
        stream_sink, stream_dest_id = self.parameterAsSink(parameters, self.OUTPUT_STREAMS, context,
                                                           ordered_streams.fields(), QgsWkbTypes.LineString, dem.crs())
        if stream_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_STREAMS))
        
        for f in ordered_streams.getFeatures():
            stream_sink.addFeature(f, QgsFeatureSink.FastInsert)
        
        return {self.OUTPUT_STREAMS: stream_dest_id}

    def calculate_stream_orders(self, stream_layer, context, feedback):
        if isinstance(stream_layer, str):
            layer = QgsVectorLayer(stream_layer, "Streams", "ogr")
        elif isinstance(stream_layer, QgsVectorLayer):
            layer = stream_layer
        else:
            raise QgsProcessingException(self.tr('Invalid stream layer type'))
        
        if not layer.isValid():
            raise QgsProcessingException(self.tr('Invalid stream layer'))
        
        layer_provider = layer.dataProvider()
        
        # Add Strahler and Shreve order fields if they don't exist
        fields_to_add = []
        if layer.fields().indexFromName("Strahler") == -1:
            fields_to_add.append(QgsField("Strahler", QVariant.Int))
        if layer.fields().indexFromName("Shreve") == -1:
            fields_to_add.append(QgsField("Shreve", QVariant.Int))
        
        if fields_to_add:
            layer_provider.addAttributes(fields_to_add)
            layer.updateFields()
        
        index = QgsSpatialIndex(layer.getFeatures())
        outlets = [f for f in layer.getFeatures() if not self.find_downstream_features(f, index, layer)]
        
        layer.startEditing()
        for outlet in outlets:
            self.get_stream_orders(outlet, layer, index)
        layer.commitChanges()
        return layer

    def get_stream_orders(self, feature, layer, index):
        upstream_features = self.find_upstream_features(feature, index, layer)
        if not upstream_features:
            feature['Strahler'] = 1
            feature['Shreve'] = 1
            layer.updateFeature(feature)
            return 1, 1
        else:
            upstream_orders = [self.get_stream_orders(f, layer, index) for f in upstream_features]
            max_strahler = max([order[0] for order in upstream_orders])
            strahler = max_strahler + 1 if [order[0] for order in upstream_orders].count(max_strahler) > 1 else max_strahler
            shreve = sum([order[1] for order in upstream_orders])
            feature['Strahler'] = strahler
            feature['Shreve'] = shreve
            layer.updateFeature(feature)
            return strahler, shreve

    def find_upstream_features(self, feature, index, layer):
        start_point = feature.geometry().asPolyline()[0]
        return [layer.getFeature(fid) for fid in index.nearestNeighbor(start_point, 5) if fid != feature.id() and layer.getFeature(fid).geometry().asPolyline()[-1] == start_point]

    def find_downstream_features(self, feature, index, layer):
        end_point = feature.geometry().asPolyline()[-1]
        return [layer.getFeature(fid) for fid in index.nearestNeighbor(end_point, 5) if fid != feature.id() and layer.getFeature(fid).geometry().asPolyline()[0] == end_point]

    def reproject_raster(self, raster_layer, crs, context, feedback):
        result = processing.run("gdal:warpreproject", {
            'INPUT': raster_layer,
            'TARGET_CRS': crs,
            'RESAMPLING': 0,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        return QgsRasterLayer(result['OUTPUT'], raster_layer.name())

    def name(self): return 'watershedanalysiswithsmooth'
    def displayName(self): return self.tr('Stream Network with Order')
    def group(self): return self.tr('Hydrology')
    def groupId(self): return 'hydrology'
    def shortHelpString(self): return self.tr("""
        This algorithm generates a stream network, applies smoothing, and calculates both Strahler and Shreve stream orders.
        It uses GRASS GIS algorithms for stream extraction, QGIS native smooth algorithm, and implements custom Strahler and Shreve order calculations.
        Parameters:
            Input DEM: A raster layer representing the terrain elevation
            Flow Accumulation Threshold: Minimum number of cells to form a stream
            Output CRS: Optional. The coordinate reference system for the output
            Smooth Iterations: Number of smoothing iterations to apply
            Smooth Offset: Controls the smoothness of the output
        Outputs:
            Output Stream Network: A line layer representing the smoothed stream network with Strahler and Shreve orders
        """)
    def createInstance(self): return WatershedAnalysisAlgorithm()
    def tr(self, string): return QCoreApplication.translate('Processing', string)