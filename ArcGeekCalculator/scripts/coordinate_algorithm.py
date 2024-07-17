from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource, 
                       QgsProcessingParameterBoolean, QgsProcessingParameterVectorDestination, 
                       QgsProcessing, QgsProcessingException, QgsField, edit, QgsVectorLayer, 
                       QgsFeatureRequest, QgsVectorFileWriter, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject, QgsProcessingProvider,
                       QgsProcessingParameterNumber, QgsProcessingParameterCrs)
from qgis.PyQt.QtCore import QVariant
import traceback

class CoordinateCalculatorAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    MODIFY = 'MODIFY'
    OUTPUT = 'OUTPUT'
    CALCULATE_XY = 'CALCULATE_XY'
    FORMAT_DD = 'FORMAT_DD'
    FORMAT_DMS = 'FORMAT_DMS'
    FORMAT_DMS2 = 'FORMAT_DMS2'
    PRECISION = 'PRECISION'
    CRS = 'CRS'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                'Input layer',
                [QgsProcessing.TypeVectorPoint]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.MODIFY,
                'Modify the current layer',
                defaultValue=False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                'Output layer',
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CALCULATE_XY,
                'Calculate XY',
                defaultValue=True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FORMAT_DD,
                'Decimal Degrees',
                defaultValue=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FORMAT_DMS,
                'Degrees Minutes Seconds (DDD° MM\' SSS.ss" <N|S|E|W>)',
                defaultValue=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FORMAT_DMS2,
                'Degrees Minutes Seconds (<N|S|E|W> DDD° MM\' SSS.ss")',
                defaultValue=False
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.PRECISION,
                'Precision',
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                maxValue=15,
                defaultValue=2
            )
        )

        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                'CRS for calculations',
                optional=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        try:
            source = self.parameterAsSource(parameters, self.INPUT, context)
            if not source:
                raise QgsProcessingException("Input layer could not be loaded")

            modify_layer = self.parameterAsBool(parameters, self.MODIFY, context)
            calculate_xy = self.parameterAsBool(parameters, self.CALCULATE_XY, context)
            format_dd = self.parameterAsBool(parameters, self.FORMAT_DD, context)
            format_dms = self.parameterAsBool(parameters, self.FORMAT_DMS, context)
            format_dms2 = self.parameterAsBool(parameters, self.FORMAT_DMS2, context)
            precision = self.parameterAsInt(parameters, self.PRECISION, context)
            crs = self.parameterAsCrs(parameters, self.CRS, context)

            if not crs.isValid():
                crs = source.sourceCrs()

            if modify_layer:
                target_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
            else:
                target_layer = QgsVectorLayer("Point?crs={}".format(source.sourceCrs().authid()), "TemporaryLayer", "memory")
                target_layer.startEditing()
                target_layer.dataProvider().addAttributes(source.fields().toList())
                target_layer.updateFields()

                for feature in source.getFeatures():
                    target_layer.addFeature(feature)
                target_layer.commitChanges()

            if not target_layer.fields():
                raise QgsProcessingException("The layer has no fields.")

            # Add new fields
            with edit(target_layer):
                if calculate_xy and (target_layer.fields().lookupField('X') == -1 or target_layer.fields().lookupField('Y') == -1):
                    target_layer.addAttribute(QgsField('X', QVariant.Double, prec=precision))
                    target_layer.addAttribute(QgsField('Y', QVariant.Double, prec=precision))
                if format_dd and (target_layer.fields().lookupField('DD_Lat') == -1 or target_layer.fields().lookupField('DD_Lon') == -1):
                    target_layer.addAttribute(QgsField('DD_Lat', QVariant.Double, prec=precision))
                    target_layer.addAttribute(QgsField('DD_Lon', QVariant.Double, prec=precision))
                if format_dms and (target_layer.fields().lookupField('DMS_Lat') == -1 or target_layer.fields().lookupField('DMS_Lon') == -1):
                    target_layer.addAttribute(QgsField('DMS_Lat', QVariant.String))
                    target_layer.addAttribute(QgsField('DMS_Lon', QVariant.String))
                if format_dms2 and (target_layer.fields().lookupField('Lat_DMS') == -1 or target_layer.fields().lookupField('Lon_DMS') == -1):
                    target_layer.addAttribute(QgsField('Lat_DMS', QVariant.String))
                    target_layer.addAttribute(QgsField('Lon_DMS', QVariant.String))

            calculate_coordinates(target_layer, calculate_xy, format_dd, format_dms, format_dms2, precision, crs, feedback)

            if not modify_layer:
                output_file = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
                result = QgsVectorFileWriter.writeAsVectorFormat(target_layer, output_file, "utf-8", target_layer.crs(), "GPKG")
                if result[0] != QgsVectorFileWriter.NoError:
                    raise QgsProcessingException(f"Error writing output: {result[1]}")
                return {self.OUTPUT: output_file}

            return {self.OUTPUT: target_layer.id()}

        except Exception as e:
            feedback.reportError(f"Error in processAlgorithm: {str(e)}", fatalError=True)
            feedback.pushInfo(traceback.format_exc())
            raise

    def name(self):
        return 'coordinate_calculator'

    def displayName(self):
        return 'Calculate Coordinates'

    def group(self):
        return 'ArcGeek Calculator'

    def groupId(self):
        return 'arcgeek_calculator'

    def shortHelpString(self):
        return """
        This algorithm calculates and adds coordinate information to a point layer in various formats.

        Parameters:
        - Input layer: The point layer to process.
        - Modify the current layer: If checked, modifies the input layer. Otherwise, creates a new layer.
        - Calculate XY: Adds X and Y fields with coordinates in the specified CRS.
        - Decimal Degrees: Adds latitude and longitude fields in decimal degrees.
        - Degrees Minutes Seconds (DDD° MM' SSS.ss" <N|S|E|W>): Adds fields with coordinates in DMS format.
        - Degrees Minutes Seconds (<N|S|E|W> DDD° MM' SSS.ss"): Adds fields with coordinates in alternative DMS format.
        - Precision: Set the number of decimal places for results.
        - CRS for calculations: Specify a CRS for the calculations. If not specified, the layer's CRS will be used.

        Note: Ensure that your input layer has a defined coordinate reference system (CRS) for accurate results.
        """

    def createInstance(self):
        return CoordinateCalculatorAlgorithm()

class ArcGeekCalculatorProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(CoordinateCalculatorAlgorithm())

    def id(self):
        return "arcgeek_calculator"

    def name(self):
        return "ArcGeek Calculator"

    def longName(self):
        return self.name()

def calculate_coordinates(layer, calculate_xy, format_dd, format_dms, format_dms2, precision, crs, feedback):
    transform_to_crs = QgsCoordinateTransform(layer.crs(), crs, QgsProject.instance())
    transform_to_wgs84 = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())

    total = 100.0 / layer.featureCount() if layer.featureCount() else 0

    with edit(layer):
        for current, feature in enumerate(layer.getFeatures()):
            if feedback.isCanceled():
                break

            try:
                geom = feature.geometry()
                if geom.isEmpty():
                    continue

                point = geom.asPoint()
                point_in_crs = transform_to_crs.transform(point)
                point_wgs84 = transform_to_wgs84.transform(point_in_crs)

                if calculate_xy:
                    feature.setAttribute('X', round(point_in_crs.x(), precision))
                    feature.setAttribute('Y', round(point_in_crs.y(), precision))

                if format_dd:
                    feature.setAttribute('DD_Lat', round(point_wgs84.y(), precision))
                    feature.setAttribute('DD_Lon', round(point_wgs84.x(), precision))
                if format_dms:
                    feature.setAttribute('DMS_Lat', convert_to_dms(point_wgs84.y(), 'lat'))
                    feature.setAttribute('DMS_Lon', convert_to_dms(point_wgs84.x(), 'lon'))
                if format_dms2:
                    feature.setAttribute('Lat_DMS', convert_to_dms2(point_wgs84.y(), 'lat'))
                    feature.setAttribute('Lon_DMS', convert_to_dms2(point_wgs84.x(), 'lon'))

                layer.updateFeature(feature)
            except Exception as e:
                feedback.pushInfo(f"Error processing feature {feature.id()}: {str(e)}")

            feedback.setProgress(int(current * total))

def convert_to_dms(decimal_degree, coord_type):
    is_positive = decimal_degree >= 0
    decimal_degree = abs(decimal_degree)
    degrees = int(decimal_degree)
    minutes = int((decimal_degree - degrees) * 60)
    seconds = round((decimal_degree - degrees - minutes / 60) * 3600, 2)
    if coord_type == 'lat':
        direction = 'N' if is_positive else 'S'
    else:
        direction = 'E' if is_positive else 'W'

    return f"{degrees:2d}° {minutes:02d}' {seconds:05.2f}\" {direction}"

def convert_to_dms2(decimal_degree, coord_type):
    is_positive = decimal_degree >= 0
    decimal_degree = abs(decimal_degree)
    degrees = int(decimal_degree)
    minutes = int((decimal_degree - degrees) * 60)
    seconds = round((decimal_degree - degrees - minutes / 60) * 3600, 2)
    if coord_type == 'lat':
        direction = 'N' if is_positive else 'S'
    else:
        direction = 'E' if is_positive else 'W'

    return f"{direction} {degrees:2d}° {minutes:02d}' {seconds:05.2f}\""