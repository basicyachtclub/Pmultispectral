
#if __name__ == "__main__":
import rasterio
import numpy as np


# Calculating  band indices
def calcIndx(a,b, lambda_func): 
    '''Calculate NDVI from integer arrays'''
    a = a.astype('f4') # Array-protocol type strings convention for data type
    b = b.astype('f4') # f4 ~ 2^4 (16bit) floating-point
    indx = lambda_func(a,b)
    indx = (indx * 65535).astype('uint16')
    # get info about datatype np.iinfo(np.uint16)
    return indx


def calcIndxAll(band0, band1, band2, band3, band4, band5):
    # Calculating all propsed indices
    # import numpy as np
    gi =    calcIndx(band1 ,band2, lambda a, b :  a / b ) # Greenness Index (also Green Difference Vegetation Index (GDVI))
    gndvi = calcIndx(band5 ,band1, lambda a, b : (a - b) / (a + b) ) # Green Normalized Difference Vegetation Index
    msr =   calcIndx(band5 ,band3, lambda a, b : ((a/b)-1) / np.sqrt((a/b)+1) )  # modified simple ration 670, 800
    ndvi =  calcIndx(band5 ,band3, lambda a, b : (a - b) / (a + b) ) 
    pri =   calcIndx(band0 ,band2, lambda a, b : (a - b) / (a + b) ) # photochemical reflectance index

    return (gi, gndvi, msr, ndvi, pri)

    # gi - index was originally designed with color-infrared photography to predict nitrogren requirements for corn
    # gndvi - is a chlorophyll index and is used at later stages of development, as it saturates later than NDVI.
    # msr - aims to linearize the  relationships between the index and biophysical parameters.
    # ndvi - green (active) biomass estimation
    # pri - indicator of photosynthetic efficiency as radation use efficency varies significantly between plants, environmental conditions 

    #dict_gi = {     "expr"  : lambda a, b :  a / b ,
    #                "a"     : band1,
    #                "b"     : band2 }


# quick indice plot and infos - data must be provided as 2D numpy array
def pltIndx(indx):
    from matplotlib import pyplot as plt
    print('dtype:    {}'.format(indx.dtype))
    print('shape:    {}'.format(indx.shape))
    print('min val:  {}'.format(indx.min()))
    print('max val:  {}'.format(indx.max()))
    #print(f"\n{indx = }")

    plt.imshow(indx, cmap='RdYlGn')
    plt.colorbar()
    plt.xlabel('Column #')
    plt.ylabel('Row #')
    plt.show()

# save indices to disk
def appendBandtoRaster(file_path, new_band):
    with rasterio.open(file_path) as src:
        profile = src.profile.copy()
        
        # position for band insertion (after last band)
        band_position = profile["count"] + 1

        profile.update({
            #'dtype':  new_band.dtype ,#"uint16", #rasterio.uint16, # 'float32',
            #'height':  new_band.shape[0],
            #'width':  new_band.shape[1],
            'count': band_position })  # only works if band is appended at last position 
        
        data = src.read()

        # some weird data wrangling creating a new array with all values    
        new_data = np.moveaxis(data, [0, 1, 2], [2, 0, 1]) # rashaping so dstack works
        new_data = np.dstack((new_data, new_band))
        new_data = np.moveaxis(new_data, [2, 0, 1], [0, 1, 2]) # retransformation
        src.close()    
    
    with rasterio.open(file_path, 'w', **profile) as dst:
        #dst.write_band(band_position, new_band)
        #dst.write(new_band, 6)
        dst.write(new_data)
        dst.close()
    

# create all indices and write out to file 
def writeIndicesToDisk(file_path, update_existing_file = False):
    
    # write the output into a new file
    if update_existing_file == False:
        out_path = file_path[:-4] + "_indices.tif"
    else:
        out_path = file_path
    

    import shutil
    shutil.copy2(file_path, out_path) # creates a copy of the orthomosaic so any alteration does not mess up original file

    with rasterio.open(file_path) as src: # currently only works for the 6 band combination of tetracam
        band0, band1, band2, band3, band4, band5, band_mask = src.read()

    gi, gndvi, msr, ndvi, pri = calcIndxAll(band0, band1, band2, band3, band4, band5)

    appendBandtoRaster(out_path, gi)
    appendBandtoRaster(out_path, gndvi)
    appendBandtoRaster(out_path, msr)
    appendBandtoRaster(out_path, ndvi)
    appendBandtoRaster(out_path, pri) 

    return None



