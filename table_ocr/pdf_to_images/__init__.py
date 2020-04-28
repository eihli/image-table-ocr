import os
import re
import subprocess

from table_ocr.util import get_logger, working_dir

logger = get_logger(__name__)

# Wrapper around the Poppler command line utility "pdfimages" and helpers for
# finding the output files of that command.
def pdf_to_images(pdf_filepath):
    """
    Turn a pdf into images
    Returns the filenames of the created images sorted lexicographically.
    """
    directory, filename = os.path.split(pdf_filepath)
    image_filenames = pdfimages(pdf_filepath)

    # Since pdfimages creates a number of files named each for there page number
    # and doesn't return us the list that it created
    return sorted([os.path.join(directory, f) for f in image_filenames])


def pdfimages(pdf_filepath):
    """
    Uses the `pdfimages` utility from Poppler
    (https://poppler.freedesktop.org/). Creates images out of each page. Images
    are prefixed by their name sans extension and suffixed by their page number.

    This should work up to pdfs with 999 pages since find matching files in dir
    uses 3 digits in its regex.
    """
    directory, filename = os.path.split(pdf_filepath)
    if not os.path.isabs(directory):
        directory = os.path.abspath(directory)
    filename_sans_ext = filename.split(".pdf")[0]

    # pdfimages outputs results to the current working directory
    with working_dir(directory):
        subprocess.run(["pdfimages", "-png", filename, filename.split(".pdf")[0]])

    image_filenames = find_matching_files_in_dir(filename_sans_ext, directory)
    logger.debug(
        "Converted {} into files:\n{}".format(pdf_filepath, "\n".join(image_filenames))
    )
    return image_filenames


def find_matching_files_in_dir(file_prefix, directory):
    files = [
        filename
        for filename in os.listdir(directory)
        if re.match(r"{}-\d{{3}}.*\.png".format(re.escape(file_prefix)), filename)
    ]
    return files

def preprocess_img(filepath, tess_params=None):
    """Processing that involves running shell executables,
    like mogrify to rotate.

    Uses tesseract to detect rotation.

    Orientation and script detection is only available for legacy tesseract
    (--oem 0). Some versions of tesseract will segfault if you let it run OSD
    with the default oem (3).
    """
    if tess_params is None:
        tess_params = ["--psm", "0", "--oem", "0"]
    rotate = get_rotate(filepath, tess_params)
    logger.debug("Rotating {} by {}.".format(filepath, rotate))
    mogrify(filepath, rotate)


def get_rotate(image_filepath, tess_params):
    """
    """
    tess_command = ["tesseract"] + tess_params + [image_filepath, "-"]
    output = (
        subprocess.check_output(tess_command)
        .decode("utf-8")
        .split("\n")
    )
    output = next(l for l in output if "Rotate: " in l)
    output = output.split(": ")[1]
    return output


def mogrify(image_filepath, rotate):
    subprocess.run(["mogrify", "-rotate", rotate, image_filepath])
