from flask import Flask, request, render_template, send_file, abort, session, redirect, url_for, send_from_directory
import geopandas as gpd
from shapely.geometry import Polygon
import os
import zipfile
import pyogrio
import tempfile
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Function to create a grid of polygons based on the extent and grid dimensions
def create_grid(extent, grid_width, grid_height):
    minx, miny, maxx, maxy = extent
    grid_polygons = []

    # Loop through the extent to create grid cells
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            # Create each grid cell as a Polygon
            grid_polygons.append(Polygon([(x, y), (x + grid_width, y),
                                          (x + grid_width, y + grid_height),
                                          (x, y + grid_height)]))
            y += grid_height
        x += grid_width

    # Return the grid as a GeoDataFrame with the specified CRS
    return gpd.GeoDataFrame({'geometry': grid_polygons}, crs="EPSG:32646")

# Main route for file upload and form submission
@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Retrieve input values from the form
        grid_width = int(request.form['grid_width'])
        grid_height = int(request.form['grid_height'])
        buffer_size = int(request.form['buffer_size'])
        grid_prefix = request.form['grid_prefix']

        # Store input values in the session for future requests
        session.update(grid_width=grid_width, grid_height=grid_height,
                       buffer_size=buffer_size, grid_prefix=grid_prefix)

        # Read uploaded KML file using pyogrio
        kml_file = request.files['kml_file']
        gdf_e = pyogrio.read_dataframe(kml_file.stream, driver='KML')

        # Validate the uploaded file
        if gdf_e.empty:
            return "KML file not loaded correctly. Check file path or data."

        # Set CRS if not set, assume WGS84 (EPSG:4326)
        if gdf_e.crs is None:
            gdf_e.set_crs("EPSG:4326", inplace=True)

        # Reproject to UTM 46N if needed
        if gdf_e.crs != "EPSG:32646":
            gdf_e = gdf_e.to_crs("EPSG:32646")

        # Generate the grid based on the KML file's extent
        extent = gdf_e.total_bounds
        grid_gdf = create_grid(extent, grid_width, grid_height)

        # Perform intersection of the KML data with the grid
        intersection_gdf = gpd.overlay(gdf_e, grid_gdf, how='intersection')

        # Set up directory for storing generated map layers
        map_layers_dir = os.path.join(os.getcwd(), 'map_layers')
        os.makedirs(map_layers_dir, exist_ok=True)

        # Save input and intersection as GeoJSON files
        input_file_path = os.path.join(map_layers_dir, "Input_File.geojson")
        intersect_file_path = os.path.join(map_layers_dir, "Grid_Intersect.geojson")
        gdf_e.to_file(input_file_path, driver='GeoJSON')
        intersection_gdf.to_file(intersect_file_path, driver='GeoJSON')

        # Apply buffer to the intersected geometries
        buffered_gdf = intersection_gdf.buffer(buffer_size)
        buffered_gdf = gpd.GeoDataFrame(geometry=buffered_gdf, crs="EPSG:32646")

        # Save buffered geometries as GeoJSON
        buffer_file_path = os.path.join(map_layers_dir, "Grid_Buffer.geojson")
        buffered_gdf.to_file(buffer_file_path, driver='GeoJSON')

        # Generate download links for individual polygons
        buffered_gdf['download_link'] = [
            url_for('download_grid', grid_prefix=grid_prefix, kml_file=f"{grid_prefix}_polygon_{idx}.kml")
            for idx in range(len(buffered_gdf))
        ]
        buffered_gdf.to_file(buffer_file_path, driver='GeoJSON')  # Save with download links

        # Create temporary directory for saving each polygon as a KML
        kml_dir = tempfile.mkdtemp()
        kml_files = []

        # Save each buffered polygon as a separate KML file
        for idx, geometry in enumerate(buffered_gdf.geometry):
            single_polygon_gdf = gpd.GeoDataFrame({'geometry': [geometry]}, crs="EPSG:32646")
            kml_file_name = f"{grid_prefix}_polygon_{idx}.kml"
            kml_file_path = os.path.join(kml_dir, kml_file_name)
            pyogrio.write_dataframe(single_polygon_gdf, kml_file_path, driver='KML')
            kml_files.append(kml_file_name)

        # Package all KML files into a single ZIP
        zip_file_path = os.path.join(kml_dir, f"{grid_prefix}_Grids_KML.zip")
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for file_name in kml_files:
                zipf.write(os.path.join(kml_dir, file_name), file_name)

        # Save file paths in session for later access
        session.update(kml_files=kml_files, zip_file_path=zip_file_path,
                       kml_dir=kml_dir, input_file_path=input_file_path,
                       intersect_file_path=intersect_file_path, buffer_file_path=buffer_file_path,
                       success_message="Grid Generation is Complete")

        return redirect(url_for('upload'))

    # Handle GET request, use session values or set defaults
    return render_template('index.html', kml_files=session.get('kml_files', []),
                           zip_file_path=session.get('zip_file_path'), 
                           grid_width=session.get('grid_width', 800),
                           grid_height=session.get('grid_height', 800),
                           buffer_size=session.get('buffer_size', 0),
                           grid_prefix=session.get('grid_prefix', 'Drone Grid'),
                           input_file_path=session.get('input_file_path'),
                           intersect_file_path=session.get('intersect_file_path'),
                           buffer_file_path=session.get('buffer_file_path'),
                           success_message=session.pop('success_message', None))

# Download route for individual KML files
@app.route('/download_grid/<grid_prefix>/<kml_file>')
def download_grid(grid_prefix, kml_file):
    kml_dir = session.get('kml_dir', "")
    kml_file_path = os.path.join(kml_dir, kml_file)

    if not os.path.exists(kml_file_path):
        return abort(404, description="Grid polygon KML file not found.")

    return send_file(kml_file_path, as_attachment=True)

# Download all KML files as a ZIP
@app.route('/download_all')
def download_all():
    zip_file_path = session.get('zip_file_path')
    
    if not zip_file_path or not os.path.exists(zip_file_path):
        return abort(404, description="ZIP file not found.")
    
    return send_file(zip_file_path, as_attachment=True)

# Download specific GeoJSON files
@app.route('/download_input_geojson')
def download_input_geojson():
    input_file_path = session.get('input_file_path')
    if not input_file_path or not os.path.exists(input_file_path):
        return abort(404, description="Input GeoJSON file not found.")
    return send_file(input_file_path, as_attachment=True, download_name='Input_File.geojson')

@app.route('/download_intersect_geojson')
def download_intersect_geojson():
    intersect_file_path = session.get('intersect_file_path')
    if not intersect_file_path or not os.path.exists(intersect_file_path):
        return abort(404, description="Intersect GeoJSON file not found.")
    return send_file(intersect_file_path, as_attachment=True, download_name='Grid_Intersect.geojson')

@app.route('/download_buffer_geojson')
def download_buffer_geojson():
    buffer_file_path = session.get('buffer_file_path')
    if not buffer_file_path or not os.path.exists(buffer_file_path):
        return abort(404, description="Buffer GeoJSON file not found.")
    return send_file(buffer_file_path, as_attachment=True, download_name='Grid_Buffer.geojson')

# Reset the session and delete temp directory
@app.route('/reset')
def reset():
    kml_dir = session.get('kml_dir')
    
    # Clear session and delete temp directory if it exists
    session.clear()
    if kml_dir and os.path.exists(kml_dir):
        shutil.rmtree(kml_dir)
    
    return redirect(url_for('upload'))

# Serve files from the map_layers directory
@app.route('/map_layers/<path:filename>')
def map_layers(filename):
    return send_from_directory('map_layers', filename)

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
