from copy import copy
import cv2
import os

import cv2

def label_cells(image, cells):
    image = image.copy()
    rows = sort_cells(cells)
    FONT_SCALE = 0.7
    FONT_COLOR = (127, 127, 127)
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            x, y, w, h = cell
            cv2.putText(
                image,
                "{},{}".format(i, j),
                (int(x + w - w / 2), int(y + h - h / 2)),
                cv2.FONT_HERSHEY_SIMPLEX,
                FONT_SCALE,
                FONT_COLOR,
                2,
            )
    return image
from copy import copy
def draw_bounding_rects(image, rects):
    image = image.copy()
    for x, y, w, h in rects:
        cv2.rectangle(image, (x, y), (x+w, y+h), (127, 127, 127), 2)
    return image
def extract_cell_images_from_table(image):
    blurred = gaus_blur(~image)
    thresholded = adapt_thresh(blurred)

    # Find just the long lines in the image. This is the table.
    masked_to_long_lines = mask_to_long_lines(thresholded)

    # Dilate to try connecting border joins so each cell
    # is a separate contour.
    connected = connect_border_joints(masked_to_long_lines)

    # The borders *still* might not be connected.
    # Blur so that only pixels in the dead center of
    # a cell are pitch black, then threshold any pixel that
    # isn't pitch black to white.
    magnified_borders = magnify_cell_borders(connected)

    # But blurring and thresholding on such a dark value makes our contours much smaller
    # than the actual cells of the table. We've rid our table of gaps in the borders; all
    # of or cells are completely enclosed now, but they are enclosed too much.
    # Let's dilate until until we can't dilate any further. Dilate until further dilation
    # would increase the number of contours.
    minified_borders = minify_cell_borders(magnified_borders)

    cells = find_cells(minified_borders)
    rows = sort_cells(cells)

    cell_images_rows = []
    for row in rows:
        cell_images_row = []
        for x, y, w, h in row:
            cell_image = image[y : y + h, x : x + w]
            cell_bordered = cv2.copyMakeBorder(
                cell_image, 2, 2, 2, 2, cv2.BORDER_CONSTANT, None, 255
            )
            cell_images_row.append(cell_bordered)
        cell_images_rows.append(cell_images_row)
    return cell_images_rows

def gaus_blur(image, kern_size=(17, 17), x_std=0, y_std=0):
    """Call through to cv2.GaussianBlur with reasonable defaults."""
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return cv2.GaussianBlur(image, kern_size, x_std, y_std)
def adapt_thresh(
    image,
    max_col=255,
    method=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    type_=cv2.THRESH_BINARY,
    block_size=15,
    sub_from_mean=-1,
):
    """Call to cv2.adaptiveThreshold with reasonable defaults."""
    MAX_COLOR_VAL = 255
    BLOCK_SIZE = 15
    SUBTRACT_FROM_MEAN = -1

    return cv2.adaptiveThreshold(
        image,
        MAX_COLOR_VAL,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        BLOCK_SIZE,
        SUBTRACT_FROM_MEAN,
    )
