# ArcGeek Calculator

## Description
ArcGeek Calculator is a QGIS plugin that provides a comprehensive set of tools for coordinate calculations, conversions, and spatial operations. It's designed for GIS analysts, cartographers, surveyors, and anyone working with spatial data.

## Key Features
1. **Calculate Coordinates**: Add XY coordinates to point layers, convert to decimal degrees, and provide two formats of degrees minutes seconds.
2. **Calculate Line from Coordinates and Table**: Generate line features from tabular data containing distances and angles.
3. **Go to XY**: Quickly navigate to specific coordinates on the map and optionally create point markers.

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
2. Go to Plugins > ArcGeek Calculator > Calculate Coordinates
3. Select the input layer and desired options
4. Run the algorithm

### Calculate Line from Coordinates and Table
1. Prepare a CSV table with distance and angle fields
2. Go to Plugins > ArcGeek Calculator > Calculate Line from Coordinates and Table
3. Enter the starting coordinates, select the CSV file, and corresponding fields
4. Run the algorithm

### Go to XY
1. Go to Plugins > ArcGeek Calculator > Go to XY
2. Enter the desired coordinates
3. Select the coordinate type and CRS
4. Click "Go"

## Usage Examples
[Here you can include screenshots or animated GIFs showing the plugin in action]

## Support
If you encounter any issues or have any suggestions, please open an issue on our [issue tracker](https://github.com/franzpc/qgis/issues).


## License
This project is licensed under the GNU General Public License v2.0 or later. See the [LICENSE](LICENSE) file for details.

## Author
ArcGeek

## Version History
- 1.1beta: Added "Calculate Line from Coordinates and Table" and "Go to XY" functionalities
- 1.0: Initial release with "Calculate Coordinates"
