import argparse
import os

from table_ocr.ocr_to_csv import text_files_to_csv

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+")


def main(files):
    print(text_files_to_csv(files))


if __name__ == "__main__":
    args = parser.parse_args()
    files = args.files
    files.sort()
    main(files)
