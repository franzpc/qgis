import math
from qgis.core import QgsGeometry, QgsPointXY, QgsRasterBandStats

def calculate_parameters(basin_source, streams_source, dem_layer, pour_point, stream_order_field, mean_slope_degrees, feedback):
    basin_area = sum([f.geometry().area() for f in basin_source.getFeatures()]) / 1e6  # m² to km²
    perimeter = sum([f.geometry().length() for f in basin_source.getFeatures()]) / 1e3  # m to km

    # Calculate Basin Length (Lb) as the longest distance within the basin polygon

    basin_length = calculate_basin_length(basin_source, QgsPointXY(pour_point))

    # Calculate Basin Width (B) as the basin area divided by the basin length
    basin_width = basin_area / basin_length

    total_stream_length = sum([f.geometry().length() for f in streams_source.getFeatures()]) / 1e3  # m to km
    main_channel_length = sum([f.geometry().length() for f in streams_source.getFeatures() if f[stream_order_field] == max([f[stream_order_field] for f in streams_source.getFeatures()])]) / 1e3

    stream_order = calculate_stream_order(streams_source, stream_order_field)
    num_streams_first_order = stream_order.count(1)
    total_stream_number = len(stream_order)

    drainage_density = total_stream_length / basin_area if basin_area > 0 else 0

    if num_streams_first_order != 0:
        bifurcation_ratio = total_stream_number / num_streams_first_order
    else:
        bifurcation_ratio = None

    dem_stats = dem_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
    max_elevation = dem_stats.maximumValue
    min_elevation = dem_stats.minimumValue
    relief = max_elevation - min_elevation

    mean_stream_length = total_stream_length / total_stream_number if total_stream_number != 0 else None

    stream_frequency = total_stream_number / basin_area

    drainage_intensity = stream_frequency / drainage_density if drainage_density != 0 else None

    length_of_overland_flow = 1 / (2 * drainage_density) if drainage_density != 0 else None

    mean_elevation = (max_elevation + min_elevation) / 2

    mean_slope_radians = math.radians(mean_slope_degrees)
    mean_slope_m_per_m = math.tan(mean_slope_radians)
    mean_slope_percent = math.tan(math.radians(mean_slope_degrees)) * 100

    time_of_concentration_kirpich = 0.021 * (basin_length * 1000) ** 0.77 * mean_slope_m_per_m ** -0.385
    time_of_concentration_kerby = 0.828 * (basin_length * 1000) ** 0.467 / (mean_slope_m_per_m ** 0.235)
    time_of_concentration_giandotti = ((4 * math.sqrt(basin_area) + 1.5 * main_channel_length) / (0.8 * math.sqrt(relief))) * 60
    time_of_concentration_temez = 0.3 * (main_channel_length * (mean_slope_m_per_m ** 0.25)) ** 0.76 * 60
    time_of_concentration_usda = (3.3 * basin_length) / math.sqrt(mean_slope_percent) * 60

    form_factor = basin_area / (basin_length ** 2)

    elongation_ratio = (2 * math.sqrt(basin_area / math.pi)) / basin_length

    circularity_ratio = (4 * math.pi * basin_area) / (perimeter ** 2)

    compactness_coefficient = 0.2821 * perimeter / math.sqrt(basin_area)

    ruggedness_number = drainage_density * relief / 1000  # Convert relief to km

    infiltration_number = drainage_density * stream_frequency

    drainage_texture = total_stream_number / perimeter

    fitness_ratio = main_channel_length / perimeter

    asymmetry_factor = calculate_asymmetry_factor(basin_source, pour_point)

    orographic_coefficient = calculate_orographic_coefficient(relief, basin_area)

    return {
        "Basin Area (A)": {"value": basin_area, "unit": "km²", "interpretation": get_basin_area_interpretation(basin_area)},
        "Perimeter (P)": {"value": perimeter, "unit": "km", "interpretation": "Basin perimeter"},
        "Basin Length (Lb)": {"value": basin_length, "unit": "km", "interpretation": "Basin length"},
        "Basin Width (B)": {"value": basin_width, "unit": "km", "interpretation": "Basin width"},
        "Relief (H)": {"value": relief, "unit": "m", "interpretation": get_relief_interpretation(relief)},
        "Mean Elevation": {"value": mean_elevation, "unit": "m a.s.l.", "interpretation": "Average elevation of the basin"},
        "Mean Slope (degrees)": {"value": mean_slope_degrees, "unit": "degrees", "interpretation": get_mean_slope_interpretation(mean_slope_degrees)},
        "Mean Slope (percent)": {"value": mean_slope_m_per_m * 100, "unit": "%", "interpretation": get_mean_slope_interpretation(mean_slope_m_per_m * 100, percent=True)},
        "Drainage Density (Dd)": {"value": drainage_density, "unit": "km/km²", "interpretation": get_drainage_density_interpretation(drainage_density)},
        "Stream Frequency (Fs)": {"value": stream_frequency, "unit": "streams/km²", "interpretation": get_stream_frequency_interpretation(stream_frequency)},
        "Form Factor (Ff)": {"value": form_factor, "unit": "", "interpretation": get_form_factor_interpretation(form_factor)},
        "Elongation Ratio (Re)": {"value": elongation_ratio, "unit": "", "interpretation": get_elongation_ratio_interpretation(elongation_ratio)},
        "Circularity Ratio (Rc)": {"value": circularity_ratio, "unit": "", "interpretation": get_circularity_ratio_interpretation(circularity_ratio)},
        "Compactness Coefficient (Kc)": {"value": compactness_coefficient, "unit": "", "interpretation": get_compactness_coefficient_interpretation(compactness_coefficient)},
        "Length of Overland Flow (Lo)": {"value": length_of_overland_flow, "unit": "km", "interpretation": get_length_of_overland_flow_interpretation(length_of_overland_flow)},
        "Constant of Channel Maintenance (C)": {"value": 1/drainage_density if drainage_density != 0 else None, "unit": "km²/km", "interpretation": get_constant_channel_maintenance_interpretation(1/drainage_density if drainage_density != 0 else None)},
        "Ruggedness Number (Rn)": {"value": ruggedness_number, "unit": "", "interpretation": get_ruggedness_number_interpretation(ruggedness_number)},
        "Time of Concentration - Kirpich (Tc)": {"value": time_of_concentration_kirpich, "unit": "minutes", "interpretation": get_time_of_concentration_interpretation(time_of_concentration_kirpich)},
        "Time of Concentration - Kerby (Tc)": {"value": time_of_concentration_kerby, "unit": "minutes", "interpretation": get_time_of_concentration_interpretation(time_of_concentration_kerby)},
        "Time of Concentration - Giandotti (Tc)": {"value": time_of_concentration_giandotti, "unit": "minutes", "interpretation": get_time_of_concentration_interpretation(time_of_concentration_giandotti)},
        "Time of Concentration - Témez (Tc)": {"value": time_of_concentration_temez, "unit": "minutes", "interpretation": get_time_of_concentration_interpretation(time_of_concentration_temez)},
        "Time of Concentration - USDA (Tc)": {"value": time_of_concentration_usda, "unit": "minutes", "interpretation": get_time_of_concentration_interpretation(time_of_concentration_usda)},
        "Bifurcation Ratio (Rb)": {"value": bifurcation_ratio, "unit": "", "interpretation": get_bifurcation_ratio_interpretation(bifurcation_ratio)},
        "Stream Order": {"value": max(stream_order), "unit": "", "interpretation": f"Highest stream order (Strahler): {max(stream_order)}"},
        "Mean Stream Length (Lm)": {"value": mean_stream_length, "unit": "km", "interpretation": "Average length of streams"},
        "Drainage Intensity (Id)": {"value": drainage_intensity, "unit": "", "interpretation": get_drainage_intensity_interpretation(drainage_intensity)},
        "Main Channel Length (Lc)": {"value": main_channel_length, "unit": "km", "interpretation": "Length of the main channel"},
        "Total Length of Channels (Lt)": {"value": total_stream_length, "unit": "km", "interpretation": "Total length of all channels"},
        "Number of Streams (Nu)": {"value": total_stream_number, "unit": "", "interpretation": "Total number of streams"},
        "Drainage Texture (Dt)": {"value": drainage_texture, "unit": "", "interpretation": get_drainage_texture_interpretation(drainage_texture)},
        "Infiltration Number (If)": {"value": infiltration_number, "unit": "", "interpretation": get_infiltration_number_interpretation(infiltration_number)},
        "Fitness Ratio (Rf)": {"value": fitness_ratio, "unit": "", "interpretation": get_fitness_ratio_interpretation(fitness_ratio)},
        "Minimum Elevation": {"value": min_elevation, "unit": "m a.s.l.", "interpretation": "Minimum elevation of the basin"},
        "Maximum Elevation": {"value": max_elevation, "unit": "m a.s.l.", "interpretation": "Maximum elevation of the basin"},
        "Asymmetry Factor (Af)": {"value": asymmetry_factor, "unit": "", "interpretation": get_asymmetry_factor_interpretation(asymmetry_factor)},
        "Orographic Coefficient (Oc)": {"value": orographic_coefficient, "unit": "", "interpretation": get_orographic_coefficient_interpretation(orographic_coefficient)}
    }

