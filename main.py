# Copyright 2024 - TurainAI
#
# GEX Tool - Geotiff EXtraction Tool
#
# Converts USGS GeoTIFF files to PNG with a 0 - 30k elevation scale, and then cuts it into tiles.
# GeoTIFF conversions are saved in the input_dir. The resulting tiles, if any, are saved in output_dir.
#
#  Currently REQUIRES the gdalinfo and gdal_translate binaries.
#  TODO: Remove dependency on binaries.
#
# Flags:
#     "--input_dir", help="Directory containing GeoTIFF files to be GEX'd.", type=str
#     "--output_dir", help="Directory to save the output tiles.", type=str
#     "--tile_size", help="Pixel width/height of tiles to be extracted from GeoTIFFs.", type=int
#     "--no-alpha", help="Whether to save tiles with any transparent pixels.", type=bool
#     "--skip-tif", help="Skips GeoTIFF file processing.", type=bool
#     "--debug", help="Enables verbose logging.", type=bool
#

import os
import re
import math
import argparse
import warnings
from PIL import Image

debug = False
converted_suffix = "_GEXD"
converted_format = "png"
tile_format = "png"


def has_transparency(img):
    pixels = list(img.getdata())
    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                print("Transparency detected in tile. P-mode detected.")
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            print("Transparency detected in tile. RGBA image detected.")
            return True

    for pixel in pixels:
        if pixel == 0:
            print("Transparency detected in tile. 0-value pixel detected.")
            return True

    print("Transparency NOT detected in tile.")
    return False


def cut_tiles(input_dir, filename, output_dir, tile_size, no_alpha):
    print(f"Cutting tiles from {filename}")
    filepath = os.path.join(input_dir, filename)
    img = Image.open(filepath)
    width, height = img.size
    tile_count = 0
    should_save_tile = True
    for x in range(0, width, tile_size):
        for y in range(0, height, tile_size):
            tile = img.crop((x, y, x + (tile_size - 1), y + (tile_size - 1)))
            x_f = f'{x:0>4}'
            y_f = f'{y:0>4}'
            suffix = f'_{x_f}_{y_f}'
            tile_name = filename.split('.')[0] + suffix
            # Check if alpha transparency is allowed and set should_save_tile accordingly.
            if no_alpha:
                should_save_tile = not has_transparency(tile)

            # Save tile, if we should.
            if should_save_tile:
                if debug:
                    print(f"DEBUG: saving tile {tile_name}.{tile_format}")
                tile_count += 1
                tile_path = os.path.join(output_dir, f"{tile_name}.{tile_format}")
                # Check P mode before saving as PNG.
                # if tile_format.casefold() == "png".casefold():
                #    if tile.mode != 'RGB':
                #        tile = tile.convert('RGB')
                tile.save(tile_path)

    return tile_count


def convert_geotiff(input_dir, filename, output_dir):
    filepath = os.path.join(input_dir, filename)
    print(f"Converting: {filename}")

    # Get min/max from gdalinfo
    cmd = f'gdalinfo -mm {filepath}'
    stream = os.popen(cmd)
    output = stream.read()
    match = re.search(r'Max=([0-9]*[.][0-9]*),([0-9]*[.][0-9]*)', output)
    if match is None:
        print("Error: no min/max elevation found with gdalinfo! Skipping GeoTIFF!")
        return
    else:
        min = math.floor(float(match.group(1)))
        max = math.floor(float(match.group(2)))
    if debug:
        print(f"DEBUG: elevation min: {min}")
        print(f"DEBUG: elevation max: {max}")

    # Convert to PNG with correct scaling (0 to 30k)
    # TODO: use GDAL python files instead?
    output_filename = filename.split('.')[0] + f"{converted_suffix}.{converted_format}"
    output_path = os.path.join(output_dir, output_filename)
    cmd = f'gdal_translate -of {converted_format} -ot UInt16 -scale {min} {max} 0 30000 {filepath} {output_path}'
    if debug:
        print(f"Executing: {cmd}")
    stream = os.popen(cmd)
    stream.read()
    if os.path.isfile(output_path):
        img = Image.open(output_path)
        width, height = img.size
        # TODO: add a --scale_ratio flag and use it here.
        img = img.resize((int(width / 2), int(height / 2)))
        resize_filename = filename.split('.')[0] + f"{converted_suffix}_resized.{converted_format}"
        img.save(os.path.join(output_dir, resize_filename))
        # Clean up non-scaled file.
        os.remove(output_path)
        print(f"File GEXD!!! Hell yeah! {output_path}")
        return output_filename
    else:
        print("Error: converted file not found! gdal_translate may have failed to complete!")
        return


