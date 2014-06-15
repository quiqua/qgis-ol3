QGIS to OpenLayers 3
=====================

Converts your QGIS project into an OpenLayers 3 map

It includes the following features:

- Built-in preview.

- Support for both raster and vector layers.

- Support for WMS/WFS layers.

- Support for QGIS groups, which are replicated in the OL3 map.

- Symbology exporting, including:

	- Basic styles for points, lines and polygons (single symbol, categorized, graduated).

	- SVG icons for point markers.
	
	- Labeling.
	
	- Scale dependent visibility.
	
	- Multi-layered symbology (several symbols for a single feature).
	
	- Transparency

- Template-based, so new templates can be easily be created

- Automatically minifies GeoJSON output files and removes unused attributes.

- Add layer legend.

- Add layers list.

- Add scale bar.

- Add feature info popup for selected layers, based on a given field, on hover or on click. 

- Add highlight function to highlight features when passing the mouse pointer over them.

Usage is documented `here <./doc/usage.rst>`_.
