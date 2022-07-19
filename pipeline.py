# executing pipeline for orthomosaic preprocessing
import src.rasterio_indices as rasterio_indices
import src.rasterio_io as rasterio_io


# platform depending alterations
from sys import platform
if platform == "linux" or platform == "linux2": # linux
    raise Exception("Linux not implemented")
elif platform == "darwin": # OS X
    external_drive = "/Volumes/T7/"
elif platform == "win32": # Windows...
    external_drive = "F:/"

# directory info
folder_path = external_drive + "UAV_Steglitz_2019/01__Multispectral/orthomosaics/"
file_path = folder_path + "2019_07_17_Flug04.tif"
out_path = folder_path + "2019_07_17_Flug04_indices.tif"


#file_path = "F:/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04.tif" #WINDOWS
#file_path = "/Volumes/T7/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04.tif" #MAC

#out_path = "F:/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04_indices.tif" #WINDOWS
#out_path = "/Volumes/T7/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04_altered.tif" #MAC


# deriving a file list for analysis
file_list = rasterio_io.listFiles(folder_path, ".tif") # get .tif files in directory
file_list_filtered = rasterio_io.filterFiles(file_list, filter_key_exclude = ['indices', 'aux', 'ovr', 'xml'], filter_key_include = ['ETRS']) # filter out unwanted ones

# run indice calculation for all files
for file in file_list_filtered:
    rasterio_indices.writeIndicesToDisk(file)
    #rasterio_indices.appendBandnames(file) # appends dictionary of bandnames to profile











# TESTING AREA
print("beginning testing!")

# reading orthomosaic values into individual band numpy arrays  

# checking the profile for band names 
import rasterio
with rasterio.open(file) as src:
    test = src.profile

# deep check
with rasterio.open(file_path[:-4] + "_indices.tif") as src:
    test = src.read()

# double check
with rasterio.open(file_path[:-4] + "_indices.tif") as src:
    print(src.profile)
    test = src.read(12) # read the one array entry
pltIndx(test)


with rasterio.open(file_path) as src:
    test = src.read()