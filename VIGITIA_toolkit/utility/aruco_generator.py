import cv2.aruco as aruco
import matplotlib.pyplot as plt

ARUCO_DICT = aruco.Dictionary_get(aruco.DICT_4X4_100)
COLUMNS = 3
ROWS = 2
MARKER_WIDTH_PX = 1700
STARTING_ID = 1

fig = plt.figure()
for i in range(STARTING_ID, COLUMNS * ROWS + 1):
    ax = fig.add_subplot(ROWS, COLUMNS, i)
    img = aruco.drawMarker(ARUCO_DICT, i, MARKER_WIDTH_PX)
    plt.imshow(img, cmap='gray', interpolation='nearest')
    ax.axis('off')

fig.set_size_inches(11.69, 8.27)
plt.savefig('aruco_marker.pdf', dpi=300, orientation='portrait')
