#------------------------------------------------------------##
# 07/1/2020
# Beatrix Haddock
# Micromaps visualizing UW mobilty 2020
# IMPORTS----------------------------------------------------##

import pandas as pd, numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as date

from matplotlib.ticker import FixedLocator, FixedFormatter
from matplotlib.backends.backend_pdf import PdfPages

import shapefile as shp

# LOAD ALL GLOBALS ------------------------------------------##

def read_shapefile(sf):
    
    #fetching the headings from the shape file
    fields = [x[0] for x in sf.fields][1:]
    
    #fetching the records from the shape file
    records = [list(i) for i in sf.records()]
    shps = [s.points for s in sf.shapes()]
    
    #converting shapefile data into pandas dataframe
    df = pd.DataFrame(columns=fields, data=records)
    
    #assigning the coordinates
    df = df.assign(coords=shps)

    return df

sf = shp.Reader('/home/j/temp/beatrixh/sim_science/census_GIS/tl_2018_53_bg/tl_2018_53_bg.shp')
df = read_shapefile(sf)

sf_edges = shp.Reader('/home/j/temp/beatrixh/sim_science/census_GIS/tl_2019_53033_edges/tl_2019_53033_edges.shp')
df_edges = read_shapefile(sf_edges)

sf_water = shp.Reader('/home/j/temp/beatrixh/sim_science/census_GIS/tl_2019_53033_areawater/tl_2019_53033_areawater.shp')
df_water = read_shapefile(sf_water)

uw_geoids = ['53033004302',
 '53033004301',
 '53033004500',
 '53033005301',
 '53033005302',
 '53033004400',
 '53033005200']

all_geoids = ['530330043013',
 '530330043022',
 '530330052001',
 '530330053014',
 '530330044004',
 '530330043021',
 '530330044001',
 '530330044003',
 '530330044002',
 '530330043011',
 '530330052003',
 '530330052002',
 '530330053012',
 '530330053013',
 '530330052004',
 '530330052005',
 '530330053021',
 '530330053022',
 '530330053023',
 '530330043012',
 '530330053011',
 '530330045002',
 '530330045001']


# DEFINE FNS-------------------------------------------------##

def fill_water(df, sf):
    for i in df.index:
        shape_ex = sf.shape(i)
        x_lon = np.zeros((len(shape_ex.points),1))
        y_lat = np.zeros((len(shape_ex.points),1))
        for ip in range(len(shape_ex.points)):
            x_lon[ip] = shape_ex.points[ip][0]
            y_lat[ip] = shape_ex.points[ip][1]
        plt.fill(x_lon,y_lat, color = 'skyblue')

def plot_mult_locations(sf, df, data, dcounts, geoid, all_geoids, l, b, w_map = 2.5, w_time = 3, h=3, 
                        colors = ['orange','palevioletred','steelblue','olive'], 
                        markers = ['o','^','s','P']):
    """"outputs four geoids on one row, with map on left and timeseries on right
    """
    #plot timeseries
    ax = None
    ax = plot_mult_timetrends(data, geoid, cols = [i for i in data.columns if (i.endswith('21day_avg') and
                                    i[:12] in geoid)],
                              area = [l + w_map + 0.3,b + h/2, w_time, h/2], colors = colors,
                              markers = markers, sharex = ax, ylim_bottom = -50, ylim_top = 50,
                              xlabels=[''] * 6)
    
    # plot dcount timeseries
    ax = None
    ax = plot_mult_timetrends(dcounts, geoid, cols = [i for i in data.columns if (i.endswith('21day_avg') and
                                    i[:12] in geoid)],
                              area = [l + w_map + 0.3,b,w_time,h/2], colors = colors, markers = markers, sharex = ax,
                             ylim_bottom = 0, ylim_top = 200, ylabel = 'Device count',
                             xlabels=data.index[np.arange(0,data.shape[0],28)].tolist())
    
    #plot map
    plt.axes([l,b,w_map,h])
    for i in df_edges[df_edges.ZIPR.isin(['98105','98195','98115','98102','98112'])].index:
        shape_ex = sf_edges.shape(i)
        x_lon = np.zeros((len(shape_ex.points),1))
        y_lat = np.zeros((len(shape_ex.points),1))
        for ip in range(len(shape_ex.points)):
            x_lon[ip] = shape_ex.points[ip][0]
            y_lat[ip] = shape_ex.points[ip][1]
        plt.plot(x_lon,y_lat, color = 'black')
    
    outline_geoids(sf = sf, df = df, geoids = all_geoids, include_labels=False)
    fill_blockgroups(sf = sf, df = df, geoids = geoid, colors=colors)
    
        
    plt.xlim(-122.325,-122.25)
    plt.ylim(47.645,47.68)
    plt.axis('off')

