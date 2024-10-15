# ArcGeek Calculator Plugin
Version 2.3beta

ArcGeek Calculator is a comprehensive QGIS plugin that provides various hydrological, geomorphological, and spatial analysis tools. This version introduces new tools for kriging analysis, satellite index calculation, basemap management, screen capture, and CSV export.

## Description
ArcGeek Calculator is a QGIS plugin that provides a comprehensive set of tools for coordinate calculations, conversions, spatial operations, watershed analysis, land use analysis, flood simulation, and more. It's designed for GIS analysts, cartographers, surveyors, hydrologists, urban planners, and anyone working with spatial data.

## Key Features

1. Calculate Coordinates: Add XY coordinates to point layers, convert to Decimal Degrees, and provide two formats of Degrees Minutes Seconds.
2. Calculate Line Geometry: Calculate length and azimuth for line features.
3. Calculate Polygon Geometry: Calculate area and perimeter for polygon features.
4. Go to XY: Quickly navigate to specific coordinates on the map and optionally create point markers.
5. Extract Ordered Points from Polygons: Extract and order points from the vertices of input polygons with bi-directional numbering.
6. Lines to Ordered Points: Convert line features to ordered point features.
7. Calculate Line from Coordinates and Table: Generate a line and points from starting coordinates and a table of distances and angles.
8. Stream Network with Order: Generate a stream network with Strahler order.
9. Watershed Basin Delineation: Delineate watershed basins from a DEM and pour points.
10. Watershed Morphometric Analysis: Perform a comprehensive morphometric analysis of a watershed, calculating various parameters and providing their interpretations.
11. Land Use Change Detection: Analyze changes in land use between two time periods.
12. Weighted Sum Analysis: Perform weighted sum analysis on multiple raster layers.
13. Optimized Parcel Division: Divide rectangular parcels into lots of specified width.
14. Dam Flood Simulation: Simulate flooding based on a DEM and specified water level.
15. Kriging Analysis: Perform spatial interpolation using Kriging (requires external libraries: pykrige, scipy).
16. Satellite Index Calculator: Calculate various satellite indices (NDVI, NDWI, etc.) for different satellites.
17. Basemap Manager: Add and manage basemaps from Google Maps, Esri, Bing, and others.
18. Screen Capture: Capture and georeference the current map view.
19. Export to CSV: Export vector layer attributes to CSV format compatible with Excel.

## External Libraries
Some tools in this plugin require external libraries:
- Kriging Analysis: Requires pykrige and scipy
- Hypsometric Curve (part of Watershed Morphometric Analysis): Interactive version requires plotly and numpy

## Support
If you encounter any issues or have any suggestions, please open an issue on our [issue tracker](https://github.com/franzpc/qgis/issues).

## Support the Project
If you find ArcGeek Calculator useful, please consider supporting its development. Your contributions help maintain and improve the plugin.

You can make a donation via PayPal: [https://paypal.me/ArcGeek](https://paypal.me/ArcGeek)

Every contribution, no matter how small, is greatly appreciated and helps ensure the continued development of this tool.

## License
This project is licensed under the GNU General Public License v2.0 or later. See the [LICENSE](LICENSE) file for details.

## Author
ArcGeek

## Version History

2.3beta: Added Kriging Analysis, Satellite Index Calculator, Basemap Manager, Screen Capture, and Export to CSV tools.
2.1beta: Fix errors and improve performance.
2.0beta: Added Dam Flood Simulation tool, correction of general errors.
1.9beta: Improved Optimized Parcel Division tool with two-pass small polygon merging
1.8beta: Added Land Use Change Detection, Weighted Sum Analysis, and Optimized Parcel Division tools
1.7beta: Added new tools for watershed analysis and geometric calculations
1.6beta: Enhanced "Extract Ordered Points from Polygons" with bi-directional numbering
1.5beta: Added "Watershed Morphometric Analysis" tool
1.4beta: Added "Extract Ordered Points from Polygons" functionalities
1.3beta: Added "Calculate Line from Coordinates and Table", and "Go to XY" functionalities
1.2beta: Added "Lines to Ordered Points" functionality
1.1beta: Enhanced functionality and bug fixes
1.0: Initial release with "Calculate Coordinates"