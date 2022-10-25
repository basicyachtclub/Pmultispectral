
#if __name__ == "__main__":
import rasterio
import numpy as np


# Calculating  band indices
def calcIndx(a,b, lower_bound, upper_bound, lambda_func): 
    '''Calculate NDVI from integer arrays'''
    # does data need to be typecast as float? are the ranges of each band relative?
    a = a.astype('f4') / 65535 # Array-protocol type strings convention for data type
    b = b.astype('f4') / 65535 # f4 ~ 2^4 (16bit) floating-point
    indx = lambda_func(a,b)
    
    #np.nan_to_num(x = indx, copy=False, nan=0, posinf=0) # getting rid of nan and inf (inplace) - maybe find a version for np 1.16?


    indx[np.isnan(indx)] =  -1
    indx[np.isinf(indx)] =  -1

    indx = np.clip(indx, lower_bound, upper_bound)

    indx = np.interp(indx, (indx.min(), indx.max()), (0, 65535)) # retransformation to uint (so it can be stored in the same raster data as RGB)
    # indx = (indx * 65535).astype('uint16')
    # get info about datatype np.info(np.uint16)
    return indx


def calcIndxAll(band0, band1, band2, band3, band4, band5):
    np.seterr(divide='ignore', invalid='ignore')
    # Calculating all propsed indices
    # TO DO VERIFY THE BOUNDS OF ALL INDICES
    gi =    calcIndx(band1 ,band3, lower_bound=0, upper_bound=10, lambda_func = lambda a, b :  a / b ) # Greenness Index (also Green Difference Vegetation Index (GDVI))
    gndvi = calcIndx(band5 ,band1, lower_bound=-1, upper_bound=1, lambda_func = lambda a, b : (a - b) / (a + b) ) # Green Normalized Difference Vegetation Index
    msr =   calcIndx(band5 ,band3, lower_bound=0, upper_bound=10, lambda_func = lambda a, b : ((a/b)-1) / np.sqrt((a/b)+1) )  # modified simple ratio 670, 800
    ndvi =  calcIndx(band5 ,band3, lower_bound=-1, upper_bound=1, lambda_func = lambda a, b : (a - b) / (a + b) ) 
    pri =   calcIndx(band0 ,band2, lower_bound=-1, upper_bound=1, lambda_func=lambda a, b : (a - b) / (a + b) )  # photochemical reflectance index

    return (gi, gndvi, msr, ndvi, pri)

    # gi - index was originally designed with color-infrared photography to predict nitrogren requirements for corn
    # gndvi - is a chlorophyll index and is used at later stages of development, as it saturates later than NDVI.
    # msr - aims to linearize the  relationships between the index and biophysical parameters.
    # ndvi - green (active) biomass estimation
    # pri - indicator of photosynthetic efficiency as radation use efficency varies significantly between plants, environmental conditions (-1 to 1)

    #dict_gi = {     "expr"  : lambda a, b :  a / b ,
    #                "a"     : band1,
    #                "b"     : band2 }
    
    # Band 0:	530nm  	    (Slave 1)
    # Band 1: 	550nm		(Slave 2)
    # Band 2: 	570nm		(Slave 3)
    # Band 3: 	670nm		(Slave 4)
    # Band 4: 	700nm		(Slave 5)
    # Band 5: 	800nm		(Master)


# quick indice plot and infos - data must be provided as 2D numpy array
def pltIndx(indx):
    from matplotlib import pyplot as plt
    print('dtype:    {}'.format(indx.dtype))
    print('shape:    {}'.format(indx.shape))
    print('min val:  {}'.format(indx.min()))
    print('min mean:  {}'.format(indx.mean()))
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

    appendBandtoRaster(out_path, gi)        #8
    appendBandtoRaster(out_path, gndvi)     #9
    appendBandtoRaster(out_path, msr)       #10 
    appendBandtoRaster(out_path, ndvi)      #11 
    appendBandtoRaster(out_path, pri)       #12

    return None



