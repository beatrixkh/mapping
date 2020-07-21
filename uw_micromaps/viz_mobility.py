import pandas as pd, numpy as np
import warnings

uw_geoids = ['53033004302',
 '53033004301',
 '53033004500',
 '53033005301',
 '53033005302',
 '53033004400',
 '53033005200']

def add_rolling_avg(df, windows = 7):
    
    #add numeric version of date, and make sure sorted
    df['num_date'] = date.datestr2num(df.index)
    df = df.sort_values(by='num_date')
    
    #blockgroup geoids
    raw_cols = [i for i in df.columns if len(str(i))==12]
    
    #add rolling avgs
    if type(windows)!=list:
        windows = [windows]
    for w in windows:
        for geoid in raw_cols:
            new = geoid + '_' + str(w) + 'day_avg'
            df[new] = df[geoid].rolling(14, win_type='triang', center=True).mean()
    
    return df

def add_sip_index(df, baseline):
    """input df: near-raw safegraph data, from compile_data_uw(), and baseline data, from calc_baseline()
    output df: formatted to include:
    (1) safegraph_sip_index, the percent of people NOT sheltering in place relative to baseline;
    (2) a datenum column (for sorting and plotting)
    (2) a date column (for labeling/reading)
    """
    
    #calculate sip
    df = df.merge(baseline, on = 'origin_census_block_group', how = 'left')
    #check if merge included all geoids
    if df[df.baseline_not_at_home.isna()].shape[0]>0:
        gids = df[df.baseline_not_at_home.isna()].origin_census_block_group.unique()
        warnings.warn('Warning: baseline missing for the following geoids: {}'.format(gids))
    
    df['sg_sip_index'] = (df['safegraph_not_at_home']-df['baseline_not_at_home'])/ df['baseline_not_at_home']*100
    
    #add date cols
    df['date'] = '2020-' + df['month'] + '-' + df['day']
    df['num_date'] = date.datestr2num(df.date)
    
    #check for nans
    if df[df.sg_sip_index.isna()].shape[0]>0:
        gids = df[df.sg_sip_index.isna()].origin_census_block_group.unique()
        warnings.warn('Warning: sip_index==nan for the following geoids: {}'.format(gids))
    
    return df

def calc_baseline(month = 2, days = np.arange(8,15)):
    
    #convert month and days to standardized format
    month = ('0' + str(month))[-2:]
    days = [('0' + str(day))[-2:] for day in days]
    
    #pull data
    baseline = [compile_data_uw(month = month, day = day) for day in days]
    baseline = pd.concat(baseline)
    
    #references for checks
    geoids = baseline.origin_census_block_group.unique()
    min_away, max_away = baseline.safegraph_not_at_home.min(), baseline.safegraph_not_at_home.max()
    
    #weighted sum, grouping by geoid
    baseline['wt'] = baseline['device_count'] / baseline.groupby('origin_census_block_group').device_count.transform(sum)
    baseline['safegraph_not_at_home'] = baseline['wt'] * baseline['safegraph_not_at_home']
    baseline = baseline.groupby('origin_census_block_group').sum().reset_index()
    baseline = baseline[['origin_census_block_group','safegraph_not_at_home']]
    baseline.rename(columns={'safegraph_not_at_home':'baseline_not_at_home'}, inplace=True)
    
    #checks
    assert(set(geoids)==set(baseline.origin_census_block_group.unique())), "Oops: geoid mismatch"
    assert(min_away <= baseline.baseline_not_at_home.min()), "Oops, check calculation; baseline_not_at_home too low"
    assert(max_away >= baseline.baseline_not_at_home.max()), "Oops, check calculation; baseline_not_at_home too high"
    
    return baseline


def compile_data_uw(month, day):
    
    #find file
    dir_2020 = '/ihme/limited_use/LIMITED_USE/PROJECT_FOLDERS/COVID19/SAFEGRAPH/social_distancing/2020'
    filename = '2020-' + month + '-' + day + '-social-distancing.csv'
    
    #read in df, get geoids as str
    df = pd.read_csv(dir_2020 + '/' + month + '/' + day + '/' + filename)
    df_geoids = pd.read_csv('/ihme/limited_use/LIMITED_USE/PROJECT_FOLDERS/COVID19/SAFEGRAPH/social_distancing/2020/03/18/2020-03-18-social-distancing.csv', dtype=str, usecols=['origin_census_block_group'])
    df.origin_census_block_group = df_geoids.astype(str)
    
    #define tract id
    df['tract_geoid'] = df.origin_census_block_group.str[:11]
    
    #subset to uw
    df = df[df.tract_geoid.isin(uw_geoids)]
    
    #define var of interest
    df['not_at_home'] = (df['device_count'] - df['completely_home_device_count'])/df['device_count']
    df['safegraph_not_at_home'] = df['not_at_home'] # safegraph_not_at_home = weighted.mean(not_at_home, device_count, ra.rm=T)) by = ('fips','date')
    
    #add date
    df['month'] = month
    df['day'] = day
    
    return df