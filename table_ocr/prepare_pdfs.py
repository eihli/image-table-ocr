import argparse
import logging
import os
import re
import subprocess
import sys

from table_ocr.util import working_dir, make_tempdir


def get_logger():
    logger = logging.getLogger(__name__)
    lvl = os.environ.get("PY_LOG_LVL", "info").upper()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    handler.setLevel(lvl)
    logger.setLevel(lvl)
    return logger

logger = get_logger()

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+")

def main(files):
    pdf_images = []
    for f in files:
        pdf_images.append((f, pdf_to_images(f)))

    for pdf, images in pdf_images:
        for image in images:
            preprocess_img(image)

    for pdf, images in pdf_images:
        print("{}\n{}\n".format(pdf, "\n".join(images)))


def pdf_to_images(pdf_filepath):
    """
    Turn a pdf into images
    """
    directory, filename = os.path.split(pdf_filepath)
    with working_dir(directory):
        image_filenames = pdfimages(pdf_filepath)

    # Since pdfimages creates a number of files named each for there page number
    # and doesn't return us the list that it created
    return [os.path.join(directory, f) for f in image_filenames]


def pdfimages(pdf_filepath):
    """
    Uses the `pdfimages` utility from Poppler
    (https://poppler.freedesktop.org/). Creates images out of each page. Images
    are prefixed by their name sans extension and suffixed by their page number.

    This should work up to pdfs with 999 pages since find matching files in dir
    uses 3 digits in its regex.
    """
    directory, filename = os.path.split(pdf_filepath)
    filename_sans_ext = filename.split(".pdf")[0]
    subprocess.run(["pdfimages", "-png", pdf_filepath, filename.split(".pdf")[0]])
    image_filenames = find_matching_files_in_dir(filename_sans_ext, directory)
    logger.debug("Converted {} into files:\n{}".format(pdf_filepath, "\n".join(image_filenames)))
    return image_filenames


def find_matching_files_in_dir(file_prefix, directory):
    files = [
        filename
        for filename in os.listdir(directory)
        if re.match(r"{}-\d{{3}}.*\.png".format(re.escape(file_prefix)), filename)
    ]
    return files
def preprocess_img(filepath):
    """
    Processing that involves running shell executables,
    like mogrify to rotate.
    """
    rotate = get_rotate(filepath)
    logger.debug("Rotating {} by {}.".format(filepath, rotate))
    mogrify(filepath, rotate)


def get_rotate(image_filepath):
    output = (
        subprocess.check_output(["tesseract", "--psm", "0", image_filepath, "-"])
        .decode("utf-8")
        .split("\n")
    )
    output = next(l for l in output if "Rotate: " in l)
    output = output.split(": ")[1]
    return output


def mogrify(image_filepath, rotate):
    subprocess.run(["mogrify", "-rotate", rotate, image_filepath])

if __name__ == "__main__":
    args = parser.parse_args()
    main(args.files)
