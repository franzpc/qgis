from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterEnum, QgsProcessingException)
from .social_media import SocialMedia

import csv
import io

class ExportToCSVAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    FORMAT = 'FORMAT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.FORMAT,
                self.tr('Output format'),
                options=['CSV', 'Excel compatible CSV'],
                defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output file'),
                self.tr('CSV files (*.csv)'),
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        output_format = self.parameterAsEnum(parameters, self.FORMAT, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        fields = source.fields()
        field_names = [field.name() for field in fields]

        with io.open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            if output_format == 0:  # Standard CSV
                writer = csv.writer(f)
            else:  # Excel compatible CSV
                writer = csv.writer(f, dialect='excel')
            
            # Write header
            writer.writerow(field_names)
            
            # Write data
            for current, feature in enumerate(source.getFeatures()):
                if feedback.isCanceled():
                    break
                writer.writerow(feature.attributes())
                feedback.setProgress(int(current * total))

        return {self.OUTPUT: output_file}

    def name(self):
        return 'exporttocsv'

    def displayName(self):
        return self.tr('Export to CSV (Excel compatible)')

    def group(self):
        return self.tr('ArcGeek Calculator')

    def groupId(self):
        return 'arcgeekcalculator'

    def shortHelpString(self):
        help_text = self.tr("""
        This algorithm exports the attributes of a vector layer to CSV format.
        It offers two output options:
        1. Standard CSV: A regular comma-separated values file.
        2. Excel compatible CSV: A CSV file formatted to be easily opened in Excel.
        The tool will export all attributes of the input layer, including the feature ID.
        Geometry information is not included in the output.
    
        Note: This export uses UTF-8 encoding with BOM for better compatibility with Excel.
        """)
        return help_text + SocialMedia.social_links


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExportToCSVAlgorithm()