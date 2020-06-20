"""
Make Icon From PNGs v1.0 Copyright (c) 2020 Mikael Klasson.

Very simple program to make a .ico icon file from one or more PNG files.

I'm setting the following fields in the .ico to 0, which doesn't seem to be
causing any problems: "number of colors in palette", "color planes", and
"bits per pixel".

Format reference: https://en.wikipedia.org/wiki/ICO_(file_format)

License: MIT
"""

import argparse

parser = argparse.ArgumentParser(
    description="Make .ico icon file from one or more PNGs. The images "
    "appear in the argument order.")
parser.add_argument("png_file", help="input PNG file(s)", nargs="+")
parser.add_argument("-o", "--output_file", required=True,
                    help="name of .ico file to create")
args = parser.parse_args()


class Png:
    """Loads a PNG file and extracts basic header data."""
    width = 0
    height = 0
    bit_depth = 0
    has_palette = False
    file_data = bytes(0)
    file_size = 0

    def __init__(self, filename):
        with open(filename, "rb") as f:
            header = f.read(8)
            if header != b"\x89PNG\r\n\x1a\n":
                raise RuntimeError("Incorrect PNG header", filename, header)
            f.seek(4, 1)
            chunk_type = f.read(4)
            if chunk_type != b"IHDR":
                raise RuntimeError("Incorrect PNG chunk", filename, chunk_type)
            self.width = int.from_bytes(f.read(4), byteorder="big")
            self.height = int.from_bytes(f.read(4), byteorder="big")
            self.bit_depth = int.from_bytes(f.read(1), byteorder="big")
            color_type = int.from_bytes(f.read(1), byteorder="big")
            self.has_palette = color_type == 3
            f.seek(0)
            self.file_data = f.read()
            self.file_size = f.tell()


with open(args.output_file, "wb") as icon_file:
    # Write .ico header.
    icon_file.write(b"\x00\x00")
    icon_file.write(b"\x01\x00")    # 1 == .ico type
    image_count = len(args.png_file)
    icon_file.write(image_count.to_bytes(2, byteorder="little"))

    # Write empty image directory.
    image_directory_offset = 6
    image_directory_size = 16 * image_count
    icon_file.write(bytes(image_directory_size))
    png_data_offset = image_directory_offset + image_directory_size

    for png_filename in args.png_file:
        icon_file.seek(image_directory_offset)
        png = Png(png_filename)
        print("Adding %s: %dx%d" % (png_filename, png.width, png.height))
        if png.width > 256 or png.height > 256:
            raise RuntimeError("Too big PNG image",
                               args.png_file, png.width, png.height)

        # Write ICONDIRENTRY.
        icon_file.write((png.width % 256).to_bytes(1, byteorder="little"))
        icon_file.write((png.height % 256).to_bytes(1, byteorder="little"))
        colors_in_palette = 0
        icon_file.write(colors_in_palette.to_bytes(1, byteorder="little"))
        icon_file.write(b"\x00")
        color_planes = 0
        icon_file.write(color_planes.to_bytes(2, byteorder="little"))
        bits_per_pixel = 0
        icon_file.write(bits_per_pixel.to_bytes(2, byteorder="little"))
        icon_file.write(png.file_size.to_bytes(4, byteorder="little"))
        icon_file.write(png_data_offset.to_bytes(4, byteorder="little"))

        # Copy entire PNG to icon file.
        icon_file.seek(png_data_offset)
        icon_file.write(png.file_data)

        # Update offsets for next PNG.
        png_data_offset += png.file_size
        image_directory_offset += 16
