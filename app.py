from flask import Flask, request, render_template, send_file, abort, session, redirect, url_for, send_from_directory
import geopandas as gpd
from shapely.geometry import Polygon
import os
import zipfile
import pyogrio
import tempfile
import shutil

app = Flask(__name__)

# Function to create a grid
def create_grid(extent, grid_size):
    minx, miny, maxx, maxy = extent
    grid_polygons = []
    
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            # Create a single grid square (Polygon)
            grid_polygons.append(Polygon([(x, y), (x + grid_size, y), 
                                          (x + grid_size, y + grid_size), 
                                          (x, y + grid_size)]))
            y += grid_size
        x += grid_size

    # Create a GeoDataFrame from the grid polygons with UTM 46N CRS
    return gpd.GeoDataFrame({'geometry': grid_polygons}, crs="EPSG:32646")



@app.route('/', methods=['GET', 'POST'])

def upload():
    if request.method == 'POST':
        # Get the input values
        grid_size = int(request.form['grid_size'])
        buffer_size = int(request.form['buffer_size'])
        grid_prefix = request.form['grid_prefix']

        # Save input values in the session
        session['grid_size'] = grid_size
        session['buffer_size'] = buffer_size
        session['grid_prefix'] = grid_prefix

        kml_file = request.files['kml_file']

        # Read the KML file
        gdf_e = gpd.read_file(kml_file)

        # Check if the KML file is loaded correctly
        if gdf_e.empty:
            return "KML file not loaded correctly. Check file path or data."

        # Reproject to UTM 46N if not already in UTM 46N
        if gdf_e.crs != "EPSG:32646":
            gdf_e = gdf_e.to_crs("EPSG:32646")

        # Get the extent of the KML file (minx, miny, maxx, maxy)
        extent = gdf_e.total_bounds

        # Create the grid
        grid_gdf = create_grid(extent, grid_size)

        # Perform intersection between the KML and the grid
        intersection_gdf = gpd.overlay(gdf_e, grid_gdf, how='intersection')

        # Create a sub-directory for map layers
        map_layers_dir = os.path.join(os.getcwd(), 'map_layers')
        os.makedirs(map_layers_dir, exist_ok=True)  # Create the directory if it doesn't exist

        # Save the input KML file as a GeoJSON in the map_layers directory
        input_file = f"Input_File.geojson"
        input_file_path = os.path.join(map_layers_dir, input_file)
        gdf_e.to_file(input_file_path, driver='GeoJSON')

        # Save intersection as GeoJSON in map_layers directory
        intersect_file = f"Grid_Intersect.geojson"
        intersect_file_path = os.path.join(map_layers_dir, intersect_file)
        intersection_gdf.to_file(intersect_file_path, driver='GeoJSON')

        # Apply the buffer
        buffered_gdf = intersection_gdf.buffer(buffer_size)
        buffered_gdf = gpd.GeoDataFrame(geometry=buffered_gdf, crs="EPSG:32646")

        # Save buffer as GeoJSON in map_layers directory
        buffer_file = f"Grid_Buffer.geojson"
        buffer_file_path = os.path.join(map_layers_dir, buffer_file)
        buffered_gdf.to_file(buffer_file_path, driver='GeoJSON')

        # Create download links for each polygon in the buffer
        buffered_gdf['download_link'] = [
            url_for('download_grid', grid_prefix=grid_prefix, kml_file=f"{grid_prefix}_polygon_{idx}.kml")
            for idx in range(len(buffered_gdf))
        ]

        # Save the updated buffered GeoDataFrame with download links as GeoJSON
        buffered_gdf.to_file(buffer_file_path, driver='GeoJSON')

        # Directory to save individual grid KML files
        kml_dir = tempfile.mkdtemp()
        kml_files = []

        # Save each polygon as a separate KML file
        for idx, geometry in enumerate(buffered_gdf.geometry):
            single_polygon_gdf = gpd.GeoDataFrame({'geometry': [geometry]}, crs="EPSG:32646")
            kml_file_name = f"{grid_prefix}_polygon_{idx}.kml"
            kml_file_path = os.path.join(kml_dir, kml_file_name)
            pyogrio.write_dataframe(single_polygon_gdf, kml_file_path, driver='KML')
            kml_files.append(kml_file_name)

        # Create a ZIP file containing all KML files
        zip_file_path = os.path.join(kml_dir, f"{grid_prefix}_Grids_KML.zip")
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for file_name in kml_files:
                zipf.write(os.path.join(kml_dir, file_name), file_name)

        # Save paths in the session
        session['kml_files'] = kml_files
        session['zip_file_path'] = zip_file_path
        session['grid_prefix'] = grid_prefix
        session['kml_dir'] = kml_dir
        session['input_file_path'] = input_file_path  # Save input file path for later use
        session['intersect_file_path'] = intersect_file_path  # Save intersect file path
        session['buffer_file_path'] = buffer_file_path  # Save buffer file path

        # At the end of the grid generation process, before the redirect
        session['success_message'] = "Grid Generation is Complete"
        return redirect(url_for('upload'))

    # Load values from the session or set defaults for GET request
    grid_size = session.get('grid_size', 1000)
    buffer_size = session.get('buffer_size', 0)
    grid_prefix = session.get('grid_prefix', 'Drone_Grid')

    # Load other variables for GET request if needed
    kml_files = session.get('kml_files', [])
    zip_file_path = session.get('zip_file_path', None)
    input_file_path = session.get('input_file_path', None)
    intersect_file_path = session.get('intersect_file_path', None)
    buffer_file_path = session.get('buffer_file_path', None)

    # Retrieve the success message from the session if available
    success_message = session.pop('success_message', None)

    return render_template('index.html', kml_files=kml_files, zip_file_path=zip_file_path,
                           grid_size=grid_size, buffer_size=buffer_size, grid_prefix=grid_prefix,
                           input_file_path=input_file_path, intersect_file_path=intersect_file_path,
                           buffer_file_path=buffer_file_path, success_message=success_message)


if __name__ == '__main__':
    app.run(debug=True)