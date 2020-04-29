import cv2
import os

def extract_cell_images_from_table(image):
    MAX_COLOR_VAL = 255
    BLOCK_SIZE = 15
    SUBTRACT_FROM_MEAN = -1
    img_bin = cv2.adaptiveThreshold(
        ~image,
        MAX_COLOR_VAL,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        BLOCK_SIZE,
        SUBTRACT_FROM_MEAN,
    )
    bordered = cv2.copyMakeBorder(
        img_bin, 50, 50, 50, 50, cv2.BORDER_CONSTANT, None, 255
    )
    vertical = horizontal = bordered.copy()

    # Dilate to get rid of anything that is not a long line of a table. The
    # higher the scale, the shorter the lines that remain. You might pick up big
    # characters or other noise. The lower the scale, the more you'll restrict
    # yourself to getting only long lines.
    # With a scale of 3, any line that is shorter than 1/3rd the width or height
    # of the image will be removed.
    SCALE = 3
    image_width, image_height = horizontal.shape
    horizontally_opened = cv2.morphologyEx(
        bordered,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (image_width // SCALE, 1)),
    )
    vertically_opened = cv2.morphologyEx(
        bordered,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, image_height // SCALE)),
    )

    # Dilate to make sure all the joints of each cell connect. If there is a gap, we
    # won't accurately detect them as 2 separate cells.
    SCALE = 40
    horizontally_dilated = cv2.morphologyEx(
        horizontally_opened,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (image_width // SCALE, 3)),
    )
    vertically_dilated = cv2.morphologyEx(
        vertically_opened,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (3, image_height // SCALE)),
    )
    mask = horizontally_dilated + vertically_dilated
    # Dilation helps, but it's not always enough. Sometimes there are still gaps.
    # Blurring causes the gaps to be a little lighter since they are surrounded by
    # "almost" connecting borders. The centers of each cell remain pitch black. So
    # let's blur and threshold any value greater than ~25% white to full white.
    BLUR_KERNEL_SIZE = (15, 15)
    STD_DEV_X_DIRECTION = 20
    STD_DEV_Y_DIRECTION = 20
    blurred_mask = cv2.GaussianBlur(
        mask, BLUR_KERNEL_SIZE, STD_DEV_X_DIRECTION, STD_DEV_Y_DIRECTION
    )

    retval, thresh = cv2.threshold(blurred_mask, 5, 255, cv2.THRESH_BINARY)

    thresh_closed = cv2.morphologyEx(
        thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    )

    # But blurring and thresholding on such a dark value makes our contours much smaller
    # than the actual cells of the table. We've rid our table of gaps in the borders; all
    # of or cells are completely enclosed now, but they are enclosed too much.
    # Let's dilate until until we can't dilate any further. Dilate until further dilation
    # would increase the number of contours.
    contours, heirarchy = cv2.findContours(
        ~thresh_closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE,
    )

    num_contours = num_contours_this_erosion = len(contours)
    MAX_ATTEMPTS = 100
    sentinel = 0
    eroded_thresh = cv2.erode(
        thresh_closed, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    )
    while num_contours == num_contours_this_erosion and sentinel < MAX_ATTEMPTS:
        best_so_far = eroded_thresh.copy()
        eroded_thresh = cv2.erode(
            eroded_thresh, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        )
        contours, heirarchy = cv2.findContours(
            ~eroded_thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE,
        )
        num_contours_this_erosion = len(contours)
        sentinel += 1

    y, x = best_so_far.shape
    contoured_table = best_so_far[50 : y - 50, 50 : x - 50]

    # BOUNDING_RECTS
    contours, heirarchy = cv2.findContours(
        ~contoured_table, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE,
    )

    perimeter_lengths = [cv2.arcLength(c, True) for c in contours]
    epsilons = [0.01 * p for p in perimeter_lengths]
    approx_polys = [cv2.approxPolyDP(c, e, True) for c, e in zip(contours, epsilons)]

    # Filter out contours that aren't rectangular. Those that aren't rectangular
    # are probably noise.
    approx_rects = [p for p in approx_polys if len(p) == 4]
    bounding_rects = [cv2.boundingRect(a) for a in approx_polys]

    # Filter out rectangles that are too narrow or too short.
    MIN_RECT_WIDTH = 40
    MIN_RECT_HEIGHT = 10
    bounding_rects = [
        r for r in bounding_rects if MIN_RECT_WIDTH < r[2] and MIN_RECT_HEIGHT < r[3]
    ]

    cells = [c for c in bounding_rects]

    # SORT
    def cell_in_same_row(c1, c2):
        c1_center = c1[1] + c1[3] - c1[3] / 2
        c2_bottom = c2[1] + c2[3]
        c2_top = c2[1]
        return c2_top < c1_center < c2_bottom

    orig_cells = [c for c in cells]
    rows = []
    while cells:
        first = cells[0]
        rest = cells[1:]
        cells_in_same_row = sorted(
            [c for c in rest if cell_in_same_row(c, first)], key=lambda c: c[0]
        )

        row_cells = sorted([first] + cells_in_same_row, key=lambda c: c[0])
        rows.append(row_cells)
        cells = [c for c in rest if not cell_in_same_row(c, first)]

    # Sort rows by average height of their center.
    def avg_height_of_center(row):
        centers = [y + h - h / 2 for x, y, w, h in row]
        return sum(centers) / len(centers)

    rows.sort(key=avg_height_of_center)

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
