import argparse

from table_ocr.util import working_dir, make_tempdir, get_logger
from table_ocr.pdf_to_images import pdf_to_images, preprocess_img

logger = get_logger(__name__)

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


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.files)
