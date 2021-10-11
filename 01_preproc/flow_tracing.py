import xarray as xr
import numpy as np



def find_outlets(aspect,mask):
    
    """
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    mask: (xarray dataarray) watershed = 1, other = nan
    output: locations flowing out of watershed = 1, others = 0
    note: only works for D4 neighborhoods
    """
    
    # find north-facing locations with nan directly above
    n = aspect.where((np.isnan(mask.shift(y=-1)))&(aspect==1),0)
    
    # find east-facing locations with nan directly to the right
    e = aspect.where((np.isnan(mask.shift(x=-1)))&(aspect==2),0)
    
    # find south-facing locations with nan directly below
    s = aspect.where((np.isnan(mask.shift(y=1)))&(aspect==3),0)
    
    # find west-facing locations with nan directly to the left
    w = aspect.where((np.isnan(mask.shift(x=1)))&(aspect==4),0)
    
    # combine
    o = n + e + s + w
    
    # aspect values --> 1
    o = o.where(o==0,1)
    
    return o



def backtrace(recipients,mask,aspect):
    
    """
    recipients: (xarray dataarray) recipient locations
    mask: (xarray dataarray) watershed = 1, other = nan
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    output: (xarray dataarray) contributor locations = 1, all others = 0
    note: only works for D4 neighborhoods
    """
    
    # cell above recipient is contributor if aspect is south
    from_north = mask.where((recipients.shift(y=1)>0)&(aspect==3),0)
    
    # cell below recipient is contributor if aspect is north
    from_south = mask.where((recipients.shift(y=-1)>0)&(aspect==1),0)
    
    # cell to the right of recipient is contributor if aspect is west
    from_east = mask.where((recipients.shift(x=1)>0)&(aspect==4),0)
    
    # cell to the left of recipient is contributor if aspect is east
    from_west = mask.where((recipients.shift(x=-1)>0)&(aspect==2),0)
    
    # combine contributors
    feeders = from_north + from_east + from_south + from_west
    
    return feeders



def map_flowdist(start,mask,aspect,name='distance'):
    
    """
    start: (xarray dataarray) binary mask of outlets from which to start tracing
    mask: (xarray dataarray) watershed = 1, others = nan
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    name: name for output dataarray, default = 'distance'
    output: (xarray dataarray) length of flowpath out of the watershed for each location
    units: number of grid cells
    note: only works for D4 neighborhoods
    """
    
    # used to record map of flowpath lengths
    trace = start
    
    # contains current batch of recipient/contributor locations 
    trace_iter = start
    
    # counter used to identify flowpath length and indicate when recursion should stop
    i = 1
    
    # will be set to zero when no new contributors have been identified
    while i > 0:
        
        # find contributor locations for current recipient locations (or previous contributor locations)
        trace_iter = backtrace(recipients = trace_iter, mask = mask, aspect = aspect)
        
        # check if any new contributors have been found
        if trace_iter.sum() > 0:
            
            # increase counter
            i += 1
            
            # use counter to assign flowpath length to new contributor locations and add to map
            trace = trace + (trace_iter * i)
        
        # if no new contributors have been found
        else:
            
            # set counter to 0 to break recursion
            i = 0
    
    # set name of dataarray
    trace.name = name
    
    return trace



def find_headwater(flowdist,mask,aspect):
    
    """
    flowdist: (xarray dataarray) length of flowpath out of the watershed for each location
    mask: (xarray dataarray) watershed = 1, others = nan
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    output: (xarray dataarray) locations in watershed that have no contributing locations
    note: only works for D4 neighborhoods
    """
    
    # set all nan values to 0
    flowdist=flowdist.where(~np.isnan(flowdist),0)
    
    # find local maxima locations with no contributors
    head = (flowdist.where(((flowdist.shift(x=1)<flowdist)|(aspect.shift(x=1)!=2))\
                   &((flowdist.shift(x=-1)<flowdist)|(aspect.shift(x=-1)!=4))\
                   &((flowdist.shift(y=1)<flowdist)|(aspect.shift(y=1)!=1))\
                   &((flowdist.shift(y=-1)<flowdist)|(aspect.shift(y=-1)!=3)),0).where(~np.isnan(mask)))
    
    # flowdist values --> 1, other --> 0
    head = head.where(head==0,1).where(mask==1,0)
    
    return head