def calculate_basin_length(basin_source, pour_point):
    basin_geom = [f.geometry() for f in basin_source.getFeatures()][0]
    furthest_point = basin_geom.vertexAt(0)
    max_distance = 0
    for vertex in basin_geom.vertices():
        distance = QgsGeometry.fromPointXY(QgsPointXY(vertex)).distance(QgsGeometry.fromPointXY(pour_point))
        if distance > max_distance:
            max_distance = distance
            furthest_point = vertex
    basin_length = QgsGeometry.fromPointXY(QgsPointXY(furthest_point)).distance(QgsGeometry.fromPointXY(pour_point))
    return basin_length / 1e3  # m to km

def calculate_stream_order(streams_source, stream_order_field):
    stream_order = []
    for f in streams_source.getFeatures():
        if stream_order_field and stream_order_field in f.fields().names():
            stream_order.append(f[stream_order_field])
        else:
            stream_order.append(1)  # Assume all streams are first order if no order field exists
    return stream_order

# Interpretations
def get_basin_area_interpretation(area):
    if area < 100:
        return "Small basin"
    elif 100 <= area < 1000:
        return "Medium-sized basin"
    else:
        return "Large basin"

def get_mean_slope_interpretation(mean_slope, percent=False):
    if percent:
        if mean_slope < 5:
            return "Gently sloping"
        elif 5 <= mean_slope < 10:
            return "Moderately steep"
        else:
            return "Steep"
    else:
        if mean_slope < 2.86:
            return "Gently sloping"
        elif 2.86 <= mean_slope < 5.71:
            return "Moderately steep"
        else:
            return "Steep"

