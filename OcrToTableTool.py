import cv2
import numpy as np
import subprocess

import keras_ocr # new

class OcrToTableTool:

    def __init__(self, image, original_image, image_with_lines_only, image_without_lines_white):
        self.thresholded_image = image
        self.original_image = original_image
        self.image_with_lines_only = image_with_lines_only # new
        self.image_without_lines_white = image_without_lines_white # new
        #self.recognizer = keras_ocr.recognition.Recognizer() # new
        self.pipeline = keras_ocr.pipeline.Pipeline() # new

    def execute(self):
        self.dilate_image()
        self.store_process_image('0_dilated_image.jpg', self.dilated_image)
        self.find_contours()
        self.store_process_image('1_contours.jpg', self.image_with_contours_drawn)
        self.convert_contours_to_bounding_boxes()
        self.store_process_image('2_bounding_boxes.jpg', self.image_with_all_bounding_boxes)
        self.mean_height = self.get_mean_height_of_bounding_boxes()
        self.sort_bounding_boxes_by_y_coordinate()
        self.club_all_bounding_boxes_by_similar_y_coordinates_into_rows()
        self.sort_all_rows_by_x_coordinate_new() # new
        self.crop_each_bounding_box_and_ocr_new() # new
        self.generate_csv_file()

    def threshold_image(self):
        return cv2.threshold(self.grey_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    def convert_image_to_grayscale(self):
        return cv2.cvtColor(self.image, self.dilated_image)

    def dilate_image(self):
        kernel_to_remove_gaps_between_words = np.array([
                [1,1,1,1,1,1,1,1,1,1],
               [1,1,1,1,1,1,1,1,1,1]
        ])
        self.dilated_image = cv2.dilate(self.thresholded_image, kernel_to_remove_gaps_between_words, iterations=5)
        simple_kernel = np.ones((5,5), np.uint8)
        self.dilated_image = cv2.dilate(self.dilated_image, simple_kernel, iterations=2)
        # remove lines in order to repair situations where two colums dilate into each other # new
        self.dilated_image = cv2.subtract(self.dilated_image, self.image_with_lines_only) # new
        # remove_noise_with_erode_and_dilate # new
        #kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)) # new
        self.dilated_image = cv2.erode(self.dilated_image, simple_kernel, iterations=7) # new
        self.dilated_image = cv2.dilate(self.dilated_image, simple_kernel, iterations=7) # new
    
    def find_contours(self):
        result = cv2.findContours(self.dilated_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        self.contours = result[0]
        self.image_with_contours_drawn = self.original_image.copy()
        cv2.drawContours(self.image_with_contours_drawn, self.contours, -1, (0, 255, 0), 3)
    
    def approximate_contours(self):
        self.approximated_contours = []
        for contour in self.contours:
            approx = cv2.approxPolyDP(contour, 3, True)
            self.approximated_contours.append(approx)

    def draw_contours(self):
        self.image_with_contours = self.original_image.copy()
        cv2.drawContours(self.image_with_contours, self.approximated_contours, -1, (0, 255, 0), 5)

    def convert_contours_to_bounding_boxes(self):
        self.bounding_boxes = []
        self.image_with_all_bounding_boxes = self.original_image.copy()
        for contour in self.contours:
            x, y, w, h = cv2.boundingRect(contour)
            self.bounding_boxes.append((x, y, w, h))
            self.image_with_all_bounding_boxes = cv2.rectangle(self.image_with_all_bounding_boxes, (x, y), (x + w, y + h), (0, 255, 0), 5)

    def get_mean_height_of_bounding_boxes(self):
        heights = []
        for bounding_box in self.bounding_boxes:
            x, y, w, h = bounding_box
            heights.append(h)
        return np.mean(heights)

    def sort_bounding_boxes_by_y_coordinate(self):
        self.bounding_boxes = sorted(self.bounding_boxes, key=lambda x: x[1])

    def club_all_bounding_boxes_by_similar_y_coordinates_into_rows(self):
        self.rows = []
        half_of_mean_height = self.mean_height / 2
        current_row = [ self.bounding_boxes[0] ]
        for bounding_box in self.bounding_boxes[1:]:
            current_bounding_box_y = bounding_box[1]
            previous_bounding_box_y = current_row[-1][1]
            distance_between_bounding_boxes = abs(current_bounding_box_y - previous_bounding_box_y)
            if distance_between_bounding_boxes <= half_of_mean_height:
                current_row.append(bounding_box)
            else:
                self.rows.append(current_row)
                current_row = [ bounding_box ]
        self.rows.append(current_row)

    def sort_all_rows_by_x_coordinate(self):
        for row in self.rows:
            row.sort(key=lambda x: x[0])

    def sort_all_rows_by_x_coordinate_new(self): # new
        # find the number of occupated columns of the lowest row with maximum occupated columns -> number of columns
        number_of_columns = 0
        for row_index in range(len(self.rows)):
            if len(self.rows[row_index]) >= number_of_columns:
                number_of_columns = len(self.rows[row_index])
                index_of_max_row = row_index
        # create a list of starts of rows
        row_starts = []
        for bounding_box in self.rows[index_of_max_row]:
            row_starts.append(bounding_box[0])
        row_starts.sort()
        # create new rows including empty columns
        new_rows = []
        for row in self.rows:
            if len(row) == number_of_columns:
                new_row = row
                new_row.sort(key=lambda x: x[0])
            else:
                new_row = [(-1, -1, -1, -1) for _ in range(number_of_columns)]
                for bounding_box in row:
                    x, y, w, h = bounding_box
                    end_of_b_box = x + w
                    for i in range(number_of_columns - 1, -1, -1):
                        if row_starts[i] < end_of_b_box:
                            new_row[i] = bounding_box
                            break
            new_rows.append(new_row)
        self.rows = new_rows

    def crop_each_bounding_box_and_ocr(self):
        self.table = []
        current_row = []
        image_number = 0
        for row in self.rows:
            for bounding_box in row:
                x, y, w, h = bounding_box
                y = y - 5
                cropped_image = self.original_image[y:y+h, x:x+w] # new: self.image_without_lines_white[y:y+h, x:x+w]
                image_slice_path = "./ocr_slices/img_" + str(image_number) + ".jpg"
                cv2.imwrite(image_slice_path, cropped_image)
                results_from_ocr = self.get_result_from_tersseract(image_slice_path)
                current_row.append(results_from_ocr)
                image_number += 1
            self.table.append(current_row)
            current_row = []

    def crop_each_bounding_box_and_ocr_new(self): # new
        self.table = []
        current_row = []
        image_number = 0
        for row in self.rows:
            for bounding_box in row:
                x, y, w, h = bounding_box
                if x == -1:
                    current_row.append('')
                else:
                    y = y - 5
                    cropped_image = self.original_image[y:y+h, x:x+w] # new: self.image_without_lines_white[y:y+h, x:x+w]
                    image_slice_path = "./ocr_slices/img_" + str(image_number) + ".jpg"
                    cv2.imwrite(image_slice_path, cropped_image)
                    results_from_ocr = self.get_result_from_tersseract(image_slice_path)
                    current_row.append(results_from_ocr)
                    image_number += 1
            self.table.append(current_row)
            current_row = []

    def get_result_from_tersseract(self, image_path):
        # original code using resseract cli interface
        #output = subprocess.getoutput('tesseract ' + image_path + ' - -l eng --oem 3 --psm 7 --dpi 72 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789().calmg* "')

        # method using Recognizer from keras ocr - seems to be only for images with one word
        #output = self.recognizer.recognize(image = image_path) # new
        
        # method with keras ocr pipeline
        image = keras_ocr.tools.read(image_path)
        prediction = self.pipeline.recognize([image])[0]
        # this will sort the words from the picture from left to right
        sorted_prediction = sorted(prediction, key=lambda x: x[1][0][0])
        output = ''
        for word, location in sorted_prediction:
            output = output + word.strip() + ' '

        output = output.strip()
        return output

    def generate_csv_file(self):
        with open("output.csv", "w") as f:
            for row in self.table:
                f.write(",".join(row) + "\n")

    def store_process_image(self, file_name, image):
        path = "./process_images/ocr_table_tool/" + file_name
        cv2.imwrite(path, image)