def forwardtrace(contributors,aspect,mask):
    
    """
    contributors: (xarray dataarray) contributor locations
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    output: (xarray dataarray) recipient locations = 1, all others = 0
    note: only works for D4 neighborhoods
    """
    
    def check_not_ready(contributors,shifted,mask,aspect):
        b = backtrace(recipients = shifted, mask = mask, aspect = aspect)
        b = b.where(contributors==0,0)
        fn = b.where(aspect==1,0).shift(y=1)
        fn = fn.where(fn==1,0)
        fe = b.where(aspect==2,0).shift(x=1)
        fe = fe.where(fe==1,0)
        fs = b.where(aspect==3,0).shift(y=-1)
        fs = fs.where(fs==1,0)
        fw = b.where(aspect==4,0).shift(x=-1)
        fw = fw.where(fw==1,0)
        f = fn + fe + fs +fw
        f = f.where(f==0,1)
        return f
    
    # recipient location is above north-facing contributor
    n = contributors.where(aspect==1,0)
    check = check_not_ready(contributors = contributors, shifted = n.shift(y=1), mask = mask, aspect = aspect)
    check = check.shift(y=-1)
    check = check.where(check==1,0)
    n_ready = n.where(check==0,0)
    n_not_ready = n.where(check==1,0)
    n = n_ready.shift(y=1)
    
    # recipient location is below south-facing contributor
    s = contributors.where(aspect==3,0)
    check = check_not_ready(contributors = contributors, shifted = s.shift(y=-1), mask = mask, aspect = aspect)
    check = check.shift(y=1)
    check = check.where(check==1,0)
    s_ready = s.where(check==0,0)
    s_not_ready = s.where(check==1,0)
    s = s_ready.shift(y=-1)
    
    # recipient location is to the right of east-facing contributor
    e = contributors.where(aspect==2,0)
    check = check_not_ready(contributors = contributors, shifted = e.shift(x=1), mask = mask, aspect = aspect)
    check = check.shift(x=-1)
    check = check.where(check==1,0)
    e_ready = e.where(check==0,0)
    e_not_ready = e.where(check==1,0)
    e = e_ready.shift(x=1)
    
    # recipient location is to the left of west-facing contributor
    w = contributors.where(aspect==4,0)
    check = check_not_ready(contributors = contributors, shifted = w.shift(x=-1), mask = mask, aspect = aspect)
    check = check.shift(x=1)
    check = check.where(check==1,0)
    w_ready = w.where(check==0,0)
    w_not_ready = w.where(check==1,0)
    w = w_ready.shift(x=-1)
    
    # combine into single dataarray but keep directions separate (needed for stream order calculation)
    f = xr.concat([n,e,s,w],dim='d')
    f['d'] = ['n','e','s','w']
    f = f.where(f>0)
    f_not_ready = n_not_ready + e_not_ready + s_not_ready + w_not_ready
    f_not_ready = f_not_ready.where(f_not_ready>0,0)
    
    return f,f_not_ready