def get_form_factor_interpretation(form_factor):
    if form_factor < 0.5:
        return "Elongated shape, low susceptibility to flash floods"
    elif 0.5 <= form_factor < 0.75:
        return "Intermediate shape"
    else:
        return "Circular shape, high susceptibility to flash floods"

def get_elongation_ratio_interpretation(elongation_ratio):
    if elongation_ratio < 0.5:
        return "Elongated shape"
    elif 0.5 <= elongation_ratio < 0.75:
        return "Oval shape"
    else:
        return "Circular shape"

def get_circularity_ratio_interpretation(circularity_ratio):
    if circularity_ratio < 0.4:
        return "Strongly elongated shape"
    elif 0.4 <= circularity_ratio < 0.6:
        return "Elongated shape"
    elif 0.6 <= circularity_ratio < 0.8:
        return "Oval shape"
    else:
        return "Circular shape"

def get_drainage_density_interpretation(drainage_density):
    if drainage_density < 0.5:
        return "Very coarse drainage texture"
    elif 0.5 <= drainage_density < 1.0:
        return "Coarse drainage texture"
    elif 1.0 <= drainage_density < 2.0:
        return "Moderate drainage texture"
    elif 2.0 <= drainage_density < 3.5:
        return "Fine drainage texture"
    else:
        return "Very fine drainage texture"

def get_stream_frequency_interpretation(stream_frequency):
    if stream_frequency < 1:
        return "Low stream frequency"
    elif 1 <= stream_frequency < 3:
        return "Moderate stream frequency"
    elif 3 <= stream_frequency < 5:
        return "High stream frequency"
    else:
        return "Very high stream frequency"

def get_compactness_coefficient_interpretation(compactness_coefficient):
    if compactness_coefficient < 1.25:
        return "Almost circular shape"
    elif 1.25 <= compactness_coefficient < 1.5:
        return "Oval-circular to oval-oblong shape"
    elif 1.5 <= compactness_coefficient < 1.75:
        return "Oval-oblong shape"
    else:
        return "Rectangular-oblong shape"

def get_length_of_overland_flow_interpretation(length_of_overland_flow):
    if length_of_overland_flow < 0.25:
        return "Short overland flow length, indicating high drainage density"
    elif 0.25 <= length_of_overland_flow < 0.5:
        return "Moderate overland flow length"
    else:
        return "Long overland flow length, indicating low drainage density"

