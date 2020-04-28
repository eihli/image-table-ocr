import os
import cv2

def find_tables(image):
    BLUR_KERNEL_SIZE = (17, 17)
    STD_DEV_X_DIRECTION = 0
    STD_DEV_Y_DIRECTION = 0
    blurred = cv2.GaussianBlur(~image, BLUR_KERNEL_SIZE, STD_DEV_X_DIRECTION, STD_DEV_Y_DIRECTION)
    MAX_COLOR_VAL = 255
    BLOCK_SIZE = 15
    SUBTRACT_FROM_MEAN = -1

    img_bin = cv2.adaptiveThreshold(
        blurred,
        MAX_COLOR_VAL,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        BLOCK_SIZE,
        SUBTRACT_FROM_MEAN,
    )
    vertical = horizontal = img_bin.copy()

    # Dilate to get rid of anything that is not a long line of a table. The
    # higher the scale, the shorter the lines that remain. You might pick up big
    # characters or other noise. The lower the scale, the more you'll restrict
    # yourself to getting only long lines.
    # With a scale of 10, any line that is shorter than 1/10th the width or height
    # of the image will be removed.
    SCALE = 10
    image_width, image_height = horizontal.shape
    horizontally_opened = cv2.morphologyEx(
        img_bin, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (image_width // SCALE, 1))
    )
    vertically_opened = cv2.morphologyEx(
        img_bin, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, image_height // SCALE))
    )

    mask = horizontally_opened + vertically_opened
    contours, heirarchy = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
    )

    MIN_TABLE_AREA = 1e5
    contours = [c for c in contours if cv2.contourArea(c) > MIN_TABLE_AREA]
    perimeter_lengths = [cv2.arcLength(c, True) for c in contours]
    epsilons = [0.1 * p for p in perimeter_lengths]
    approx_polys = [cv2.approxPolyDP(c, e, True) for c, e in zip(contours, epsilons)]
    bounding_rects = [cv2.boundingRect(a) for a in approx_polys]

    # The link where a lot of this code was borrowed from recommends an
    # additional step to check the number of "joints" inside this bounding rectangle.
    # A table should have a lot of intersections. We might have a rectangular image
    # here though which would only have 4 intersections, 1 at each corner.
    # Leaving that step as a future TODO if it is ever necessary.
    images = [image[y:y+h, x:x+w] for x, y, w, h in bounding_rects]
    return images

def main(files):
    results = []
    for f in files:
        directory, filename = os.path.split(f)
        image = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
        tables = find_tables(image)
        files = []
        filename_sans_extension = os.path.splitext(filename)[0]
        if tables:
            os.makedirs(os.path.join(directory, filename_sans_extension), exist_ok=True)
        for i, table in enumerate(tables):
            table_filename = "table-{:03d}.png".format(i)
            table_filepath = os.path.join(
                directory, filename_sans_extension, table_filename
            )
            files.append(table_filepath)
            cv2.imwrite(table_filepath, table)
        if tables:
            results.append((f, files))
    # Results is [[<input image>, [<images of detected tables>]]]
    return results
