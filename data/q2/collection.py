# -*- coding: utf-8 -*-
"""
Data collection functions for the unemployment forecast model.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data.helper_funcs import data_collection, get_jv_tawteen

from config.parameters import get_default_parameters
from utils.db_connection import (
                                   database_engine_user, get_db_config)

#Migrated
def load_target_data(input_target_data, forecast_start, citizen_id, target_reg):
    """
    Load target unemployment data
    
    Args:
        input_target_data: Input target data table name
        forecast_start: Forecast start date
        citizen_id: Citizen ID ('Citizen' or 'Non-Citizen')
        target_reg: Target region
        
    Returns:
        DataFrame with target data
    """
    params = get_default_parameters()
    db_config = get_db_config()
    engine = database_engine_user(db_config.user_SC)
    
    # Load Citizen / Non-Citizen Data from ds_unemployment_total Table at S_COI_LABOUR_FORCE schema
    # df_unem = pd.read_sql(input_target_data, con=engine)
    df_unem = pd.read_sql(f"select * from {input_target_data}", con=engine)
    df_unem.rename(columns={'citizen':'CITIZEN'}, inplace=True)
    # df_unem["OBS_DT"] = df_unem["obs_dt"].apply(lambda x: x[0:4] + '-'+x[4:6] + '-'+ x[6:])
    df_unem["OBS_DT"] = df_unem['obs_dt'].str[0:4] + '-' + df_unem['obs_dt'].str[4:6] + '-' + df_unem['obs_dt'].str[6:]
    
    df_unem.drop(columns='obs_dt', inplace=True)
    
    #____________________________#
    
    # Plot target data
    positions = df_unem['OBS_DT'].to_list()[::24]
    #labels = [l.strftime('%Y-%m') for l in positions]
    fig, ax1 = plt.subplots()
    df_unem.plot(x='OBS_DT', y='CITIZEN', kind='scatter',rot=45, label='Unemployment Rate Citizen [%]', color='blue',  ax=ax1)
    #df_unem.plot(x='OBS_DT', y='NON-CITIZEN', kind='scatter',rot=45, label='Unemployment Rate Non-Citizen [%]', color='red',  ax=ax1)
    df_unem['OBS_DT'] = pd.to_datetime(df_unem['OBS_DT'], format='%Y-%m-%d')
    ax1.set_xticks(positions)
    fig, ax1 = plt.subplots()
    #df_unem.plot(x='OBS_DT', y='CITIZEN', kind='scatter',rot=45, label='Unemployment Rate Citizen [%]', color='blue',  ax=ax1)
    df_unem.plot(x='OBS_DT', y='NON-CITIZEN', kind='scatter',rot=45, label='Unemployment Rate Non-Citizen [%]', color='red',  ax=ax1)
    
    #___________________________________#
    df_unem.set_index('OBS_DT', inplace=True)
    df_unem_q = (df_unem.groupby(pd.PeriodIndex(df_unem.index , freq='Q')).sum())
    df_unem_q.replace(0,np.nan, inplace=True)
    df_unem_q.reset_index(inplace=True)

    qs = df_unem_q['OBS_DT'].astype(str)
    qs = pd.PeriodIndex(qs, freq='Q').to_timestamp()
    qs = qs + pd.offsets.QuarterEnd(0)
    df_unem_q['OBS_DT'] = qs

    df_unem_q = df_unem_q.set_index('OBS_DT')
    df_unem_q_filt = df_unem_q[df_unem_q.index>'2011'] # data before 2011 is quite coarse
    df_unem_q_filt.reset_index(inplace=True)

    fig, ax1 = plt.subplots()
    df_unem_q_filt.plot(x='OBS_DT', y='CITIZEN', kind='scatter',rot=45, label='Citizen', color='blue',  ax=ax1)
    df_unem_q_filt.plot(x='OBS_DT', y='NON-CITIZEN', kind='scatter',rot=45, label='Non-Citizen', color='red',  ax=ax1)
    df_unem_q_filt['OBS_DT'] = pd.to_datetime(df_unem_q_filt['OBS_DT'], format='%Y-%m-%d')
    positions = df_unem_q_filt.OBS_DT.to_list()[::10]
    labels = [l.strftime('%Y-%m') for l in positions]
    ax1.set_xticks(positions)
    ax1.set_xticklabels(labels)
    
    # Add missing observations
    #df_unem_q_filt.set_index('OBS_DT', inplace=True)
    df_new = pd.DataFrame({'OBS_DT':['2020-06-30'],
                            'NON-CITIZEN':[np.nan],
                            'CITIZEN':[np.nan],
                            'ALL-CITIZEN':[np.nan],
                            'LFS_Citizen':[np.nan],
                            'LFS_Non-Citizen':[np.nan]})
    df_unem_q_filt = df_unem_q_filt._append(df_new)
    df_new = pd.DataFrame({'OBS_DT':['2020-09-30'],
                            'NON-CITIZEN':[np.nan],
                            'CITIZEN':[np.nan],
                            'ALL-CITIZEN':[np.nan],
                            'LFS_Citizen':[np.nan],
                            'LFS_Non-Citizen':[np.nan]})
    df_unem_q_filt = df_unem_q_filt._append(df_new)
    df_new = pd.DataFrame({'OBS_DT':['2020-12-31'],
                            'NON-CITIZEN':[np.nan],
                            'CITIZEN':[np.nan],
                            'ALL-CITIZEN':[np.nan],
                            'LFS_Citizen':[np.nan],
                            'LFS_Non-Citizen':[np.nan]})
    df_unem_q_filt = df_unem_q_filt._append(df_new)
    df_unem_q_filt['OBS_DT'] = pd.to_datetime(df_unem_q_filt['OBS_DT'], format='%Y-%m-%d')
    
    df_unem_q_filt.set_index('OBS_DT',inplace=True)
    # Sorting the dataset before inerpolation
    df_unem_q_filt.sort_values(by='OBS_DT', inplace=True)
    # interpolation Data
    df_unem_q_filt_int = df_unem_q_filt.interpolate()
    df_unem_q_filt_int.reset_index(inplace=True)
    df_unem_q_filt_int.sort_values(by='OBS_DT', inplace=True)
    # Plot
    fig, ax1 = plt.subplots()
    df_unem_q_filt_int.plot(x='OBS_DT', y='CITIZEN', kind='scatter',rot=45, label='Citizen', color='blue',  ax=ax1)
    df_unem_q_filt_int.plot(x='OBS_DT', y='NON-CITIZEN', kind='scatter',rot=45, label='Non-Citizen', color='red',  ax=ax1)
    df_unem_q_filt_int['OBS_DT'] = pd.to_datetime(df_unem_q_filt_int['OBS_DT'], format='%Y-%m-%d')
    positions = df_unem_q_filt_int.OBS_DT.to_list()[::3]
    labels = [l.strftime('%Y-%m') for l in positions]
    ax1.set_xticks(positions)
    ax1.set_xticklabels(labels)
    
    # Format data
    df_unem_q_filt_int.set_index('OBS_DT', inplace=True)
    # Remove quarters beyond forecast_start
    ind = df_unem_q_filt_int[df_unem_q_filt_int.index>params.forecast_end].index
    df_unem_q_filt_int.drop(ind, inplace=True)
    if citizen_id == 'Citizen':
        df_unem_q_filt_int.rename(columns={'CITIZEN': target_reg}, inplace=True)
    elif citizen_id == 'Non-Citizen':
        df_unem_q_filt_int.rename(columns={'NON-CITIZEN':target_reg}, inplace=True)
    
    return df_unem_q_filt_int

#Migrated
def load_target_reg_data(input_target_data, citizen_id, target_reg):
    """
    Load target regional unemployment data
    
    Args:
        input_target_data: Input target data table name
        citizen_id: Citizen ID ('Citizen' or 'Non-Citizen')
        target_reg: Target region
        
    Returns:
        DataFrame with target regional data
    """
    params = get_default_parameters()
    db_config = get_db_config()
    engine = database_engine_user(db_config.user_SC)
    
    if citizen_id == 'Citizen':
        df_unem_reg = pd.read_sql(f"select * from {input_target_data}", con=engine)
        
    elif citizen_id == 'Non-Citizen':
        df_unem_reg = pd.read_sql(f"select * from {input_target_data}", con=engine)

    for col in df_unem_reg:
        if col != 'obs_dt':
            df_unem_reg[col] = df_unem_reg[col].astype(float)  
    
    # if region is Al Ain or Al Dhafra we have to remove 2015 datapoint
    if target_reg == 'Al Dhafra' or target_reg == 'Al Ain':
        ind = df_unem_reg[df_unem_reg['obs_dt']=='20151201'].index
        df_unem_reg.loc[ind,['Al Dhafra' , 'Al Ain']]=np.nan
    
    df_unem_reg.rename(columns={'obs_dt':'OBS_DT'}, inplace=True)
    df_unem_reg['OBS_DT'] = df_unem_reg["OBS_DT"].astype(str)
    # df_unem_reg["OBS_DT"] = df_unem_reg["OBS_DT"].apply(lambda x: x[0:4]+'-'+x[4:6]+'-'+x[-2:])
    df_unem_reg["OBS_DT"] = df_unem_reg['OBS_DT'].str[0:4] + '-' + df_unem_reg['OBS_DT'].str[4:6] + '-' + df_unem_reg['OBS_DT'].str[6:]
    df_unem_reg["OBS_DT"] = pd.to_datetime(df_unem_reg["OBS_DT"])
    df_unem_reg.set_index('OBS_DT', inplace=True)
    
    
    df_unem_reg_na = df_unem_reg.dropna(how='all')
    positions = df_unem_reg_na.index.to_list()
    #labels = [l.strftime('%Y-%m') for l in positions]
    
    fig, ax1 = plt.subplots()
    ax1.plot(df_unem_reg_na.index, df_unem_reg_na[df_unem_reg_na.columns[0]], '-o', color='blue', linewidth = 2,  label=df_unem_reg_na.columns[0])
    ax1.plot(df_unem_reg_na.index, df_unem_reg_na[df_unem_reg_na.columns[1]], '-o', color='red', linewidth = 2,  label=df_unem_reg_na.columns[1])
    ax1.plot(df_unem_reg_na.index, df_unem_reg_na[df_unem_reg_na.columns[2]], '-o', color='green', linewidth = 2,  label=df_unem_reg_na.columns[2])
    ax1.legend(loc = 'upper left')
    ax1.set_ylabel('Unemployment Rate by Region [%]')
    #ax1.set_xticks(positions, rotation=45)
    plt.xticks(rotation=45)
    plt.show()
    
    df_unem_q = (df_unem_reg.groupby(pd.PeriodIndex(df_unem_reg.index , freq='Q')).sum())
    df_unem_q.reset_index(inplace=True)

    
    qs = df_unem_q['OBS_DT'].astype(str)
    qs = pd.PeriodIndex(qs, freq='Q').to_timestamp()
    qs = qs + pd.offsets.QuarterEnd(0)
    df_unem_q['OBS_DT'] = qs
    df_unem_q.set_index('OBS_DT',inplace=True)
    df_unem_q.replace(0,np.nan, inplace=True)
    range_opt = 'C'
    df_unem_q_filt = df_unem_q[df_unem_q.index>'2010'] # Abu Dhabi
    #df_unem_q_filt = df_unem_q[df_unem_q.index>'2010'] # Al Ain & Al Dhafra
    # df_unem_q_filt.reset_index(inplace=True)
    # Interpolate to quarterly basis
    df_unem_q_filt_int = df_unem_q_filt.interpolate(method='time')
    
    
    #Interpolated data
    df_unem_q_filt_int.reset_index(inplace=True)
    fig, ax1 = plt.subplots()
    ax1.plot(df_unem_q_filt_int.OBS_DT, df_unem_q_filt_int[df_unem_q_filt_int.columns[1]], '-o', color='blue', linewidth = 2,  label=df_unem_reg_na.columns[0])
    ax1.plot(df_unem_q_filt_int.OBS_DT, df_unem_q_filt_int[df_unem_q_filt_int.columns[2]], '-o', color='red', linewidth = 2,  label=df_unem_reg_na.columns[1])
    ax1.plot(df_unem_q_filt_int.OBS_DT, df_unem_q_filt_int[df_unem_q_filt_int.columns[3]], '-o', color='green', linewidth = 2,  label=df_unem_reg_na.columns[2])
    ax1.legend(loc = 'upper left')
    ax1.set_ylabel('Unemployment Rate by Region [%]')
    #ax1.set_xticks(positions, rotation=45)
    plt.xticks(rotation=45)
    df_unem_q_filt_int.set_index('OBS_DT', inplace=True)
    ind = df_unem_q_filt_int[df_unem_q_filt_int.index>params.forecast_end].index
    df_unem_q_filt_int.drop(ind, inplace=True)

    return df_unem_q_filt_int

#Migrated
def load_indicators_data(indicator_id,  cdir, userSE_ECON, userLD_ECON, user_MISC, target, deflators_calc):
    params = get_default_parameters()
    # conn, c = database_connection_user(userSE_ECON)
    # conn_ld, c_ld = database_connection_user(userLD_ECON)
    #pmi_sector = pmi_sectors[1]
    engine = database_engine_user(userSE_ECON)
    # date_col = 'OBS_DT'
    target_ind = '4658_Emirate Of Abu Dhabi_General Index'
    analytical_df_complete = data_collection(indicator_id, deflators_calc, target_ind, userSE_ECON,
                                                  params.save_raw_analytical_df,
                                                  params.save_transformed_analytical_df, params.forecast_start)
    df0 = analytical_df_complete.copy()
    # df0 = analytical_df_complete
    #############################################
    # Statistical Analysis to assess data quality and usefulness
    df0.drop(columns=['INSERT_DT','RUN_SEQ_ID'], inplace=True)
    # grouping to quarterly level
    # read indicators type in order to aggregate or interpolate to quarterly frequency properly
    engine = database_engine_user(userSE_ECON)
    df_type = pd.read_sql('select * from DS_INDICATORS_AGGREGATION', con=engine)
    aa= [x for x in df_type['Indicator'].to_list() if x not in df0.columns.to_list()]
    df_type.drop(df_type[df_type['Indicator'].isin(aa)].index, inplace=True)
    col_last = df_type[df_type.aggregate_type=='last']['Indicator'].to_list()
    df0_last = (df0[col_last].groupby(pd.PeriodIndex(df0.index , freq='Q')).last())
    col_sum = df_type[df_type.aggregate_type=='sum']['Indicator'].to_list()
    df0_sum = (df0[col_sum].groupby(pd.PeriodIndex(df0.index , freq='Q')).sum())
    df0_q = pd.merge(df0_last, df0_sum, left_index=True, right_index=True, how='outer')
    df0_q = df0_q.replace(0.0, np.nan)
    df0_q.reset_index(inplace=True)
    df0_q.rename(columns={'index':'OBS_DT'}, inplace=True)
    qs = df0_q['OBS_DT'].astype(str)
    qs = pd.PeriodIndex(qs, freq='Q').to_timestamp()
    qs = qs + pd.offsets.QuarterEnd(0)
    df0_q['OBS_DT'] = qs
    df0_q.set_index(['OBS_DT'], inplace=True)
    df0_q.dropna(how='all', axis=1, inplace=True)
    df0 = df0_q.copy()

    # create new indicator as oil revenue
    #df0['oil_revenue'] = df0['OPECDALY Index'] * df0['OPCRUAE Index']
    
    #########  Add job Vacancies from Tawteen (only for UAE Citizen)
    #fname = 'job_vacancies2015_2022.xlsx'
    #cdir_tawteen = cdir 
    df_jv_final = get_jv_tawteen(target)
    # fig, ax1 = plt.subplots()
    # ax1.plot(df_jv_final_inter.index, df_jv_final_inter[regions2[0]], '-o', color='black', linewidth = 2,  label='Total')
    # ax1.plot(df_jv_final_inter.index, df_jv_final_inter[regions2[1]], '-o', color='blue', linewidth = 2,  label=regions2[1])
    # ax1.plot(df_jv_final_inter.index, df_jv_final_inter[regions2[2]], '-o', color='green', linewidth =2,  label=regions2[2])
    # ax1.plot(df_jv_final_inter.index, df_jv_final_inter[regions2[3]], '-o', color='red', linewidth = 2,  label=regions2[3])
    # ax1.legend(loc = 'upper right')
    # ax1.set_ylabel('Job Vacancies Tawteen')
    # plt.show()
    #df_jv_final.drop(df_jv_raw.index[-1])
    # df_jv_final = pd.merge(df0[target_ind], df_jv_final, left_index=True, right_index=True, how='outer')
    df_jv_final = pd.merge(df0, df_jv_final, left_index=True, right_index=True, how='outer')
    df_jv_final_inter = df_jv_final.interpolate()
    df_jv_final_inter.rename(columns={'No of Vacancies':'JV Tawteen All Regions',
                                      'Abu Dhabi':'JV Tawteen Abu Dhabi',
                                      'Al Ain':'JV Tawteen Al Ain',
                                      'Al Dhafra':'JV Tawteen Al Dhafra'}, inplace=True)
    df0 = pd.merge(df0, df_jv_final_inter[[ 'JV Tawteen All Regions', 
                                            'JV Tawteen Abu Dhabi',
                                            'JV Tawteen Al Ain',
                                            'JV Tawteen Al Dhafra']], left_index=True, right_index=True, how='outer')
    return df0