def mask_to_long_lines(image, scale=3):
    # Dilate to get rid of anything that is not a long line of a table. The
    # higher the scale, the shorter the lines that remain. You might pick up big
    # characters or other noise. The lower the scale, the more you'll restrict
    # yourself to getting only long lines.
    # With a scale of 3, any line that is shorter than 1/3rd the width or height
    # of the image will be removed.
    image_width, image_height = image.shape
    horizontally_opened = cv2.morphologyEx(
        image,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (image_width // scale, 1)),
    )
    vertically_opened = cv2.morphologyEx(
        image,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, image_height // scale)),
    )
    lines_mask = horizontally_opened + vertically_opened
    return lines_mask
def connect_border_joints(image):
    # Dilate to make sure all the joints of each cell connect. If there is a gap, we
    # won't accurately detect 2 cells as actually 2 separate cells.
    SCALE = 40
    image_width, image_height = image.shape
    horizontally_dilated = cv2.morphologyEx(
        image,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (image_width // SCALE, 3)),
    )
    vertically_dilated = cv2.morphologyEx(
        image,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (3, image_height // SCALE)),
    )
    mask = horizontally_dilated + vertically_dilated
    return mask
def magnify_cell_borders(image):
    # Dilation helps, but it's not always enough. Sometimes there are still gaps.
    # Blurring causes the gaps to be a little lighter since they are surrounded by
    # almost connecting borders. The centers of each cell remain pitch black. So
    # let's blur and threshold any value that's not pitch black to full white.
    BLUR_KERNEL_SIZE = (15, 15)
    STD_DEV_X_DIRECTION = 20
    STD_DEV_Y_DIRECTION = 20
    blurred = cv2.GaussianBlur(
        image, BLUR_KERNEL_SIZE, STD_DEV_X_DIRECTION, STD_DEV_Y_DIRECTION
    )

    retval, thresh = cv2.threshold(blurred, 5, 255, cv2.THRESH_BINARY)

    thresh_closed = cv2.morphologyEx(
        thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    )
    return thresh_closed
def minify_cell_borders(image):
    contours, heirarchy = cv2.findContours(
        ~image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE,
    )

    num_contours = num_contours_this_erosion = len(contours)
    MAX_ATTEMPTS = 100
    sentinel = 0
    eroded = cv2.erode(
        image, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    )
    while num_contours == num_contours_this_erosion and sentinel < MAX_ATTEMPTS:
        best_so_far = eroded.copy()
        eroded = cv2.erode(
            eroded, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        )
        contours, heirarchy = cv2.findContours(
            ~eroded, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE,
        )
        num_contours_this_erosion = len(contours)
        sentinel += 1

    return best_so_far
def find_cells(image):
    # BOUNDING_RECTS
    contours, heirarchy = cv2.findContours(
        ~image, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE,
    )

    # TODO: If we did everything above correctly, we probably don't need this
    # approx poly stuff to ensure our shapes are all rectangular.
    perimeter_lengths = [cv2.arcLength(c, True) for c in contours]
    epsilons = [0.01 * p for p in perimeter_lengths]
    approx_polys = [cv2.approxPolyDP(c, e, True) for c, e in zip(contours, epsilons)]

    # Filter out contours that aren't rectangular. Those that aren't rectangular
    # are probably noise.
    approx_rects = [p for p in approx_polys if len(p) == 4]
    bounding_rects = [cv2.boundingRect(a) for a in approx_polys]

    # TODO: This filtering might also not be necessary if the above
    # code is good.
    # Filter out rectangles that are too narrow or too short.
    MIN_RECT_WIDTH = 40
    MIN_RECT_HEIGHT = 10
    bounding_rects = [
        r for r in bounding_rects if MIN_RECT_WIDTH < r[2] and MIN_RECT_HEIGHT < r[3]
    ]

    return bounding_rects
def sort_cells(cells):
    cells = copy(cells)
    rows = []
    while cells:
        first = cells[0]
        rest = cells[1:]
        cells_in_same_row = sorted(
            [
                c for c in rest
                if cell_in_same_row(c, first)
            ],
            key=lambda c: c[0]
        )

        row_cells = sorted([first] + cells_in_same_row, key=lambda c: c[0])
        rows.append(row_cells)
        cells = [
            c for c in rest
            if not cell_in_same_row(c, first)
        ]

    # Sort rows by average height of their center.

    rows.sort(key=avg_height_of_center)
    return rows


def cell_in_same_row(c1, c2):
    c1_center = c1[1] + c1[3] - c1[3] / 2
    c2_bottom = c2[1] + c2[3]
    c2_top = c2[1]
    return c2_top < c1_center < c2_bottom


def avg_height_of_center(row):
    centers = [y + h - h / 2 for x, y, w, h in row]
    return sum(centers) / len(centers)

def main(f):
    results = []
    directory, filename = os.path.split(f)
    table = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    rows = extract_cell_images_from_table(table)
    cell_img_dir = os.path.join(directory, "cells")
    os.makedirs(cell_img_dir, exist_ok=True)
    paths = []
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            cell_filename = "{:03d}-{:03d}.png".format(i, j)
            path = os.path.join(cell_img_dir, cell_filename)
            cv2.imwrite(path, cell)
            paths.append(path)
    return paths
