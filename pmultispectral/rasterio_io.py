# RASTERIO INPUT/ OUTPUT FUNCTIONS
#if __name__ == "__main__":
    #from unicodedata import name
    #import nacl
    
import rasterio
import numpy as np
import os
import logging


# get a list of files within folder matching search pattern
def listFiles (path, file_extension = "*", search_pattern = "*"):
    #print("\nsearching for '% s':" % (search_pattern + ' ' + file_extension))
    import glob
    #print("\nFiles in directory '% s':" % path)
    file_list = glob.glob(path + '/' + "*" + search_pattern + "*" + file_extension + "*")
    #for files in file_list:
    #    print(files)
    return file_list

# filteres out file names which contain unwanted keywords
def filterFiles(file_list, filter_key_exclude = None, filter_key_include = None):
    # filtering out all key's that are unwanted
    if filter_key_exclude != None:
        if isinstance(filter_key_exclude, str):  # if only string is given convert to list
            filter_key_exclude = [filter_key_exclude]
        file_list = [x for x in file_list if
              all(y not in x for y in filter_key_exclude)]
    
    # filtering out everyhting that doesnt contain key's that are wanted
    if filter_key_include != None:
        if isinstance(filter_key_include, str): # if only string is given convert to list
            filter_key_include = [filter_key_include]
        file_list = [x for x in file_list if
              all(y in x for y in filter_key_include)]
    # emtpy list treated as None
    if file_list == []: 
        return None
    #elif len(file_list) == 1: # FUCKS WITH SOME LOOP EXECUTION 
    #    return file_list[0] # returning as single string not list
    else:
        return(file_list)   


def checkForAlternativeFile(file_path, file_extension, filter_key_include, filter_key_exclude= None ,  remove_str=None, replace_str=""):
    '''Checking a file path for an alternative file name - used to identify cases where orthomosaics have manually been georeferenced. 
    Input is string type output is string type.'''
    folder_path = os.path.dirname(os.path.abspath(file_path)) # dirname
    
    file_name = os.path.basename(os.path.abspath(file_path)) # filename
    file_name = file_name.replace(file_extension, "") # removing file extension
    
    if remove_str is not None:
     file_name = file_name.replace(remove_str, replace_str) # removing or substituting sub string
    
    file_list = listFiles(folder_path, file_extension= file_extension, search_pattern= file_name) # gathering potential files
    file_list = filterFiles(file_list, filter_key_exclude = filter_key_exclude, filter_key_include= filter_key_include)
    #logging.debug('extracted file_list: ' + file_list)

    if file_list is None or (len(file_list) > 1):
        logging.info('could not identify single alternative file, returning original: ' + file_path)
        return file_path
    else:
        file_list = file_list[0] # dirty transformation from list to string 
        logging.info('identified alternative file: ' + file_list)
        return file_list


#file_list = listFiles(folder_path, ".tif")
#file_list_filtered = filterFiles(file_list)
#file_list_filtered = filterFiles(file_list, filter_key_exclude = ['indices', 'aux', 'ovr', 'xml'])
#file_list_filtered = filterFiles(file_list, filter_key_include = ['ETRS'])
#file_list_filtered = filterFiles(file_list, filter_key_exclude = ['indices', 'aux', 'ovr', 'xml'], filter_key_include = ['ETRS'])


def openRasterIntoBands(file_path):
    with rasterio.open(file_path) as src:
        band0, band1, band2, band3, band4, band5, band_mask = src.read()
  

def openRasterBand(file_path):
    with rasterio.open(file_path) as src:   
        myband = src.read()
        