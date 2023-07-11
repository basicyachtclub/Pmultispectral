# Learning Lunch

# for setting up python environment in visual studio code check out
# https://code.visualstudio.com/docs/python/environments

# SETUP FOR USING SOME BASIC I/O FUNCTIONS for utilizing multipage .tif files


from operator import truediv
import pmultispectral.rasterio_indices as rasterio_indices
import pmultispectral.rasterio_io as rasterio_io
import pmultispectral.zonal_statistics as zonal_statistics
import rasterio
import os
import numpy as np
#import logging
#logging.basicConfig(level=logging.DEBUG)


# get external drive
import psutil
partitions = psutil.disk_partitions()
for p in partitions:
    if p.fstype == "exFAT": # Windows
        external_drive = p.mountpoint
      # logging.info('disk located at : ' + external_drive)
    elif p.fstype == "exfat": # Osx
        external_drive = p.mountpoint + "/"
       # logging.info('disk located at : ' + external_drive)
folder_path = external_drive + "UAV_Steglitz_2019/01__Multispectral/2099-01-01/Flug_01"
#file_list = rasterio_io.listFiles(folder_path, ".tif")




# get all files in folder
file_list = rasterio_io.listFiles(folder_path, recursive = True)
print(file_list[1:200])

# filter files
file_list_filtered = rasterio_io.filterFiles(file_list,
                                             #filter_key_exclude=['georef','aux', 'ovr', 'xml', 'points'],
                                             #filter_key_include=['_16'])  
                                             filter_key_include=['.TIF', 'TTC043'])       
print(file_list_filtered[1:200])





# open raster into bands
def openRasterIntoBands(file_path):
    with rasterio.open(file_path) as src:  # currently only works for the 6 band combination of tetracam
            band0, band1, band2, band3, band4, band5 = src.read() # band_mask
            gi, gndvi, msr, ndvi, pri = rasterio_indices.calcIndxAll(band0, band1, band2, band3, band4, band5)
    return band0, band1, band2, band3, band4, band5, gi, gndvi, msr, ndvi, pri


# file multipage.tif is located in the folder
img_path_one = external_drive + 'UAV_Steglitz_2019/01__Multispectral/2099-01-01/Flug_01/03__Layerstack_16bit/TTC04328_16.TIF'
img_path_two = external_drive + 'UAV_Steglitz_2019/01__Multispectral/2099-01-01/Flug_01/03__Layerstack_16bit/TTC04329_16.TIF'


# load image into rasterio file type object
img1 = rasterio.open(img_path_one)


# load individual bands of image into array's
img1_band0, img1_band1, img1_band2, img1_band3, img1_band4, img1_band5, \
    img1_gi, img1_gndvi, img1_msr, img1_ndvi, img1_pri = openRasterIntoBands(img_path_one)

img2_band0, img2_band1, img2_band2, img2_band3, img2_band4, img2_band5, \
img2_gi, img2_gndvi, img2_msr, img2_ndvi, img2_pri = openRasterIntoBands(img_path_two)

rasterio_indices.pltIndx(img1_ndvi)
rasterio_indices.pltIndx(img2_ndvi)



# 
for file in file_list_filtered:
    # if 'TTC04315' in file # set this as breakpoint
    band0, band1, band2, band3, band4, band5, gi, gndvi, msr, ndvi, pri = openRasterIntoBands(file)
    
    print("file: " + file)
    print('dtype:    {}'.format(ndvi.dtype))
    print('shape:    {}'.format(ndvi.shape))
    print('min:  {}'.format(ndvi.min() / 65535))
    print('mean:  {}'.format(ndvi.mean() / 65535))
    print('max:  {}'.format(ndvi.max() / 65535))
    print('\n')







print("END OF FILE")


# lets filter our file list for .tif files

def filterFileListForTif(file_list):
    file_list_filtered = []
    for file in file_list:
        if '.tif' in file:
            file_list_filtered.append(file)
    return file_list_filtered


