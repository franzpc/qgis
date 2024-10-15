from qgis.core import *
from qgis.analysis import QgsZonalStatistics
from qgis.PyQt.QtGui import QColor, QPainter, QFont, QImage, QPen, QBrush
from qgis.PyQt.QtCore import QSize, Qt, QPointF, QRectF
import processing
import os
import csv

# Try to import plotly
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def generate_hypsometric_curve(dem_layer, basin_layer, output_folder, feedback):
    """
    Generate the hypsometric curve for the given DEM and basin layers.
    
    :param dem_layer: QgsRasterLayer of the DEM
    :param basin_layer: QgsVectorLayer of the basin
    :param output_folder: str, path to the output folder
    :param feedback: QgsProcessingFeedback object for logging
    """
    # Generate hypsometric curve data
    result = processing.run("qgis:hypsometriccurves", 
                            {'INPUT_DEM': dem_layer,
                             'BOUNDARY_LAYER': basin_layer,
                             'STEP': 100,
                             'USE_PERCENTAGE': True,
                             'OUTPUT_DIRECTORY': output_folder})

    # Find the most recent generated CSV file
    csv_files = [f for f in os.listdir(output_folder) if f.startswith('histogram_') and f.endswith('.csv')]
    if not csv_files:
        feedback.reportError("No histogram CSV file found in the output directory.")
        return

    csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_folder, x)), reverse=True)
    csv_file = os.path.join(output_folder, csv_files[0])
    feedback.pushInfo(f"Using most recent histogram file: {csv_file}")

    try:
        # Read data from the generated CSV
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            data = list(reader)

        area = [float(row[0]) for row in data]
        elevation = [float(row[1]) for row in data]

        # Calculate relative height and area
        min_elev, max_elev = min(elevation), max(elevation)
        relative_height = [(e - min_elev) / (max_elev - min_elev) for e in elevation]
        relative_area = [a / 100 for a in area]  # Convert percentage to decimal

        # Invert the order of data for the hypsometric curve
        relative_height = relative_height[::-1]
        relative_area = [1 - a for a in relative_area[::-1]]

        # Colors for the hypsometric curve
        curve_color = QColor(19, 138, 249)  # Blue
        point_color = QColor(203, 67, 53)   # Red

        # Create static image
        create_static_image(relative_area, relative_height, curve_color, point_color, output_folder)

        # Create interactive HTML if plotly is available
        if PLOTLY_AVAILABLE:
            create_interactive_html(relative_area, relative_height, area, elevation, curve_color, point_color, output_folder)
            feedback.pushInfo("Interactive hypsometric curve (HTML) generated.")
        else:
            feedback.pushInfo("Note: The interactive HTML version was not generated because plotly and numpy libraries are required.")

        feedback.pushInfo(f"Hypsometric curve generated. Results saved in: {output_folder}")
        
        return {
            'CSV': csv_file,
            'PNG': os.path.join(output_folder, 'hypsometric_curve.png'),
            'HTML': os.path.join(output_folder, 'hypsometric_curve_interactive.html') if PLOTLY_AVAILABLE else None
        }

    except Exception as e:
        feedback.reportError(f"Error processing CSV file: {str(e)}")
        return None
def create_static_image(relative_area, relative_height, curve_color, point_color, output_folder):
    """
    Create a static image of the hypsometric curve.
    
    :param relative_area: list of relative area values
    :param relative_height: list of relative height values
    :param curve_color: QColor for the curve
    :param point_color: QColor for the points
    :param output_folder: str, path to the output folder
    """
    # Create an image for the graph
    width, height = 800, 600
    image = QImage(QSize(width, height), QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.white)

    painter = QPainter()
    painter.begin(image)
    painter.setRenderHint(QPainter.Antialiasing)

    # Define margins
    margin_left = 80
    margin_right = 50
    margin_top = 50
    margin_bottom = 70
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    # Draw axes
    painter.setPen(QPen(Qt.black, 2))
    painter.drawLine(margin_left, height - margin_bottom, width - margin_right, height - margin_bottom)  # X-axis
    painter.drawLine(margin_left, height - margin_bottom, margin_left, margin_top)  # Y-axis

    # Draw axis labels
    painter.setFont(QFont('Arial', 9))
    # X-axis labels
    for i in range(11):
        x = int(margin_left + i * plot_width / 10)
        y = height - margin_bottom
        painter.drawLine(x, y, x, y + 5)
        painter.drawText(x - 15, y + 15, 30, 20, Qt.AlignCenter, f"{i/10:.1f}")
    
    # Y-axis labels
    for i in range(11):
        x = margin_left
        y = int(height - margin_bottom - i * plot_height / 10)
        painter.drawLine(x - 5, y, x, y)
        painter.drawText(x - 60, y - 10, 50, 20, Qt.AlignRight | Qt.AlignVCenter, f"{i/10:.1f}")

    # Function to draw curves
    def draw_curve(func, color, style=Qt.SolidLine):
        painter.setPen(QPen(color, 1, style))
        points = []
        for i in range(101):
            x = i / 100
            y = func(x)
            point = QPointF(margin_left + x * plot_width, height - margin_bottom - y * plot_height)
            points.append(point)
        painter.drawPolyline(points)

    # Draw standard curves
    draw_curve(lambda x: 1 - x**2, QColor('#FF6B6B'), Qt.DashLine)  # Young stage
    draw_curve(lambda x: 1 - x, QColor('#4ECDC4'), Qt.DotLine)      # Mature stage
    draw_curve(lambda x: (1 - x)**2, QColor('#2ECC71'), Qt.DashDotLine)  # Old stage

    # Draw hypsometric curve
    painter.setPen(QPen(curve_color, 3))
    points = [QPointF(margin_left + x * plot_width, height - margin_bottom - y * plot_height) 
              for x, y in zip(relative_area, relative_height)]
    painter.drawPolyline(points)

    # Draw points on the hypsometric curve
    painter.setPen(QPen(Qt.black))
    painter.setBrush(QBrush(point_color))
    for point in points:
        painter.drawEllipse(point, 4, 4)

    # Add axis labels
    painter.setPen(QPen(Qt.black))
    painter.setFont(QFont('Arial', 10))
    painter.drawText(QRectF(width/2 - 100, height - 25, 200, 20), Qt.AlignCenter, "Relative area (a/A)")
    
    # Y-axis label
    painter.save()
    painter.translate(20, height/2)
    painter.rotate(-90)
    painter.drawText(QRectF(-100, -30, 200, 60), Qt.AlignCenter, "Relative height (h/H)")
    painter.restore()

    painter.end()

    # Save image
    output_path = os.path.join(output_folder, 'hypsometric_curve.png')
    image.save(output_path)

