import argparse
import csv
import io
import os
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+")

def main(files):
    """Files must be sorted lexicographically
    Filenames must be <row>-<colum>.txt.
    000-000.txt
    000-001.txt
    001-000.txt
    etc...
    """
    rows = []
    for f in files:
        directory, filename = os.path.split(f)
        with open(f) as of:
            txt = of.read()
        row, column = map(int, filename.split(".")[0].split("-"))
        if row == len(rows):
            rows.append([])
        rows[row].append(txt)

    csv_file = io.StringIO()
    writer = csv.writer(csv_file)
    writer.writerows(rows)
    print(csv_file.getvalue())

if __name__ == "__main__":
    args = parser.parse_args()
    files = args.files
    files.sort()
    main(files)
