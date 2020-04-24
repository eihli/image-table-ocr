import argparse
import math
import os
import sys

import cv2

from table_ocr.ocr_image import crop_to_text, ocr_image

description="""Takes a single argument that is the image to OCR.
Remaining arguments are passed directly to Tesseract.

Attempts to make OCR more accurate by performing some modifications on the image.
Saves the modified image and the OCR text in an `ocr_data` directory.
Filenames are of the format for training with tesstrain."""
parser = argparse.ArgumentParser(description=description)
parser.add_argument("image", help="filepath of image to perform OCR")

def main(image_file, tess_args):
    directory, filename = os.path.split(image_file)
    filename_sans_ext, ext = os.path.splitext(filename)
    image = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    cropped = crop_to_text(image)
    ocr_data_dir = os.path.join(directory, "ocr_data")
    os.makedirs(ocr_data_dir, exist_ok=True)
    out_imagepath = os.path.join(ocr_data_dir, filename)
    out_txtpath = os.path.join(ocr_data_dir, "{}.gt.txt".format(filename_sans_ext))
    cv2.imwrite(out_imagepath, cropped)
    txt = ocr_image(cropped, " ".join(tess_args))
    print(txt)
    with open(out_txtpath, "w") as txt_file:
        txt_file.write(txt)

if __name__ == "__main__":
    args, tess_args = parser.parse_known_args()
    main(args.image, tess_args)
