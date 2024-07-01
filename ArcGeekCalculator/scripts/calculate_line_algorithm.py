from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterNumber,
                       QgsProcessingParameterFile, QgsProcessingParameterField,
                       QgsProcessingParameterVectorDestination, QgsVectorLayer,
                       QgsFeature, QgsGeometry, QgsPointXY, QgsField, QgsProject,
                       QgsWkbTypes, QgsFeatureSink, QgsProcessingParameterCrs,
                       QgsFields, QgsProcessingMultiStepFeedback, QgsCoordinateReferenceSystem)
from qgis.PyQt.QtCore import QVariant
import numpy as np
import csv

class CalculateLineAlgorithm(QgsProcessingAlgorithm):
    INPUT_X = 'INPUT_X'
    INPUT_Y = 'INPUT_Y'
    INPUT_TABLE = 'INPUT_TABLE'
    FIELD_DISTANCE = 'FIELD_DISTANCE'
    FIELD_ANGLE = 'FIELD_ANGLE'
    OUTPUT_CRS = 'OUTPUT_CRS'
    OUTPUT_LINE = 'OUTPUT_LINE'
    OUTPUT_POINTS = 'OUTPUT_POINTS'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterNumber(self.INPUT_X, 'Starting X coordinate', QgsProcessingParameterNumber.Double))
        self.addParameter(QgsProcessingParameterNumber(self.INPUT_Y, 'Starting Y coordinate', QgsProcessingParameterNumber.Double))
        self.addParameter(QgsProcessingParameterFile(self.INPUT_TABLE, 'Input table', extension='csv'))
        self.addParameter(QgsProcessingParameterField(self.FIELD_DISTANCE, 'Distance field', parentLayerParameterName=self.INPUT_TABLE, type=QgsProcessingParameterField.Any))
        self.addParameter(QgsProcessingParameterField(self.FIELD_ANGLE, 'Angle field', parentLayerParameterName=self.INPUT_TABLE, type=QgsProcessingParameterField.Any))
        self.addParameter(QgsProcessingParameterCrs(self.OUTPUT_CRS, 'Output CRS', optional=True))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_LINE, 'Output line layer'))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_POINTS, 'Output points layer'))

    def processAlgorithm(self, parameters, context, feedback):
        multi_feedback = QgsProcessingMultiStepFeedback(2, feedback)
        
        x_start = self.parameterAsDouble(parameters, self.INPUT_X, context)
        y_start = self.parameterAsDouble(parameters, self.INPUT_Y, context)
        input_file = self.parameterAsFile(parameters, self.INPUT_TABLE, context)
        field_distance = self.parameterAsString(parameters, self.FIELD_DISTANCE, context)
        field_angle = self.parameterAsString(parameters, self.FIELD_ANGLE, context)
        output_crs = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)
        
        if not output_crs.isValid():
            feedback.pushInfo('No CRS selected. Using the project CRS.')
            output_crs = context.project().crs()

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
        
        (line_sink, line_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_LINE, context,
                                                         line_fields, QgsWkbTypes.LineString, output_crs)
        (point_sink, point_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_POINTS, context,
                                                           point_fields, QgsWkbTypes.Point, output_crs)

        points = [QgsPointXY(x_start, y_start)]
        x_anterior, y_anterior = x_start, y_start
        
        # Crear punto inicial
        initial_point = QgsFeature(point_fields)
        initial_point.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x_start, y_start)))
        initial_point.setAttributes([0, 0, 0, x_start, y_start])
        point_sink.addFeature(initial_point, QgsFeatureSink.FastInsert)
        
        with open(input_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for id_punto, row in enumerate(reader, start=1):
                try:
                    distancia = float(row[field_distance])
                    angulo_grados = float(row[field_angle])
                    angulo_radianes = np.radians(angulo_grados)
                    x_actual = x_anterior + distancia * np.sin(angulo_radianes)
                    y_actual = y_anterior + distancia * np.cos(angulo_radianes)
                    new_point = QgsPointXY(x_actual, y_actual)
                    points.append(new_point)
                    
                    # Crear punto
                    point_feature = QgsFeature(point_fields)
                    point_feature.setGeometry(QgsGeometry.fromPointXY(new_point))
                    point_feature.setAttributes([id_punto, distancia, angulo_grados, x_actual, y_actual])
                    point_sink.addFeature(point_feature, QgsFeatureSink.FastInsert)
                    
                    # Crear segmento de línea
                    line_feature = QgsFeature(line_fields)
                    line_geom = QgsGeometry.fromPolylineXY([QgsPointXY(x_anterior, y_anterior), new_point])
                    length = line_geom.length()
                    line_feature.setGeometry(line_geom)
                    line_feature.setAttributes([length])
                    line_sink.addFeature(line_feature, QgsFeatureSink.FastInsert)
                    
                    x_anterior, y_anterior = x_actual, y_actual
                    
                    if feedback.isCanceled():
                        break
                except ValueError as e:
                    feedback.reportError(f"Error en la fila {id_punto}: {str(e)}")
                    continue

        return {self.OUTPUT_LINE: line_dest_id, self.OUTPUT_POINTS: point_dest_id}

    def name(self):
        return 'calculatelinefromcoordinatesandtable'

    def displayName(self):
        return 'Calculate Line from Coordinates and Table'

    def group(self):
        return 'ArcGeek Calculator'

    def groupId(self):
        return 'arcgeek_calculator'

    def createInstance(self):
        return CalculateLineAlgorithm()