def calc_strahler(contributors,aspect,mask):
    
    """
    contributors: (xarray dataarray) contributor locations
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    output: (xarray dataarray) recipient locations with values determined by strahler rules
    note: only accounts for current merges, merges with previously calculated streams handled outside this function
    note: outputs two dataarrays one for each strahler rule used (needed to handle other merges)
    note: only works for D4 neighborhoods
    """
    
    # get recipients
    f,f_not_ready = forwardtrace(contributors,aspect,mask)
    
    # number of contributors for each recipient location
    fcount = f.where(f>0).count(dim='d')
    
    # if only one contributor, recipient value = contributor value
    f1a = f.where(fcount==1,0).max(dim='d')
    
    # if two contributors but one maximum value, recipient value = maximum contributor value    
    f2a = f.where((fcount==2)&(f.where(f==f.max(dim='d'),0).sum(dim='d') == f.where(f==f.max(dim='d'),0).max(dim='d')),0).max(dim='d')
    
    # if three contributors but one maximum value, recipient value = maximum contributor value
    f3a = f.where((fcount==3)&(f.where(f==f.max(dim='d'),0).sum(dim='d') == f.where(f==f.max(dim='d'),0).max(dim='d')),0).max(dim='d')
    
    # if four contributors but one maximum value, recipient value = maximum contributor value
    f4a = f.where((fcount==4)&(f.where(f==f.max(dim='d'),0).sum(dim='d') == f.where(f==f.max(dim='d'),0).max(dim='d')),0).max(dim='d')
    
    # combine for map of recipients that do not increase stream order
    fa = f1a + f2a + f3a + f4a
    
    # if two contributors but multiple maximum values, recipient value = maximum value + 1
    f2b = f.where((fcount==2)&(f.where(f==f.max(dim='d'),0).sum(dim='d') > f.where(f==f.max(dim='d')).max(dim='d'))).max(dim='d') + 1
    f2b = f2b.where(f2b>0,0)
    
    # if three contributors but multiple maximum values, recipient value = maximum value + 1
    f3b = f.where((fcount==3)&(f.where(f==f.max(dim='d'),0).sum(dim='d') > f.where(f==f.max(dim='d')).max(dim='d'))).max(dim='d') + 1
    f3b = f3b.where(f3b>0,0)
    
    # if four contributors but multiple maximum values, recipient value = maximum value + 1
    f4b = f.where((fcount==4)&(f.where(f==f.max(dim='d'),0).sum(dim='d') > f.where(f==f.max(dim='d')).max(dim='d'))).max(dim='d') + 1
    f4b = f4b.where(f4b>0,0)
    
    # combine for map of recipients that increase stream order
    fb = f2b + f3b + f4b
    
    f = fa + fb + f_not_ready
    
    return f



def map_strahler(flowdist,mask,aspect,name='order'):
    
    """
    flowdist: (xarray dataarray) length of flowpath out of the watershed for each location
    mask: (xarray dataarray) watershed = 1, others = nan
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    name: name for output dataarray, default = 'order'
    note: if new recipient updates a previously mapped location, the entire flowpath from that point will be remapped and updated
    note: only works for D4 neighborhoods
    """
    
    # get headwater contributor locations
    h = find_headwater(flowdist = flowdist, mask = mask, aspect = aspect)
    
    # used to record stream order map
    s = h
    
    # contains current batch of recipient/contributor locations
    f = h
    
    # break recursion when no new contributors have been identified
    while f.sum()>f.max():
        
        # get strahler numbers for current contributors
        f = calc_strahler(contributors = f, aspect = aspect, mask = mask)
        
        # keep previously mapped that did not have a new merge, then add the newest iteration (removes erroneous values)
        s = s.where(f==0,0) + f
    
    # clean up map
    s = s * mask
    
    # set name of dataarray
    s.name = name
    
    return s

def calc_contrib_area(contributors,aspect,mask):
    
    """
    contributors: (xarray dataarray) contributor locations
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    output: (xarray dataarray) recipient locations with values equal to the total number of contributing cells
    note: only works for D4 neighborhoods
    """
    
    # get recipients
    f,f_not_ready = forwardtrace(contributors,aspect,mask)
    
    # sum total of contributing area
    f = f.sum(dim='d')
    
    # add one for recipient cell
    f = f.where(f>0) + 1
    
    # add not ready cells for future iteration
    f = f.where(f>0,0) + f_not_ready
    
    return f

def map_contrib_area(flowdist,mask,aspect,name='contrib'):
    
    """
    flowdist: (xarray dataarray) length of flowpath out of the watershed for each location
    mask: (xarray dataarray) watershed = 1, others = nan
    aspect: (xarray dataarray) north = 1, east = 2, south = 3, west = 4
    name: name for output dataarray, default = 'order'
    note: only works for D4 neighborhoods
    """
    
    # get headwater contributor locations
    h = find_headwater(flowdist = flowdist, mask = mask, aspect = aspect)
    
    # used to record map
    s = h
    
    # contains current batch of recipient/contributor locations
    f = h
    
    # break recursion when no new contributors have been identified
    while f.sum()>f.max():
        
        # get strahler numbers for current contributors
        f = calc_contrib_area(contributors = f, aspect = aspect, mask = mask)
        
        # keep previously mapped that did not have a new merge, then add the newest iteration (removes erroneous values)
        s = s.where(f==0,0) + f
    
    # clean up map
    s = s * mask
    
    # set name of dataarray
    s.name = name
    
    return s