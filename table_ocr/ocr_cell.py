import sys

import cv2
import pytesseract

def crop_to_text(image):
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (4, 4))
    opened = cv2.morphologyEx(~image, cv2.MORPH_OPEN, kernel)

    contours, hierarchy = cv2.findContours(opened, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    bounding_rects = [cv2.boundingRect(c) for c in contours]
    # The largest contour is certainly the text that we're looking for.
    largest_rect = max(bounding_rects, key=lambda r: r[2] * r[3])
    x, y, w, h = largest_rect
    cropped = image[y:y+h, x:x+w]
    bordered = cv2.copyMakeBorder(cropped, 5, 5, 5, 5, cv2.BORDER_CONSTANT, None, 255)
    return bordered
def ocr_image(image, config):
    cropped = crop_to_text(image)
    return pytesseract.image_to_string(
        ~cropped,
        config=config
    )

def main(f):
    image = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    print(ocr_image(image, "--psm 7"))

if __name__ == "__main__":
    main(sys.argv[1])
