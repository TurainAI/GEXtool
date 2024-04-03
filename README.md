# GEXtool
GEX Tool - Geotiff EXtraction Tool

Converts USGS GeoTIFF files to PNG with a 0 - 30k elevation scale, and then cuts it into tiles.
GeoTIFF conversions are saved in the input_dir. The resulting tiles, if any, are saved in output_dir.

Currently REQUIRES the gdalinfo and gdal_translate binaries. See gdal.org

Flags:
  --input_dir, Directory containing GeoTIFF files to be GEX'd.
  --output_dir, Directory to save the output tiles.
  --tile_size, Pixel width/height of tiles to be extracted from GeoTIFFs.
  --no-alpha, Whether to save tiles with any transparent pixels.
  --skip-tif, Skips GeoTIFF file processing.
  --debug, Enables verbose logging.
