# GEXtool
GEX Tool - Geotiff EXtraction Tool

Converts USGS GeoTIFF files to PNG, and then cuts them into the desired tile sizes for training.
Converted PNGs are saved next to originals in the input_dir. 
The resulting tiles, if any, are saved in output_dir.

Currently requires the gdalinfo and gdal_translate binaries:\
sudo apt install gdal-bin

Flags:\
--input_dir, Directory containing GeoTIFF files to be GEX'd.\
--output_dir, Directory to save the output tiles.\
--tile_size, Pixel width/height of tiles to be extracted from GeoTIFFs.\
--no-alpha, Whether to save tiles with any transparent pixels.\
--skip-tif, Skips GeoTIFF file processing.\
--debug, Enables verbose logging.\

Example output tile:
![example output](https://github.com/TurainAI/GEXtool/blob/main/USGS_one_meter_x42y531_WA_Olympic_Peninsula_2013_GEXD_resized_3072_2048.png?raw=true)
