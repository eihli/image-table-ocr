import os
import sys

import cv2
import pytesseract

def crop_to_text(image):
    MAX_COLOR_VAL = 255
    BLOCK_SIZE = 15
    SUBTRACT_FROM_MEAN = -2

    img_bin = cv2.adaptiveThreshold(
        ~image,
        MAX_COLOR_VAL,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        BLOCK_SIZE,
        SUBTRACT_FROM_MEAN,
    )

    # Get rid of littl noise.
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    opened = cv2.morphologyEx(img_bin, cv2.MORPH_OPEN, kernel)

    # Dilate so each digit is connected, so we can get a bounding rectangle
    # around all of the digits as one contour. This will make the bounding
    # rectangle 8 pixels wider on the left and right, so we'll need to crop that
    # out at the end so that we don't pick up stray border pixels.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (16, 1))
    dilated = cv2.dilate(opened, kernel)

    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    bounding_rects = [cv2.boundingRect(c) for c in contours]

    if bounding_rects:
        # The largest contour is certainly the text that we're looking for.
        largest_rect = max(bounding_rects, key=lambda r: r[2] * r[3])
        x, y, w, h = largest_rect
        # Commas sometimes go a little below the bounding box and we don't want
        # to lost them or turn them into periods.
        img_h, img_w = image.shape
        cropped = image[y:min(img_h, y+h+6), x+8:x+w-8]
    else:
        cropped = image
    bordered = cv2.copyMakeBorder(cropped, 5, 5, 5, 5, cv2.BORDER_CONSTANT, None, 255)
    return bordered
def ocr_image(image, config):
    return pytesseract.image_to_string(
        image,
        config=config
    )

def main(f):
    directory, filename = os.path.split(f)
    filename_sans_ext, ext = os.path.splitext(filename)
    image = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    cropped = crop_to_text(image)
    ocr_data_dir = os.path.join(directory, "ocr_data")
    os.makedirs(ocr_data_dir, exist_ok=True)
    out_imagepath = os.path.join(ocr_data_dir, filename)
    out_txtpath = os.path.join(ocr_data_dir, "{}.gt.txt".format(filename_sans_ext))
    cv2.imwrite(out_imagepath, cropped)
    txt = ocr_image(cropped, "--psm 7")
    with open(out_txtpath, "w") as txt_file:
        txt_file.write(txt)

if __name__ == "__main__":
    main(sys.argv[1])
