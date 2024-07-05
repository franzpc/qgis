# ArcGeek Calculator Plugin

## Version 1.3beta

ArcGeek Calculator is a QGIS plugin that provides various hydrological and geomorphological analysis tools. This version introduces the new `Watershed Morphometric Analysis` tool.

## Description
ArcGeek Calculator is a QGIS plugin that provides a comprehensive set of tools for coordinate calculations, conversions, and spatial operations. It's designed for GIS analysts, cartographers, surveyors, and anyone working with spatial data.

## Key Features
1. **Calculate Coordinates**: Add XY coordinates to point layers, convert to decimal degrees, and provide two formats of degrees minutes seconds.
2. **Calculate Line from Coordinates and Table**: Generate line features from tabular data containing distances and angles.
3. **Go to XY**: Quickly navigate to specific coordinates on the map and optionally create point markers.
4. **Extract Ordered Points from Polygons**: Extract and order points from the vertices of input polygons.
5. **Watershed Morphometric Analysis**: Perform a comprehensive morphometric analysis of a watershed, calculating various parameters and providing their interpretations.

## Installation Requirements
- QGIS 3.0 or higher
- Python 3.x

## Installation
1. Open QGIS
2. Go to Plugins > Manage and Install Plugins
3. Search for "ArcGeek Calculator"
4. Click "Install Plugin"

## Usage Instructions

### Calculate Coordinates
1. Open a point layer in QGIS
2. Go to Plugins > Watershed Morphometric Analysis > Calculate Coordinates
3. Select the input layer and desired options
4. Run the algorithm

### Calculate Line from Coordinates and Table
1. Prepare a table (CSV, TXT, or vector layer) with distance and angle fields
2. Go to Plugins > Watershed Morphometric Analysis > Calculate Line from Coordinates and Table
3. Enter the starting coordinates, select the input table, and corresponding fields
4. Choose the output CRS
5. Run the algorithm

### Go to XY
1. Go to Plugins > Watershed Morphometric Analysis > Go to XY
2. Enter the desired coordinates
3. Select the coordinate type and CRS
4. Click "Go"

### Extract Ordered Points from Polygons
1. Open a polygon layer in QGIS
2. Go to Plugins > Watershed Morphometric Analysis > Extract Ordered Points from Polygons
3. Select the input polygon layer and the polygon ID field
4. Run the algorithm

### Watershed Morphometric Analysis
1. Load your basin layer (polygon), stream network (line), and Digital Elevation Model (DEM) into QGIS.
2. Set the pour point (outlet) as a point layer.
3. Open the plugin from Plugins > Watershed Morphometric Analysis > Watershed Morphometric Analysis.
4. Select the input layers and parameters.
5. Click "Run".

The tool will calculate and display various morphometric parameters, including basin area, perimeter, length, width, relief, mean elevation, mean slope, drainage density, stream frequency, form factor, elongation ratio, circularity ratio, compactness coefficient, length of overland flow, ruggedness number, time of concentration (various methods), bifurcation ratio, and more.

## Usage Examples
[Here you can include screenshots or animated GIFs showing the plugin in action]

## Support
If you encounter any issues or have any suggestions, please open an issue on our [issue tracker](https://github.com/franzpc/qgis/issues).

## License
This project is licensed under the GNU General Public License v2.0 or later. See the [LICENSE](LICENSE) file for details.

## Author
ArcGeek

## Version History
- 1.3beta: Added "Watershed Morphometric Analysis" tool
- 1.2beta: Added "Extract Ordered Points from Polygons" functionalities
- 1.1beta: Added "Calculate Line from Coordinates and Table", and "Go to XY" functionalities
- 1.0: Initial release with "Calculate Coordinates"
