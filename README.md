# VIGITIA Toolkit zum Erstellen von Projected-Augmented-Reality-Anwendungen auf Tischen

Dieses Toolkit entstand im Rahmen der Masterarbeit von Vitus Maierhöfer im Forschungsprojekt VIGITIA 
(https://vigitia.de/) am Lehrstuhl für Medieninformatik der Universität Regensburg


# Installationsanleitung (Linux):

#### Abhängigkeiten:

```
sudo apt-get install python3-pip python3-numpy
```

```
sudo apt-get install gstreamer1.0*
sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev

sudo apt-get install build-essential
sudo apt-get install cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install python-dev python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libdc1394-22-dev
```

####Installation von OpenCV in der korrekten Version mit GStreamer Support und dem opencv_contrib-Modul
```
git clone https://github.com/opencv/opencv.git
git clone https://github.com/opencv/opencv_contrib.git
cd opencv/
git checkout 4.4.0

cmake -D CMAKE_BUILD_TYPE=RELEASE \
-D CMAKE_INSTALL_PREFIX=/usr/local \
-D INSTALL_PYTHON_EXAMPLES=ON \
-D INSTALL_C_EXAMPLES=OFF \
-D PYTHON_EXECUTABLE=$(which python3) \
-D BUILD_opencv_python2=OFF \
-D CMAKE_INSTALL_PREFIX=$(python3 -c "import sys; print(sys.prefix)") \
-D PYTHON3_EXECUTABLE=$(which python3) \
-D PYTHON3_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
-D PYTHON3_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
-D WITH_GSTREAMER=ON \
-D OPENCV_EXTRA_MODULES_PATH=/home/vigitia/opencv_contrib/modules /home/vigitia/opencv/ \
-D BUILD_EXAMPLES=ON ..

sudo make -j16
sudo make install
sudo ldconfig```

```
#### Weitere Python-Bibliotheken
```
pip3 install PyQt5==5.10
pip3 install pyrealsense2
pip3 install python-osc
pip3 install cvlib
pip3 install scipy
pip3 install tensorflow
pip3 install scikit-learn
```


# Arbeiten mit dem Toolkit

#### 1: Hardwaresetup
...

#### 2: Kalibrieren des Systems
...

#### 3: Konfigurieren und Starten des SensorProcessingControllers
...

#### 4: Konfigurieren und Starten des RenderingManagers
...