import functools
import os
import sys
import pprint

import PyPDF2
from VIGITIA_toolkit.utility.get_ip import get_ip_address
from VIGITIA_toolkit.data_transportation.TUIOServer import TUIOServer  # Import TUIO Server

TARGET_COMPUTER_IP = '10.61.3.117'
print(TARGET_COMPUTER_IP)

TARGET_COMPUTER_PORT = 3333


class PdfReader:

    def __init__(self):
        self.init_tuio_server()
        self.process_and_send()

    def init_tuio_server(self):
        self.tuio_server = TUIOServer(TARGET_COMPUTER_IP, TARGET_COMPUTER_PORT)
        self.dimension = self.tuio_server.get_dimension(1920, 1080)
        self.source = os.uname()[1]  # TODO: Not working on windows

    def process_and_send(self):
        self.tuio_server.start_tuio_bundle(dimension=self.dimension, source=self.source)

        highlights = self.get_annotations()

        s_id = 0

        for highlight in highlights:

            current_ids = []

            for rectangle in highlight['quad_points']:
                print(rectangle)
                self.tuio_server.add_symbol_message(s_id, tu_id=0, c_id=0, group='0', data='__Highlight__')
                self.tuio_server.add_token_message(s_id, tu_id=0, c_id=0, x_pos=0.0, y_pos=0.0, angle=0.0)
                self.tuio_server.add_outer_contour_geometry_message(s_id, rectangle)
                current_ids.append(s_id)
                s_id += 1
            # If the current highlight consists of more than one rectangle: Send TUIO link association message
            if len(current_ids) > 1:
                # Tell the receiver what IDs are linked
                self.tuio_server.add_lia_message(current_ids.pop(0), True, current_ids)

        self.tuio_server.send_tuio_bundle()

    def get_annotations(self):
        src = r'/home/vitus/Desktop/Toolkit/VIGITIA-Interaction-Prototype/assets/paper_annot.pdf'

        input_pdf = PyPDF2.PdfFileReader(open(src, "rb"))
        page_width = input_pdf.getPage(0).mediaBox[2]
        page_height = input_pdf.getPage(0).mediaBox[3]

        print(page_width, page_height)


        num_pages = input_pdf.getNumPages()

        highlights = []

        for i in range(num_pages):
            current_page = input_pdf.getPage(i)
            try:
                for annotations in current_page['/Annots']:
                    annot_dict = annotations.getObject()
                    # print(annot_dict)

                    # Select all elements of type "Hightlight"
                    if annot_dict['/Subtype'] == '/Highlight':
                        print(annot_dict)
                        highlight = {
                            #'rect': self.sort_points(self.translate_points(annot_dict['/Rect'])),
                            'quad_points': self.sort_points(self.translate_points(annot_dict['/QuadPoints'], page_width, page_height)),
                            'color': annot_dict['/C'],
                            'annotator': annot_dict['/T']
                        }
                        #print(highlight)
                        highlights.append(highlight)
            except Exception as e:
                print(e)

        return highlights

    def translate_points(self, points_list, page_width, page_height):

        # Currently flipping points along horizontal axis
        for i, point in enumerate(points_list):
            if i & 1 != 0:
                points_list[i] = float(page_height - point)

        return points_list

    def sort_points(self, points_list):

        num_rects = int(len(points_list) / 8)
        # print(num_rects)

        sorted_points = []

        for i in range(num_rects):
            rect_points = points_list[i*8:(i+1)*8]

            top_right = rect_points[0:2]
            top_left = rect_points[2:4]
            bottom_right = rect_points[4:6]
            bottom_left = rect_points[6:8]

            # sorted_points += top_left + bottom_left + bottom_right + top_right
            sorted_points.append([top_left[0], top_left[1], bottom_left[0], bottom_left[1], bottom_right[0], bottom_right[1], top_right[0], top_right[1]])

        return sorted_points


def main():
    PdfReader()
    sys.exit()


if __name__ == '__main__':
    main()
