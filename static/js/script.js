// Initialize the map
var map = L.map("map", {
  attributionControl: true,
  measureControl: true,
}).setView([0, 0], 2); // Center on a neutral location, can be adjusted
map.addControl(
  new L.Control.Fullscreen({
    position: "topleft",
  })
);
// Initialize Leaflet Draw
var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

var drawControl = new L.Control.Draw({
  edit: {
    featureGroup: drawnItems, // Allow editing of drawn items
  },
  draw: {
    polygon: true, // Allow drawing polygons
    polyline: true, // Allow drawing polylines
    rectangle: true, // Allow drawing rectangles
    circle: true, // Allow drawing circles
    marker: true, // Allow adding markers
    circlemarker: false, // Disable circle markers
  },
});

// Add the draw control to the map
map.addControl(drawControl);

// Event listener for when a shape is drawn
map.on("draw:created", function (e) {
  var layer = e.layer;

  // Add the drawn layer to the FeatureGroup
  drawnItems.addLayer(layer);

  // Add the drawn layer to overlayMaps for layer control
  var layerName = "Drawn Layer "; // Create a unique name for the layer
  overlayMaps[layerName] = layer; // Add layer to overlayMaps

  // Optionally, bind a popup or any other action here
  layer.bindPopup("You drew a shape!").openPopup();

  // Add the layer to the map and update the layer control
  layer.addTo(map);
  layerControl.remove(); // Remove old layer control
  layerControl = L.control.layers({}, overlayMaps).addTo(map); // Add updated layer control
});

let uploadBtn = document.getElementById("uploadBtn");
let showLayersBtn = document.getElementById("show-layers-btn");
let geoLayer = null;

// If the success message div is present, unhide the button
if (document.getElementById("successMessage")) {
  document.getElementById("showLayersBtn").style.display = "block";
}

// Define the EPSG:32646 projection
var utm46N = new L.Proj.CRS(
  "EPSG:32646",
  "+proj=utm +zone=46 +datum=WGS84 +units=m +no_defs",
  {
    resolutions: [256, 128, 64, 32, 16, 8, 4, 2, 1, 0.5],
  }
);
loadGeoJsonLayer(
  "map_layers/Drone_Restricted_Zones.geojson",
  "Restriction Zones"
);
// Create an array to hold the layers
let geoJsonLayers = [];
let overlayMaps = {}; // Initialize overlay maps

// Add event listener for the Show Layers button
showLayersBtn.addEventListener("click", function () {
  // Clear any existing layers from the map
  geoJsonLayers.forEach((layer) => {
    map.removeLayer(layer);
  });
  //Hello
  geoJsonLayers = []; // Reset the layers array
  overlayMaps = {}; // Reset overlayMaps

  // Load all layers and add them to overlayMaps
  Promise.all([
    loadGeoJsonLayer("map_layers/Input_File.geojson", "Input Layer"),
    loadGeoJsonLayer("map_layers/Grid_Intersect.geojson", "Intersection Layer"),
    loadGeoJsonLayer("map_layers/Grid_Buffer.geojson", "Final Grid"),
  ]).then(() => {
    // Remove the old layer control and add the updated one
    layerControl.remove();
    layerControl = L.control.layers({}, overlayMaps).addTo(map);
  });
});

// Automatically click the button if the success message is present
if (showLayersBtn && `{{ success_message | tojson }}`) {
  showLayersBtn.click();
}

// Initialize the layer control outside of the loadGeoJsonLayer function
let layerControl = L.control.layers({}, overlayMaps).addTo(map);

// Modify the loadGeoJsonLayer function to add each layer to overlayMaps and control layer toggle
function loadGeoJsonLayer(url, layerName) {
  return fetch(url)
    .then((response) => response.json())
    .then((data) => {
      let layer = L.Proj.geoJson(data, {
        onEachFeature: function (feature, layer) {
          let popupContent = `<h3>${layerName}</h3>`;
          if (feature.properties.download_link) {
            popupContent += `<br><a href="${feature.properties.download_link}" target="_blank" rel="noopener noreferrer" class="download-link">Download KML</a>`;
          }
          layer.bindPopup(popupContent);
        },
      });

      layer.addTo(map);
      geoJsonLayers.push(layer);
      overlayMaps[layerName] = layer; // Use custom layer name in overlay maps

      map.fitBounds(layer.getBounds());
    })
    .catch((error) => console.error("Error loading GeoJSON:", error));
}

// Prevent default behavior for download links
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("download-link")) {
    e.preventDefault(); // Prevent default action
    // Open the link in a new tab
    window.open(e.target.href, "_blank");
  }
});

// Wait for the DOM to load before making changes
document.addEventListener("DOMContentLoaded", function () {
  // Select the attribution control element
  let attributionControl = document.querySelector(
    ".leaflet-control-attribution"
  );
});

