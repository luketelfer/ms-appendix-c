# packages
from parflowio.pyParflowio import PFData
import rasterio as rio
import numpy as np
import xarray as xr
from pfpostproc.attrs import *
import pandas as pd
from datetime import datetime,timedelta
from memory_profiler import profile

# open pfb, return array
def pfb_arr(fpath):
    pfb = PFData(fpath)
    pfb.loadHeader();
    pfb.loadData();
    arr = pfb.copyDataArray()
    arr = arr.squeeze()
    pfb.close()
    return arr

# open raster, return array
def raster_arr(fpath):
    raster = rio.open(fpath)
    arr = raster.read(1).astype(float)
    arr = np.flip(arr,axis=0)
    return arr

def write_gage_csv(fpath,wy,outdir,outname):
    # read tab delimited txt file
    df1 = pd.read_csv(fpath,
                      sep='\t',
                      names=['agency',
                             'siteID',
                             'datetime',
                             'timezone',
                             'cfs',
                             'code'])
    df1['m3h'] = df1.cfs * 101.9406477312
    df1['datetime'] = df1['datetime'].apply(lambda x: datetime.strptime(x,'%Y-%m-%d %H:%M'))
    gdict = dict(zip(df1.datetime, df1.m3h))
    # account for missing timesteps
    df2 = pd.DataFrame()
    df2['datetime'] = np.arange(datetime.strptime(f'{wy-1}-10-01 00:00', '%Y-%m-%d %H:%M'),
                    datetime.strptime(f'{wy}-10-01 00:00', '%Y-%m-%d %H:%M'),
                    timedelta(hours=1)).astype(datetime)
    df2['m3h'] = df2['datetime'].map(gdict)
    # write to csv
    arr = df2.m3h.values
    np.savetxt(outdir + outname + '.csv', arr, delimiter=',', fmt='%f')

# add johnson creek stream gage data
def add_johnsoncreek(fpath):
    arr = np.loadtxt(fpath)
    da = xr.DataArray(
        arr,
        dims = 't',
        name = 'johnsoncreek')
    return da

# add krassel stream gage data
def add_krassel(fpath):
    arr = np.loadtxt(fpath)
    da = xr.DataArray(
        arr,
        dims = 't',
        name = 'krassel')
    return da
    