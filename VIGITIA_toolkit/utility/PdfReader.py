import functools
import os
import sys
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
            self.tuio_server.add_symbol_message(s_id, tu_id=0, c_id=0, group='0', data='__Highlight__')
            self.tuio_server.add_token_message(s_id, tu_id=0, c_id=0, x_pos=0.0, y_pos=0.0, angle=0.0)
            self.tuio_server.add_outer_contour_geometry_message(s_id, highlight['quad_points'])
            s_id += 1

        self.tuio_server.send_tuio_bundle()

    def get_annotations(self):
        src = r'/home/vitus/Desktop/Toolkit/VIGITIA-Interaction-Prototype/assets/paper_annot.pdf'

        input1 = PyPDF2.PdfFileReader(open(src, "rb"))
        nPages = input1.getNumPages()

        highlights = []

        for i in range(nPages):
            page0 = input1.getPage(i)
            try:
                for annot in page0['/Annots']:
                    annot_dict = annot.getObject()

                    # print(annot_dict)
                    if annot_dict['/Subtype'] == '/Highlight':
                        highlight = {
                            #'rect': self.sort_points(self.translate_points(annot_dict['/Rect'])),
                            'quad_points': self.sort_points(self.translate_points(annot_dict['/QuadPoints'])),
                            'color': annot_dict['/C'],
                            'annotator': annot_dict['/T']
                        }
                        #print(highlight)
                        highlights.append(highlight)
            except Exception as e:
                print(e)

        return highlights

    def translate_points(self, points_list):

        page_width = 600
        page_height = 800

        for i, point in enumerate(points_list):
            if i & 1 == 0:
                points_list[i] = float(page_width - point)
            else:
                points_list[i] = float(page_height - point)

        return points_list

    def sort_points(self, points_list):

        num_rects = int(len(points_list) / 8)
        print(num_rects)

        sorted_points = []

        for i in range(num_rects):
            rect_points = points_list[i*8:(i+1)*8]

            top_right = rect_points[0:2]
            top_left = rect_points[2:4]
            bottom_right = rect_points[4:6]
            bottom_left = rect_points[6:8]

            sorted_points += top_left + bottom_left + bottom_right + top_right

        if num_rects > 1:
            print(sorted_points)
            sorted_points = self.merge_rectangles(sorted_points, num_rects)

        return sorted_points

    # https://stackoverflow.com/questions/13746284/merging-multiple-adjacent-rectangles-into-one-polygon
    def merge_rectangles(self, old_points, num_rects):

        rect = []

        for i in range(num_rects):
            rect_points = old_points[i * 8:(i + 1) * 8]

            converted = [[rect_points[0], rect_points[1]], [rect_points[4], rect_points[5]]]
            rect.append(converted)

        rect = tuple(rect)
        #print(rect)

        # # These rectangles resemble the OP's illustration.
        # rect = ([[0, 10], [10, 0]],
        #         [[10, 13], [19, 0]],
        #         [[19, 10], [23, 0]])

        points = set()
        for (x1, y1), (x2, y2) in rect:
            for pt in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
                if pt in points:  # Shared vertice, remove it.
                    points.remove(pt)
                else:
                    points.add(pt)
        points = list(points)

        def y_then_x(a, b):
            if a[1] < b[1] or (a[1] == b[1] and a[0] < b[0]):
                return -1
            elif a == b:
                return 0
            else:
                return 1

        sort_x = sorted(points)
        sort_y = sorted(points, key=functools.cmp_to_key(y_then_x))

        edges_h = {}
        edges_v = {}

        i = 0
        while i < len(points):
            curr_y = sort_y[i][1]
            while i < len(points) and sort_y[i][1] == curr_y:
                edges_h[sort_y[i]] = sort_y[i + 1]
                edges_h[sort_y[i + 1]] = sort_y[i]
                i += 2

        i = 0
        while i < len(points):
            curr_x = sort_x[i][0]
            while i < len(points) and sort_x[i][0] == curr_x:
                edges_v[sort_x[i]] = sort_x[i + 1]
                edges_v[sort_x[i + 1]] = sort_x[i]
                i += 2

        # Get all the polygons.
        p = []
        while edges_h:
            # We can start with any point.
            polygon = [(edges_h.popitem()[0], 0)]
            while True:
                curr, e = polygon[-1]
                if e == 0:
                    next_vertex = edges_v.pop(curr)
                    polygon.append((next_vertex, 1))
                else:
                    next_vertex = edges_h.pop(curr)
                    polygon.append((next_vertex, 0))
                if polygon[-1] == polygon[0]:
                    # Closed polygon
                    polygon.pop()
                    break
            # Remove implementation-markers from the polygon.
            poly = [point for point, _ in polygon]
            for vertex in poly:
                if vertex in edges_h: edges_h.pop(vertex)
                if vertex in edges_v: edges_v.pop(vertex)

            p.append(poly)

        new_points = []

        for poly in p:
            #print(poly)
            for pair in poly:
                new_points.append(pair[0])
                new_points.append(pair[1])

        print(new_points)

        return new_points

def main():
    PdfReader()
    sys.exit()


if __name__ == '__main__':
    main()