import xarray as xr
from nlmpy import nlmpy
import pylandstats as pls
import numpy as np
from pyflowtrace import *

md = xr.open_dataset('md.nc')
number_burned = 200
total_cells = md.okburn.sum().values.tolist()
bp = number_burned/total_cells
up = 1 - bp

def map_burnflow(ds):
    mask = ds.outlet_distance_map.where(np.isnan(ds.outlet_distance_map),1)
    aspect = md.aspect.where(mask==1)
    out = find_outlets(aspect,mask)
    flowmap = map_flowdist(out,mask,aspect)
    return flowmap

def calc_lmetrics(da):
    ls = pls.Landscape(da.values,res=[1000,1000],nodata=0)
    ds = xr.Dataset()
    ds['mosaic'] = da
    ds['contagion'] = ls.contagion(percent=False)
    ds['edge_density'] = ls.edge_density(class_val=2)
    ds['number_of_patches'] = ls.number_of_patches(class_val=2)
    ds['largest_patch_index'] = ls.largest_patch_index(class_val=2)
    ds['landscape_shape_index'] = ls.landscape_shape_index(class_val=2)
    ds['number_burned'] = ls.proportion_of_landscape(class_val=2,percent=False) * total_cells
    ds['outlet_distance_map'] = md.flowdist.where(ds.mosaic==2)
    ds['contributing_area_map'] = md.contrib.where(ds.mosaic==2)
    ds['mean_outlet_distance'] = ds.outlet_distance_map.mean().values.tolist()
    ds['mean_contributing_area'] = ds.contributing_area_map.mean().values.tolist()
    ds['std_outlet_distance'] = ds.outlet_distance_map.std().values.tolist()
    ds['std_contributing_area'] = ds.contributing_area_map.std().values.tolist()
    ds['burnflow_map'] = map_burnflow(ds)
    ds['mean_burnflow_distance'] = ds.burnflow_map.where(ds.burnflow_map>0).mean().values.tolist()
    
    return ds

def generate_mpd(h,cp=[up,bp]):
    nRow,nCol = md.mask.shape
    nlm = nlmpy.mpd(nRow=nRow,
                    nCol=nCol,
                    mask=md.okburn,
                    h=h)
    c = nlmpy.classifyArray(nlm,cp) + 1
    da = xr.DataArray(c,dims=['y','x'])
    da = da.where(da>0,0)
    ds = calc_lmetrics(da)
    return ds

def generate_randomClusterNN(p,cp=[up,bp]):
    nRow,nCol = md.mask.shape
    nlm = nlmpy.randomClusterNN(nRow=nRow,
                                nCol=nCol,
                                mask=md.okburn,
                                n='4-neighbourhood',
                                p=p)
    c = nlmpy.classifyArray(nlm,cp) + 1
    da = xr.DataArray(c,dims=['y','x'])
    da = da.where(da>0,0)
    ds = calc_lmetrics(da)
    return ds

def generate_random(cp=[up,bp]):
    nRow,nCol = md.mask.shape
    nlm = nlmpy.random(nRow=nRow,
                       nCol=nCol,
                       mask=md.okburn)
    c = nlmpy.classifyArray(nlm,cp) + 1
    da = xr.DataArray(c,dims=['y','x'])
    da = da.where(da>0,0)
    ds = calc_lmetrics(da)
    return ds

def monte_carlo_mpd(h,n,cp=[up,bp]):
    lst = [generate_mpd(h=i,cp=cp) for i in h for j in np.arange(n)]
    ds = xr.concat(lst,dim='m')
    ds['m'] = np.arange(n*len(h)) + 1
    return ds

def monte_carlo_randomClusterNN(p,n,cp=[up,bp]):
    lst = [generate_randomClusterNN(p=i,cp=cp) for i in p for j in np.arange(n)]
    ds = xr.concat(lst,dim='m')
    ds['m'] = np.arange(n*len(p)) + 1
    return ds

def monte_carlo_random(n,cp=[up,bp]):
    lst = [generate_random(cp=cp) for i in np.arange(n)]
    ds = xr.concat(lst,dim='m')
    ds['m'] = np.arange(n) + 1
    return ds