def plot_mult_timetrends(data, geoids, cols, area, colors, markers, sharex,
                         ylim_bottom = -150, ylim_top = 150, ylabel = 'Pct change in mobility', xlabels=None):
    """outputs four timeseries, layered, using inputted vector of colors
    """
    ax = plt.axes(area, sharex = None)
    
    cols = cols
    plt.hlines(0,data.num_date.min(),data.num_date.max())
    i = 0
    for y in cols:
        pts = y[:12]
        
#         lim = ylim
#         plt.xlabel('date', fontsize=18)
        plt.ylabel(ylabel, fontsize=22)

        plt.yticks(fontsize=30)          

        x_locator = FixedLocator(data.num_date[np.arange(0,data.shape[0],7)].tolist())
        ax.xaxis.set_minor_locator(x_locator)
        plt.grid(axis='x', which = 'both')       
    
        plt.plot(data['num_date'], data[y], color = colors[i], linewidth=5)
        i = i+ 1
        plt.xticks(ticks = data.num_date[np.arange(0,data.shape[0],28)].tolist(),
               labels = xlabels, rotation=30, ha='right',
               fontsize=30)
    plt.ylim(ylim_bottom,ylim_top)

    return ax

def fill_blockgroups(sf, df,geoids, colors):
    """ takes in geoid list and a color, and fills in those geoids
    """
    color_ids = []
    for i in geoids:
        color_ids.append(df[df.GEOID==i].index[0])
    
    i = 0
    for bg in color_ids:
        shape_ex = sf.shape(bg)
        x_lon = np.zeros((len(shape_ex.points),1))
        y_lat = np.zeros((len(shape_ex.points),1))
        for ip in range(len(shape_ex.points)):
            x_lon[ip] = shape_ex.points[ip][0]
            y_lat[ip] = shape_ex.points[ip][1]
        plt.fill(x_lon,y_lat, colors[i])
        i = i +1

def outline_geoids(sf, df, geoids, include_labels=True):
    """plots outlines for list of inputted geoids
    """
#     df = read_shapefile(sf)
#     df['tract_geoid'] = df.GEOID.str[:11]
    bg_id = []
    for i in geoids:
        bg_id.append(df[df.GEOID==i].index[0])

    itr = 0
    for shape in sf.shapeRecords():
        if itr in bg_id:
            x = [i[0] for i in shape.shape.points[:]]
            y = [i[1] for i in shape.shape.points[:]]
            plt.plot(x, y, 'k')
        
        
            if include_labels:
                x0 = np.mean(x)
                y0 = np.mean(y)
                label = df.iloc[itr].density_label

                plt.text(x0, y0, label, fontsize=8)
                
        itr = itr+1
        
def find_order(data, ending = '7day_avg', fn = np.mean):
    """ sorts df by geoid from highest to lowest mobility as defined by collapsing full time series with fn
    """
    subset = data[[i for i in data.columns if i.endswith(ending)]]
    df = pd.DataFrame(data = [subset.columns.str[:12].tolist(),[fn(data.iloc[:,i]) for i in range(subset.shape[1])]],
                           index = ['geoid','val']).T
    df = df.sort_values(by='val', ascending=False)
    df.index = range(df.shape[0])
    df['plot_group'] = [np.floor(i/3) + 1 for i in df.index]
    df['order_in_group'] = [i % 3 for i in df.index]
    
    return df


