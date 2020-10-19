import os
import sys

import requests
import table_ocr.util
import table_ocr.extract_tables
import table_ocr.extract_cells
import table_ocr.ocr_image
import table_ocr.ocr_to_csv
def download_image_to_tempdir(url, filename=None):
    if filename is None:
        filename = os.path.basename(url)
    response = requests.get(url, stream=True)
    tempdir = table_ocr.util.make_tempdir("demo")
    filepath = os.path.join(tempdir, filename)
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content():
            f.write(chunk)
    return filepath

def main(url):
    image_filepath = download_image_to_tempdir(url)
    image_tables = table_ocr.extract_tables.main([image_filepath])
    print("Running `{}`".format(f"extract_tables.main([{image_filepath}])."))
    print("Extracted the following tables from the image:")
    print(image_tables)
    for image, tables in image_tables:
        print(f"Processing tables for {image}.")
        for table in tables:
            print(f"Processing table {table}.")
            cells = table_ocr.extract_cells.main(table)
            ocr = [
                table_ocr.ocr_image.main(cell, None)
                for cell in cells
            ]
            print("Extracted {} cells from {}".format(len(ocr), table))
            print("Cells:")
            for c, o in zip(cells[:3], ocr[:3]):
                with open(o) as ocr_file:
                    # Tesseract puts line feeds at end of text.
                    # Stript it out.
                    text = ocr_file.read().strip()
                    print("{}: {}".format(c, text))
            # If we have more than 3 cells (likely), print an ellipses
            # to show that we are truncating output for the demo.
            if len(cells) > 3:
                print("...")
            return table_ocr.ocr_to_csv.text_files_to_csv(ocr)

if __name__ == "__main__":
    csv_output = main(sys.argv[1])
    print()
    print("Here is the entire CSV output:")
    print()
    print(csv_output)
