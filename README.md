Skychecker
=========

Just a python script using Skyreader dump output 

Note to myself don't forget udev rules:
SUBSYSTEM=="usb", ATTRS{idVendor}=="1430", ATTRS{idProduct}=="0150",GROUP="plugdev", MODE="0666"
KERNEL=="hidraw*", ATTRS{idVendor}=="1430", ATTRS{idProduct}=="0150",GROUP="plugdev", MODE="0666" 
