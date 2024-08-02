from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer, 
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterPoint, 
                       QgsProcessingParameterCrs, QgsCoordinateReferenceSystem, 
                       QgsWkbTypes, QgsField, QgsProcessingUtils, QgsFields, 
                       QgsVectorLayer, QgsProject, QgsFeatureSink, QgsProcessing, QgsFeature,
                       QgsProcessingParameterVectorLayer, QgsProcessingException,
                       QgsProcessingParameterNumber)
from qgis.PyQt.QtCore import QVariant, QCoreApplication
import processing

class WatershedBasinDelineationAlgorithm(QgsProcessingAlgorithm):
    INPUT_DEM = 'INPUT_DEM'
    POUR_POINT = 'POUR_POINT'
    INPUT_STREAM = 'INPUT_STREAM'
    OUTPUT_BASIN = 'OUTPUT_BASIN'
    OUTPUT_STREAM = 'OUTPUT_STREAM'
    OUTPUT_CRS = 'OUTPUT_CRS'
    SMOOTH_ITERATIONS = 'SMOOTH_ITERATIONS'
    SMOOTH_OFFSET = 'SMOOTH_OFFSET'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, 'Input DEM'))
        self.addParameter(QgsProcessingParameterPoint(self.POUR_POINT, 'Pour Point'))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_STREAM, 'Input Stream Network', 
                                                            types=[QgsProcessing.TypeVectorLine], optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.SMOOTH_ITERATIONS, 'Smoothing Iterations', 
                                                       type=QgsProcessingParameterNumber.Integer, 
                                                       minValue=0, maxValue=10, defaultValue=2))
        self.addParameter(QgsProcessingParameterNumber(self.SMOOTH_OFFSET, 'Smoothing Offset', 
                                                       type=QgsProcessingParameterNumber.Double, 
                                                       minValue=0.0, maxValue=0.5, defaultValue=0.25))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_BASIN, 'Output Basin', QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_STREAM, 'Output Basin Stream Network', QgsProcessing.TypeVectorLine, optional=True))
        self.addParameter(QgsProcessingParameterCrs(self.OUTPUT_CRS, 'Output CRS', optional=True))

    def processAlgorithm(self, parameters, context, feedback):
        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        pour_point = self.parameterAsPoint(parameters, self.POUR_POINT, context)
        input_stream = self.parameterAsVectorLayer(parameters, self.INPUT_STREAM, context)
        output_crs = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)
        smooth_iterations = self.parameterAsInt(parameters, self.SMOOTH_ITERATIONS, context)
        smooth_offset = self.parameterAsDouble(parameters, self.SMOOTH_OFFSET, context)

        if not dem.isValid():
            raise QgsProcessingException(self.tr('Invalid input DEM'))

        if input_stream and input_stream.geometryType() != QgsWkbTypes.LineGeometry:
            raise QgsProcessingException(self.tr('Input Stream Network must be a line layer'))

        # Step 1: Fill sinks
        filled_dem = processing.run('grass7:r.fill.dir', {
            'input': dem,
            'format': 0,
            'output': 'TEMPORARY_OUTPUT',
            'direction': 'TEMPORARY_OUTPUT',
            'areas': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback)['output']

        # Step 2: Calculate flow direction and accumulation
        watershed_result = processing.run('grass7:r.watershed', {
            'elevation': filled_dem,
            'convergence': 5,
            'memory': 300,
            '-s': True,
            'accumulation': 'TEMPORARY_OUTPUT',
            'drainage': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback)
        
        drainage = watershed_result['drainage']

        # Step 3: Delineate watershed
        pour_point_str = f'{pour_point.x()},{pour_point.y()}'
        basin_raster = processing.run('grass7:r.water.outlet', {
            'input': drainage,
            'coordinates': pour_point_str,
            'output': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback)['output']

        # Step 4: Convert raster basin to vector
        basin_vector = processing.run('grass7:r.to.vect', {
            'input': basin_raster,
            'type': 2,  # area
            'column': 'value',
            '-s': True,
            'output': 'TEMPORARY_OUTPUT',
            'GRASS_OUTPUT_TYPE_PARAMETER': 3  # auto
        }, context=context, feedback=feedback)['output']

        # Step 5: Apply smoothing to the basin
        smoothed_basin = processing.run('native:smoothgeometry', {
            'INPUT': basin_vector,
            'ITERATIONS': smooth_iterations,
            'OFFSET': smooth_offset,
            'MAX_ANGLE': 180,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']

        # Load the vector layer
        basin_layer = smoothed_basin  # smoothed_basin is already a QgsVectorLayer

        # Reproject the output if necessary
        if output_crs.isValid() and output_crs != basin_layer.crs():
            reprojected = processing.run('native:reprojectlayer', {
                'INPUT': basin_layer,
                'TARGET_CRS': output_crs,
                'OUTPUT': 'memory:'
            }, context=context, feedback=feedback)['OUTPUT']
            basin_layer = reprojected

        # Save the basin result
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT_BASIN, context,
                                               basin_layer.fields(), QgsWkbTypes.Polygon, basin_layer.crs())
        
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_BASIN))

        features = basin_layer.getFeatures()
        for feature in features:
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        results = {self.OUTPUT_BASIN: dest_id}

        # Process input stream network if provided
        if input_stream:
            clipped_stream = processing.run('native:clip', {
                'INPUT': input_stream,
                'OVERLAY': basin_layer,
                'OUTPUT': 'memory:'
            }, context=context, feedback=feedback)['OUTPUT']

            # Save the clipped stream result
            (stream_sink, stream_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_STREAM, context,
                                                                 clipped_stream.fields(), QgsWkbTypes.LineString, clipped_stream.crs())
            
            if stream_sink is None:
                raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_STREAM))

            stream_features = clipped_stream.getFeatures()
            for feature in stream_features:
                stream_sink.addFeature(feature, QgsFeatureSink.FastInsert)

            results[self.OUTPUT_STREAM] = stream_dest_id

        return results

    def name(self):
        return 'watershedbasindelineation'

    def displayName(self):
        return self.tr('Watershed Basin Delineation')

    def group(self):
        return self.tr('ArcGeek Calculator')

    def groupId(self):
        return 'arcgeekcalculator'

    def createInstance(self):
        return WatershedBasinDelineationAlgorithm()

    def shortHelpString(self):
        return self.tr("""
        This algorithm delineates a watershed basin based on a Digital Elevation Model (DEM) and a pour point.
        It uses GRASS GIS algorithms for hydrological analysis and watershed delineation.
        
        Parameters:
            Input DEM: A raster layer representing the terrain elevation
            Pour Point: The outlet point of the watershed
            Input Stream Network: Optional. A line vector layer representing the stream network
            Smoothing Iterations: Number of iterations for smoothing the basin boundary (0-10)
            Smoothing Offset: Offset value for smoothing (0.0-0.5)
            Output CRS: Optional. The coordinate reference system for the output
        
        Outputs:
            Output Basin: A polygon layer representing the delineated watershed basin
            Output Basin Stream Network: Optional. A line layer representing the clipped stream network within the basin
        
        The algorithm performs the following steps:
        1. Fills sinks in the DEM
        2. Calculates flow direction and accumulation
        3. Delineates the watershed based on the pour point
        4. Converts the raster watershed to a vector polygon
        5. Applies smoothing to the basin boundary
        6. Clips the input stream network to the basin boundary (if provided)
        
        Note: The accuracy of the watershed delineation depends on the resolution and quality of the input DEM.
        """)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)