# RASTERIO INPUT/ OUTPUT FUNCTIONS
#if __name__ == "__main__":
    #from unicodedata import name
    #import nacl
    
import rasterio
import numpy as np


# get a list of files within folder matching search pattern
def listFiles (path, search_pattern = "*"):
    import glob
    print("\nFiles in directory '% s':" % path)
    file_list = glob.glob(path + '/' + "*" + search_pattern + "*")
    for files in file_list:
        print(files)
    return file_list

# filteres out file names which contain unwanted keywords
def filterFiles(file_list, filter_key_exclude = None, filter_key_include = None):
    # filtering out all key's that are unwanted
    if filter_key_exclude != None:
        file_list = [x for x in file_list if
              all(y not in x for y in filter_key_exclude)]
    # filtering out everyhting that doesnt contain key's that are wanted
    if filter_key_include != None:
        file_list = [x for x in file_list if
              all(y in x for y in filter_key_include)]
    return(file_list)   

#file_list = listFiles(folder_path, ".tif")
#file_list_filtered = filterFiles(file_list)
#file_list_filtered = filterFiles(file_list, filter_key_exclude = ['indices', 'aux', 'ovr', 'xml'])
#file_list_filtered = filterFiles(file_list, filter_key_include = ['ETRS'])
#file_list_filtered = filterFiles(file_list, filter_key_exclude = ['indices', 'aux', 'ovr', 'xml'], filter_key_include = ['ETRS'])


def openRasterIntoBands(file_path):
    with rasterio.open(file_path) as src:
        band0, band1, band2, band3, band4, band5, band_mask = src.read()
  