def gextool(input_dir, output_dir, tile_size, no_alpha, skip_tif):
    print("Running GEXtool! Your friendly neighborhood Geotiff EXtraction tool.")

    # Check if output_dir exists, if not try to create it.
    if not os.path.isdir(output_dir):
        print(f"output_dir not found, trying to create it...")
        os.mkdir(output_dir)
        if not os.path.isdir(output_dir):
            print(f"Error: failed to create output_dir: {output_dir}")
            print("Please create output_dir and try again, or specify an dir that already exists.")
        else:
            print(f"Successfully created output_dir: {output_dir}")

    total_tif_count = 0
    if skip_tif:
        print("Skipping GeoTIFF files.")
    else:
        # Calculate how many TIFs are present in input_dir.
        for filename in os.listdir(input_dir):
            if filename.endswith(".tif"):
                total_tif_count += 1
        if total_tif_count > 0:
            print(f"{total_tif_count} TIF files found! Nice!")

        # Process GeoTIFFs
        loop_count = 0
        print("Processing GeoTIFFs...")
        for filename in os.listdir(input_dir):
            if filename.endswith(".tif"):
                gexd_file = filename.split(',')[0] + f'{converted_suffix}.{converted_format}'
                if os.path.isfile(gexd_file):
                    print(f"Input file has already been GEXD: {gexd_file}")
                else:
                    loop_count += 1
                    print(f"Processing {loop_count}/{total_tif_count}")
                    convert_geotiff(input_dir, filename, input_dir)  # Saves to the input_dir


    # Calculate how many GEX'd files are present in input_dir
    total_gexd_count = 0
    for filename in os.listdir(input_dir):
        if filename.endswith(f"{converted_suffix}.{converted_format}"):
            total_gexd_count += 1
    if total_gexd_count > 0:
        print(f"{total_gexd_count} GEX'd PNG files found.")

    tile_count = 0
    # Process GEX'd files
    print("Cutting tiles from GEX'd files...")
    for filename in os.listdir(input_dir):
        # TODO: Once flag for scaling GEX'd files is done, use it to set the expected format string in a var and call that.
        if filename.endswith(f"{converted_suffix}_resized.{converted_format}"):
            count = cut_tiles(input_dir, filename, output_dir, tile_size, no_alpha)
            tile_count += count

    print(f"{total_tif_count} GEX'd file(s) processed.")
    print(f"{tile_count} tile(s) generated at {tile_size}x{tile_size}.")
    if no_alpha:
        print("Tiles were NOT allowed to have any pixels with alpha transparency.")
    else:
        print("Tiles were allowed to have pixels with alpha transparency.")
    print("GEXtool is done!")


if __name__ == '__main__':
    # Suppress the DecompressionBombWarning since we're using very large TIFF files that trigger it.
    # TODO: update this to raise the limit instead of suppressing the warning entirely. Not a security issue since this
    # is only intended to run GeoTIFF files from the USGS.
    warnings.simplefilter('ignore', Image.DecompressionBombWarning)

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", help="Directory containing GeoTIFF files to be GEX'd.", type=str)
    parser.add_argument("--output_dir", help="Directory to save the output tiles.", type=str)
    parser.add_argument("--tile_size", help="Pixel width/height of tiles to be extracted from GeoTIFFs.", type=int)
    parser.add_argument("--debug", help="Pixel width/height of tiles to be extracted from GeoTIFFs.", type=bool)
    parser.add_argument("--no-alpha", help="Whether to allow resulting tiles to contain any transparent pixels.",
                        type=bool)
    parser.add_argument("--skip-tif", help="Whether to skip any GeoTIFFs and process only GEX'd PNGs.",
                        type=bool)
    args = parser.parse_args()
    debug = args.debug

    if debug:
        print(f"DEBUG: input_dir: {args.input_dir}")
        print(f"DEBUG: output_dir: {args.output_dir}")
        print(f"DEBUG: tile_size: {args.tile_size}")

    gextool(args.input_dir, args.output_dir, args.tile_size, args.no_alpha, args.skip_tif)