def get_constant_channel_maintenance_interpretation(constant_channel_maintenance):
    if constant_channel_maintenance < 0.5:
        return "Low constant of channel maintenance, indicating high drainage density"
    elif 0.5 <= constant_channel_maintenance < 1:
        return "Moderate constant of channel maintenance"
    else:
        return "High constant of channel maintenance, indicating low drainage density"

def get_ruggedness_number_interpretation(ruggedness_number):
    if ruggedness_number < 0.1:
        return "Extremely low ruggedness"
    elif 0.1 <= ruggedness_number < 0.5:
        return "Low ruggedness"
    elif 0.5 <= ruggedness_number < 1:
        return "Moderate ruggedness"
    elif 1 <= ruggedness_number < 2:
        return "High ruggedness"
    else:
        return "Extremely high ruggedness"

def get_time_of_concentration_interpretation(time_of_concentration):
    if time_of_concentration < 1:
        return "Very short time of concentration, indicating rapid response to rainfall"
    elif 1 <= time_of_concentration < 3:
        return "Short time of concentration"
    elif 3 <= time_of_concentration < 6:
        return "Moderate time of concentration"
    else:
        return "Long time of concentration, indicating slow response to rainfall"

def get_bifurcation_ratio_interpretation(bifurcation_ratio):
    if bifurcation_ratio is None:
        return "Unable to calculate bifurcation ratio"
    elif bifurcation_ratio < 3:
        return "Low bifurcation ratio, indicating uniform lithology and gentle slopes"
    elif 3 <= bifurcation_ratio <= 5:
        return "Normal bifurcation ratio for natural drainage systems"
    else:
        return "High bifurcation ratio, indicating steep slopes and structural control"

def get_drainage_intensity_interpretation(drainage_intensity):
    if drainage_intensity is None:
        return "Unable to calculate drainage intensity"
    elif drainage_intensity < 1:
        return "Low drainage intensity"
    elif 1 <= drainage_intensity < 2:
        return "Moderate drainage intensity"
    elif 2 <= drainage_intensity < 3:
        return "High drainage intensity"
    else:
        return "Very high drainage intensity"

def get_relief_interpretation(relief):
    if relief < 100:
        return "Low relief, indicating flat terrain"
    elif 100 <= relief < 300:
        return "Moderate relief"
    elif 300 <= relief < 600:
        return "High relief"
    else:
        return "Very high relief, indicating mountainous terrain"

def get_drainage_texture_interpretation(drainage_texture):
    if drainage_texture < 2:
        return "Coarse drainage texture"
    elif 2 <= drainage_texture < 4:
        return "Moderate drainage texture"
    elif 4 <= drainage_texture < 6:
        return "Fine drainage texture"
    else:
        return "Very fine drainage texture"

def get_infiltration_number_interpretation(infiltration_number):
    if infiltration_number < 1:
        return "Low infiltration number, indicating high infiltration"
    elif 1 <= infiltration_number < 3:
        return "Moderate infiltration number"
    elif 3 <= infiltration_number < 5:
        return "High infiltration number"
    else:
        return "Very high infiltration number"

def get_fitness_ratio_interpretation(fitness_ratio):
    if fitness_ratio < 0.2:
        return "Low fitness ratio, indicating inefficient drainage network"
    elif 0.2 <= fitness_ratio < 0.4:
        return "Moderate fitness ratio"
    else:
        return "High fitness ratio, indicating efficient drainage network"

def calculate_asymmetry_factor(basin_source, pour_point):
    # Implement the calculation for the asymmetry factor
    return 0.5  # Placeholder value

def calculate_orographic_coefficient(relief, basin_area):
    # Implement the calculation for the orographic coefficient
    return relief * basin_area  # Placeholder formula

def get_asymmetry_factor_interpretation(asymmetry_factor):
    if asymmetry_factor < 0.4:
        return "Low asymmetry, indicating a symmetrical basin"
    elif 0.4 <= asymmetry_factor < 0.6:
        return "Moderate asymmetry"
    else:
        return "High asymmetry, indicating an asymmetrical basin"

def get_orographic_coefficient_interpretation(orographic_coefficient):
    if orographic_coefficient < 100:
        return "Low orographic influence"
    elif 100 <= orographic_coefficient < 300:
        return "Moderate orographic influence"
    else:
        return "High orographic influence"
