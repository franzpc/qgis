from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterField,
                       QgsProcessingParameterVectorDestination, QgsVectorLayer,
                       QgsFeature, QgsGeometry, QgsPointXY, QgsField, QgsProject,
                       QgsWkbTypes, QgsFeatureSink, QgsProcessingParameterCrs,
                       QgsFields, QgsProcessingMultiStepFeedback, QgsCoordinateReferenceSystem,
                       QgsProcessing)
from qgis.PyQt.QtCore import QVariant
import numpy as np

class CalculateLineAlgorithm(QgsProcessingAlgorithm):
    INPUT_X = 'INPUT_X'
    INPUT_Y = 'INPUT_Y'
    INPUT_TABLE = 'INPUT_TABLE'
    FIELD_DISTANCE = 'FIELD_DISTANCE'
    FIELD_ANGLE = 'FIELD_ANGLE'
    FIELD_OBSERVATIONS = 'FIELD_OBSERVATIONS'
    OUTPUT_CRS = 'OUTPUT_CRS'
    OUTPUT_LINE = 'OUTPUT_LINE'
    OUTPUT_POINTS = 'OUTPUT_POINTS'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterNumber(self.INPUT_X, 'Starting X coordinate', QgsProcessingParameterNumber.Double))
        self.addParameter(QgsProcessingParameterNumber(self.INPUT_Y, 'Starting Y coordinate', QgsProcessingParameterNumber.Double))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_TABLE, 'Input table', [QgsProcessing.TypeVector, QgsProcessing.TypeFile], optional=False))
        self.addParameter(QgsProcessingParameterField(self.FIELD_DISTANCE, 'Distance field', parentLayerParameterName=self.INPUT_TABLE, type=QgsProcessingParameterField.Any, optional=False))
        self.addParameter(QgsProcessingParameterField(self.FIELD_ANGLE, 'Angle field', parentLayerParameterName=self.INPUT_TABLE, type=QgsProcessingParameterField.Any, optional=False))
        self.addParameter(QgsProcessingParameterField(self.FIELD_OBSERVATIONS, 'Observations field', parentLayerParameterName=self.INPUT_TABLE, type=QgsProcessingParameterField.Any, optional=True))
        self.addParameter(QgsProcessingParameterCrs(self.OUTPUT_CRS, 'Output CRS', optional=False))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_LINE, 'Output line layer'))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_POINTS, 'Output points layer'))

    def processAlgorithm(self, parameters, context, feedback):
        multi_feedback = QgsProcessingMultiStepFeedback(2, feedback)
        
        x_start = self.parameterAsDouble(parameters, self.INPUT_X, context)
        y_start = self.parameterAsDouble(parameters, self.INPUT_Y, context)
        source = self.parameterAsSource(parameters, self.INPUT_TABLE, context)
        field_distance = self.parameterAsString(parameters, self.FIELD_DISTANCE, context)
        field_angle = self.parameterAsString(parameters, self.FIELD_ANGLE, context)
        field_observations = self.parameterAsString(parameters, self.FIELD_OBSERVATIONS, context)
        output_crs = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)

        # Preparar campos para la capa de líneas
        line_fields = QgsFields()
        line_fields.append(QgsField('length', QVariant.Double))

        # Preparar campos para la capa de puntos
        point_fields = QgsFields()
        point_fields.append(QgsField('ID', QVariant.Int))
        point_fields.append(QgsField('Distancia', QVariant.Double))
        point_fields.append(QgsField('Angulo', QVariant.Double))
        point_fields.append(QgsField('X', QVariant.Double))
        point_fields.append(QgsField('Y', QVariant.Double))
        if field_observations:
            point_fields.append(QgsField('Observaciones', QVariant.String))
        
        (line_sink, line_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_LINE, context,
                                                         line_fields, QgsWkbTypes.LineString, output_crs)
        (point_sink, point_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_POINTS, context,
                                                           point_fields, QgsWkbTypes.Point, output_crs)

        points = [QgsPointXY(x_start, y_start)]
        x_anterior, y_anterior = x_start, y_start
        
        # Crear punto inicial
        initial_point = QgsFeature(point_fields)
        initial_point.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x_start, y_start)))
        initial_attributes = [0, 0, 0, x_start, y_start]
        if field_observations:
            initial_attributes.append('')
        initial_point.setAttributes(initial_attributes)
        point_sink.addFeature(initial_point, QgsFeatureSink.FastInsert)
        
        features = source.getFeatures()
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            try:
                distancia = float(feature[field_distance])
                angulo_grados = float(feature[field_angle])
                angulo_radianes = np.radians(angulo_grados)
                x_actual = x_anterior + distancia * np.sin(angulo_radianes)
                y_actual = y_anterior + distancia * np.cos(angulo_radianes)
                new_point = QgsPointXY(x_actual, y_actual)
                points.append(new_point)
                
                # Crear punto
                point_feature = QgsFeature(point_fields)
                point_feature.setGeometry(QgsGeometry.fromPointXY(new_point))
                point_attributes = [current + 1, distancia, angulo_grados, x_actual, y_actual]
                if field_observations:
                    point_attributes.append(feature[field_observations])
                point_feature.setAttributes(point_attributes)
                point_sink.addFeature(point_feature, QgsFeatureSink.FastInsert)
                
                # Crear segmento de línea
                line_feature = QgsFeature(line_fields)
                line_geom = QgsGeometry.fromPolylineXY([QgsPointXY(x_anterior, y_anterior), new_point])
                length = line_geom.length()
                line_feature.setGeometry(line_geom)
                line_feature.setAttributes([length])
                line_sink.addFeature(line_feature, QgsFeatureSink.FastInsert)
                
                x_anterior, y_anterior = x_actual, y_actual
                
            except ValueError as e:
                feedback.reportError(f"Error en la fila {current + 1}: {str(e)}")
                continue

            feedback.setProgress(int(current * total))

        return {self.OUTPUT_LINE: line_dest_id, self.OUTPUT_POINTS: point_dest_id}

    def name(self):
        return 'calculatelinefromcoordinatesandtable'

    def displayName(self):
        return 'Calculate Line from Coordinates and Table'

    def group(self):
        return 'ArcGeek Calculator'

    def groupId(self):
        return 'arcgeek_calculator'

    def shortHelpString(self):
        return """
        This algorithm calculates a line and points from starting coordinates and a table of distances and angles.

        Parameters:
        - Starting X and Y coordinates: The initial point of the line.
        - Input table: A vector layer or table (csv, txt, etc) containing distance and angle data.
        - Distance field: The field in the input table containing distance values.
        - Angle field: The field in the input table containing angle values.
        - Observations field (optional): A field for additional information about each point.
        - Output CRS: The coordinate reference system for the output layers.

        Outputs:
        - A line layer with segments connecting the calculated points.
        - A point layer with all calculated points.

        The algorithm reads the input table row by row, calculating new points based on the distance and angle from the previous point. It starts from the given X and Y coordinates and creates a new point for each row in the table.

        Use this tool when you need to:
        - Convert tabular distance and angle data into spatial features.
        - Generate a line path from a series of movements.
        - Create point locations from relative positioning data.

        Note: Ensure that you select the correct CRS for your data and that appropriate coordinate transformations are set up in your project properties to avoid potential inaccuracies in the results.
        """

    def createInstance(self):
        return CalculateLineAlgorithm()