new L.basemapsSwitcher(
  [
    {
      layer: L.tileLayer(
        "http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga",
        {
          attribution:
            'Dveloped By: &copy; <a href="https://www.linkedin.com/in/m-mashrur-zaman-7b3abb155/">M. Mashrur Zaman</a> ',
        }
      ).addTo(map),
      icon: "/static/image/img1.PNG",
      name: "Google Hybrid",
    },
    {
      layer: L.tileLayer(
        "http://mt0.google.com/vt/lyrs=m,traffic,transit&hl=en&x={x}&y={y}&z={z}&s=Ga",
        {
          attribution:
            'Dveloped By: &copy; <a href="https://www.linkedin.com/in/m-mashrur-zaman-7b3abb155/">M. Mashrur Zaman</a> ',
        }
      ),
      icon: "/static/image/img2.PNG",
      name: "Google Street",
    },
    {
      layer: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          'Dveloped By: &copy; <a href="https://www.linkedin.com/in/m-mashrur-zaman-7b3abb155/">M. Mashrur Zaman</a> ',
      }), //DEFAULT MAP
      icon: "/static/image/img3.PNG",
      name: "OSM Map",
    },
    {
      layer: L.tileLayer(
        "http://services.arcgisonline.com/arcgis/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        {
          attribution:
            'Dveloped By: &copy; <a href="https://www.linkedin.com/in/m-mashrur-zaman-7b3abb155/">M. Mashrur Zaman</a> ',
        }
      ),
      icon: "/static/image/img4.PNG",
      name: "ESRI Topomap",
    },
    {
      layer: L.tileLayer(
        "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png",
        {
          attribution:
            'Dveloped By: &copy; <a href="https://www.linkedin.com/in/m-mashrur-zaman-7b3abb155/">M. Mashrur Zaman</a> ',
        }
      ),
      icon: "/static/image/img5.PNG",
      name: "World Terrain",
    },
    {
      layer: L.tileLayer(
        "https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg",
        {
          attribution:
            'Dveloped By: &copy; <a href="https://www.linkedin.com/in/m-mashrur-zaman-7b3abb155/">M. Mashrur Zaman</a> ',
        }
      ),
      icon: "/static/image/img6.PNG",
      name: "World Colormap",
    },
  ],
  { position: "bottomright" }
).addTo(map);

// Event listener for the Save button
document.getElementById("saveBtn").addEventListener("click", function () {
  // Create an empty GeoJSON FeatureCollection
  var geoJson = {
    type: "FeatureCollection",
    features: [],
  };

  // Loop through drawn items and add them to the GeoJSON
  drawnItems.eachLayer(function (layer) {
    if (layer instanceof L.Circle) {
      // Convert the circle to an approximate polygon
      const circleGeoJson = layer.toGeoJSON();
      circleGeoJson.properties.radius = layer.getRadius();
      geoJson.features.push(circleGeoJson);
    } else {
      geoJson.features.push(layer.toGeoJSON());
    }
  });

  // Convert GeoJSON to KML
  var kml = geojson2kml(geoJson);

  // Convert KML to a Blob
  var blob = new Blob([kml], {
    type: "application/vnd.google-earth.kml+xml",
  });

  // Create a link element to trigger download
  var link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "drawn_shapes.kml"; // Default file name
  link.click(); // Trigger download
});

// Function to convert GeoJSON to KML
function geojson2kml(geoJson) {
  // KML header
  let kml = `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
`;

  // Loop through GeoJSON features
  geoJson.features.forEach(function (feature) {
    const { geometry, properties } = feature;
    kml += `<Placemark>
  <name>${properties.name || "Unnamed"}</name>
  <description>${properties.description || ""}</description>
  <${
    geometry.type === "Point" && properties.radius ? "Polygon" : geometry.type
  }>
`;

    // Process coordinates based on geometry type
    if (geometry.type === "Point" && properties.radius) {
      // Circle approximation
      const center = geometry.coordinates;
      const radius = properties.radius;
      const numPoints = 64; // Number of points to approximate the circle
      let coordinates = [];

      for (let i = 0; i < numPoints; i++) {
        const angle = (i * 2 * Math.PI) / numPoints;
        const dx = (radius * Math.cos(angle)) / 111320;
        const dy = (radius * Math.sin(angle)) / 111320;
        const lon = center[0] + dx / Math.cos((center[1] * Math.PI) / 180);
        const lat = center[1] + dy;
        coordinates.push(`${lon},${lat}`);
      }
      // Close the ring
      coordinates.push(coordinates[0]);
      kml += `<outerBoundaryIs>
        <LinearRing>
          <coordinates>${coordinates.join(" ")}</coordinates>
        </LinearRing>
      </outerBoundaryIs>`;
    } else if (geometry.type === "Point") {
      kml += `<coordinates>${geometry.coordinates.join(",")}</coordinates>`;
    } else if (geometry.type === "LineString") {
      kml += `<coordinates>${geometry.coordinates
        .map((coord) => coord.join(","))
        .join(" ")}</coordinates>`;
    } else if (geometry.type === "Polygon") {
      kml += `<outerBoundaryIs>
        <LinearRing>
          <coordinates>${geometry.coordinates[0]
            .map((coord) => coord.join(","))
            .join(" ")}</coordinates>
        </LinearRing>
      </outerBoundaryIs>`;
    }
    kml += `</${
      geometry.type === "Point" && properties.radius ? "Polygon" : geometry.type
    }>
</Placemark>
`;
  });

  // KML footer
  kml += `</Document>
</kml>`;

  return kml;
}

L.control
  .measure({
    position: "topleft",
  })
  .addTo(map);

// 2. using action directly
var measureAction = new L.MeasureAction(map, {
  model: "distance", // 'area' or 'distance', default is 'distance'
});
// measureAction.setModel('area');
measureAction.disable();

L.Measure = {
  linearMeasurement: "Distance measurement",
  areaMeasurement: "Area measurement",
  start: "Start",
  meter: "m",
  meterDecimals: 0,
  kilometer: "km",
  kilometerDecimals: 2,
  squareMeter: "m²",
  squareMeterDecimals: 0,
  squareKilometers: "km²",
  squareKilometersDecimals: 2,
};

L.Control.geocoder({
  position: "topleft",
}).addTo(map);