def create_interactive_html(relative_area, relative_height, area, elevation, curve_color, point_color, output_folder):
    """
    Create an interactive HTML version of the hypsometric curve.
    
    :param relative_area: list of relative area values
    :param relative_height: list of relative height values
    :param area: list of original area values
    :param elevation: list of original elevation values
    :param curve_color: QColor for the curve
    :param point_color: QColor for the points
    :param output_folder: str, path to the output folder
    """
    # Create subplots
    fig = make_subplots(rows=1, cols=2, column_widths=[0.7, 0.3])

    # Generate standard curves
    x = np.linspace(0, 1, 100)
    y_young = 1 - x**2
    y_mature = 1 - x
    y_old = (1 - x)**2

    # Add standard curves
    fig.add_trace(go.Scatter(x=x, y=y_young, mode='lines', name='Young stage', 
                             line=dict(color='#FF6B6B', width=1, dash='dash'),
                             hovertemplate='a/A: %{x:.2f}<br>h/H: %{y:.2f}<extra></extra>'), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=y_mature, mode='lines', name='Mature stage', 
                             line=dict(color='#4ECDC4', width=1, dash='dot'),
                             hovertemplate='a/A: %{x:.2f}<br>h/H: %{y:.2f}<extra></extra>'), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=y_old, mode='lines', name='Old stage', 
                             line=dict(color='#2ECC71', width=1, dash='dashdot'),
                             hovertemplate='a/A: %{x:.2f}<br>h/H: %{y:.2f}<extra></extra>'), row=1, col=1)

    # Hypsometric curve (line)
    fig.add_trace(go.Scatter(
        x=relative_area, 
        y=relative_height, 
        mode='lines', 
        name='Hypsometric Curve (Line)',
        line=dict(color=f'rgb{curve_color.getRgb()[:3]}', width=3),
        hovertemplate='a/A: %{x:.2f}<br>h/H: %{y:.2f}<extra></extra>'
    ), row=1, col=1)

    # Hypsometric curve (points)
    fig.add_trace(go.Scatter(
        x=relative_area, 
        y=relative_height, 
        mode='markers', 
        name='Hypsometric Curve (Points)',
        marker=dict(color=f'rgb{point_color.getRgb()[:3]}', size=8, symbol='circle'),
        hovertemplate='a/A: %{x:.2f}<br>h/H: %{y:.2f}<extra></extra>'
    ), row=1, col=1)

    # Elevation distribution
    fig.add_trace(
        go.Bar(
            y=elevation, 
            x=[a - area[i-1] if i > 0 else a for i, a in enumerate(area)],
            orientation='h', 
            name='Elevation Distribution',
            marker=dict(color=f'rgb{curve_color.getRgb()[:3]}', line=dict(color=f'rgb{curve_color.getRgb()[:3]}', width=1)),
            hovertemplate='Area: %{x:.2f} %<br>Elevation: %{y:.2f} m<extra></extra>'
        ),
        row=1, col=2
    )

    # Update layout
    fig.update_layout(
        title_text="Hypsometric Curve and Elevation Distribution",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Update axes for hypsometric curve

    fig.update_xaxes(title_text="Relative area (a/A)", range=[0, 1], row=1, col=1, 
                     showgrid=False, zeroline=False, ticks="outside", ticklen=5,
                     showline=True, linewidth=0.5, linecolor='black', mirror=False)
    fig.update_yaxes(title_text="Relative height (h/H)", range=[0, 1], row=1, col=1, 
                     showgrid=False, zeroline=False, ticks="outside", ticklen=5,
                     showline=True, linewidth=0.5, linecolor='black', mirror=False)
    
    # Update axes for elevation distribution
    fig.update_xaxes(title_text="Area (%)", row=1, col=2, 
                     showgrid=False, zeroline=False, ticks="outside", ticklen=5,
                     showline=True, linewidth=0.05, linecolor='black', mirror=False)
    fig.update_yaxes(title_text="Elevation (m a.s.l.)", row=1, col=2, 
                     showgrid=False, zeroline=False, ticks="outside", ticklen=5,
                     showline=True, linewidth=0.05, linecolor='black', mirror=False)

    # Save plot as interactive HTML
    output_path = os.path.join(output_folder, 'hypsometric_curve_interactive.html')
    fig.write_html(output_path)