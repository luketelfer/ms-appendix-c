import argparse
import xarray as xr
from pfpostproc.workflow import *
from datetime import datetime,timedelta
import time
import sys

def zarr_write_ds(ds):
    ds.to_zarr(store='/home/ltelfer/scratch/upper_sfs/heter.zarr/ctr/',
               mode='a',
               group=f'ctr/{ctr}');
    return None

def domain_workflow(rundir,runname,tcoords):
    sys.stdout.write('\n\ngetting domain .......... ')
    start = time.perf_counter()
    domain = get_domain(rundir,runname)
    domain['t'] = tcoords
    end = time.perf_counter()
    elapsed = time.strftime("%H:%M:%S", time.gmtime(end - start))
    sys.stdout.write(elapsed)
    return domain

def pf_workflow(rundir,runname,domain,tcoords):
    sys.stdout.write('\ngetting parflow ......... ')
    start = time.perf_counter()
    pf = get_pf(rundir,runname,domain)
    pf['t'] = tcoords
    end = time.perf_counter()
    elapsed = time.strftime("%H:%M:%S", time.gmtime(end - start))
    sys.stdout.write(elapsed)
    sys.stdout.write('\nwriting parflow ......... ')
    start = time.perf_counter()
    zarr_write_ds(pf.expand_dims({'ctr':[ctr]}))
    end = time.perf_counter()
    elapsed = time.strftime("%H:%M:%S", time.gmtime(end - start))
    sys.stdout.write(elapsed)
    return pf

def clm_workflow(rundir,runname,domain,tcoords):
    sys.stdout.write('\ngetting clm ............. ')
    start = time.perf_counter()
    clm = get_clm(rundir,runname,domain)
    clm['t'] = tcoords
    end = time.perf_counter()
    elapsed = time.strftime("%H:%M:%S", time.gmtime(end - start))
    sys.stdout.write(elapsed)
    sys.stdout.write('\nwriting clm ............. ')
    start = time.perf_counter()
    zarr_write_ds(clm.expand_dims({'ctr':[ctr]}))
    end = time.perf_counter()
    elapsed = time.strftime("%H:%M:%S", time.gmtime(end - start))
    sys.stdout.write(elapsed)
    return clm

def calc_workflow(pf,domain,tcoords):
    sys.stdout.write('\ncalculating variables ... ')
    start = time.perf_counter()
    calcs = get_calc(pf,domain)
    calcs['t'] = tcoords
    end = time.perf_counter()
    elapsed = time.strftime("%H:%M:%S", time.gmtime(end - start))
    sys.stdout.write(elapsed)
    sys.stdout.write('\nwriting calculations .... ')
    start = time.perf_counter()
    zarr_write_ds(calcs.expand_dims({'ctr':[ctr]}))
    end = time.perf_counter()
    elapsed = time.strftime("%H:%M:%S", time.gmtime(end - start))
    sys.stdout.write(elapsed)
    return calcs
    
def main():
    sys.stdout.write(args.runname)
    start = time.perf_counter()
    tcoords = np.arange(datetime.strptime('2005-10-01 00:00', "%Y-%m-%d %H:%M"),
                        datetime.strptime('2006-10-01 00:00', "%Y-%m-%d %H:%M"),
                        timedelta(hours=1)).astype(datetime)
    domain = domain_workflow(rundir,args.runname,tcoords)
    pf = pf_workflow(rundir,args.runname,domain,tcoords)
    clm = clm_workflow(rundir,args.runname,domain,tcoords)
    calc = calc_workflow(pf,domain,tcoords)
    sys.stdout.write('\n\nTOTAL TIME:               ')
    end = time.perf_counter()
    elapsed = time.strftime("%H:%M:%S", time.gmtime(end - start))
    print(elapsed)
    print('')    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n','--runname',type=str,required=True)
    args = parser.parse_args()
    ctr = args.runname[3]
    rundir = f'../output_files/ctr/{args.runname}/'
    main()