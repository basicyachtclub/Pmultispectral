# RASTERIO INPUT/ OUTPUT FUNCTIONS
#if __name__ == "__main__":
    #from unicodedata import name
    #import nacl
    
import re
import rasterio
import numpy as np
import os
import logging
import shutil

# get a list of files within folder matching search pattern
def listFiles (path, file_extension = "*", search_pattern = "*", recursive = False):
    #print("\nsearching for '% s':" % (search_pattern + ' ' + file_extension))
    import glob
    #print("\nFiles in directory '% s':" % path)
    if recursive == False:
        file_list = glob.glob(path + '/' + "*" + search_pattern + "*" + file_extension + "*")
    if recursive == True:
        file_list = glob.glob(path + '/**/' + "*" + search_pattern + "*" + file_extension + "*", recursive=recursive)
    #for files in file_list:
    #    print(files)
    return file_list

# filteres out file names which contain unwanted keywords
def filterFiles(file_list, filter_key_exclude = None, filter_key_include = None):
    # filtering out all key's that are unwanted
    if filter_key_exclude != None:
        if isinstance(filter_key_exclude, str):  # if only string is given convert to list
            filter_key_exclude = [filter_key_exclude]
        # For every file_path in the list it is checked if the file name (not path name) contains filter keys
        file_list = [x for x in file_list if
                     all(y not in os.path.basename(os.path.abspath(x)) for y in filter_key_exclude)]

    # filtering out everyhting that doesnt contain key's that are wanted
    if filter_key_include != None:
        if isinstance(filter_key_include, str): # if only string is given convert to list
            filter_key_include = [filter_key_include]
        file_list = [x for x in file_list if
                     all(y in os.path.basename(os.path.abspath(x)) for y in filter_key_include)]
    # emtpy list treated as None
    if file_list == []: 
        return None
    #elif len(file_list) == 1: # FUCKS WITH SOME LOOP EXECUTION 
    #    return file_list[0] # returning as single string not list
    else:
        return(file_list)   

def matchUpFileLists(list1, list2, filter_key_exclude = '', fuzz_thresh = 100):
    '''tries to find a matching file from file list b for each file in file_list a.
    Only looks for matches of list2 to list1.'''
    from fuzzywuzzy import fuzz
    new_list1, new_list2, matching, no_matching = [], [], [], []
    m_score = 0
    for item1 in list1:    
        for item2 in list2:      
            
            # getting only the filename
            item1_name = os.path.basename(os.path.abspath(item1)) 
            item2_name = os.path.basename(os.path.abspath(item2)) 

            for key in filter_key_exclude: # removing unwanted text from string
                item1_name = item1_name.replace(key, '')
                item2_name = item2_name.replace(key, '')

            m_score = fuzz.ratio(item1_name, item2_name)
            if m_score >= fuzz_thresh: # use 100 if only completely identicall items should be matched
                #matching.append(item1)
                new_list1.append(item1)
                new_list2.append(item2)

        if m_score < 60 and not(item1 in matching):
            no_matching.append(item1)
            logging.warning('could not match an item with filelist')
            logging.debug('could not match: ' + item1 + ' \n with: ' + item2)
    
    return(new_list1, new_list2)

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


# def moveFileToFolder (file_path, folder_path):
#     file_name = os.path.basename(os.path.abspath(file_path)) # filename
#     out_file_path = os.path.join(folder_path, file_name)

#     logging.debug(' transfering ' + file_name + ' to ' + folder_path)
#     try:
#        shutil.copy(file_path, out_file_path)
#     except FileNotFoundError as e:
#         logging.debug(e)
#         raise

# moveFileToFolder (file_path = 'F:\\UAV_Steglitz_2019\\04__Processed\\orthomosaics\\2019_04_17_Flug01_ETRS1989_modified_indices.tif', 
#                  folder_path = 'F:\\UAV_Steglitz_2019\\04__Processed\\TT')



def moveFileToFolder (file_path, folder_path, overwrite = False, existing_dir_only = True, remove_input_file = True):
    '''Moves provided file to new folder.'''
    # check if input file exists
    if os.path.exists(file_path) == False:   
        logging.debug(' File Not Found: ' + file_path)     
        raise FileNotFoundError
        # raise Exception(' File Not Found: ' + file_path)
    file_name = os.path.basename(os.path.abspath(file_path)) # filename

    # check if output directory exists
    if os.path.exists(folder_path) == False:
        logging.warning(' no directory at ' + folder_path)
        if existing_dir_only:
            logging.warning(' could not copy file ' + file_name)
            return
        logging.debug(' creating dir ' + folder_path)
        os.makedirs(folder_path, exist_ok=False) 
        # raises an exception in case there should be a directory
        # creates folder into depth recursively   
    out_file_path = os.path.join(folder_path, file_name) # full file output path
    
    # checking if file exists at location
    if os.path.exists(out_file_path):
        logging.debug(' file already exists at: ' + out_file_path) 
        if overwrite == False:
            logging.info(' file duplicate found for ' + file_name + ' at ' + folder_path + ' not overwriting')
            return
        else :
            logging.warning(' file duplicate found for ' + file_name + ' at ' + folder_path + ' overwriting!')

    logging.debug(' transfering ' + file_name + ' to ' + folder_path)
    shutil.copy2(file_path, out_file_path)
    
    if remove_input_file:
        logging.debug(' removing file at ' + file_path)
        os.remove(file_path)


# import logging    
# logging.basicConfig(level=logging.DEBUG)
# moveFileToFolder (file_path = 'F:\\UAV_Steglitz_2019\\04__Processed\\orthomosaics\\2019_04_17_Flug01_ETRS1989_modified_indices.tif', 
#                  folder_path = 'F:\\UAV_Steglitz_2019\\04__Processed\\T' , 
#                  overwrite = True)

# moveFileToFolder (file_path = 'F:\\UAV_Steglitz_2019\\04__Processed\\orthomosaics\\2019_04_17_Flug01_ETRS1989_modified_indices.tif', 
#                  folder_path = 'F:\\UAV_Steglitz_2019\\04__Processed\\test' , 
#                  overwrite = False,
#                  existing_dir_only= True)

print('END')

def openRasterIntoBands(file_path):
    with rasterio.open(file_path) as src:
        band0, band1, band2, band3, band4, band5, band_mask = src.read()
  

def openRasterBand(file_path):
    with rasterio.open(file_path) as src:   
        myband = src.read()
        
