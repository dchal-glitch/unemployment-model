import datetime

import numpy as np
import pandas as pd
from pandas.api.types import is_object_dtype
from sqlalchemy import types

from config.parameters import get_default_parameters
from utils.db_connection import database_engine_user, get_db_config

lags_for_drivers = {"PMI_Whole Economy_Abu Dhabi_Three month Moving Average_Overall PMI_BACKLOGS":1,
                    "COA Comdty_MONTHLY":7,
                    "SRRGGDP Index_QUARTERLY":6,
                    "USTWBGD Index_WEEKLY":6,
                    '1830_Public Administration and defence':2,
                    "GPR":2}

def get_col_format(df):
    dtyp = {c:types.VARCHAR(100)
    for c in df.columns[df.dtypes == 'object'].tolist()}
    dtyp_float32 = {c:types.NUMERIC(10,5)
    for c in df.columns[df.dtypes == 'float64'].tolist()}
    dtyp_int32 = {c:types.FLOAT()
    for c in df.columns[df.dtypes == 'int32'].tolist()}
    dtyp_int64 = {c:types.NUMERIC(10,0)
    for c in df.columns[df.dtypes == 'int64'].tolist()}
    dtyp_float = {c:types.FLOAT()
    for c in df.columns[df.dtypes == 'float'].tolist()}
    dtyp_date = {c:types.DATE()
    for c in df.columns[df.dtypes == 'datetime64[ns]'].tolist()}
    dtyp_all = {**dtyp, **dtyp_float, **dtyp_int32, **dtyp_int64 ,**dtyp_float,**dtyp_date}
    return dtyp_all


def get_gpr_data():
    gpr_df = pd.read_excel(r"E:\Mebin\Geopolitical Indicators\GPR Index.xlsx")
    gpr_df.set_index('Date (year/month)',inplace=True)
    needed = ['Recent GPR (Index: 1985:2019=100)']
    gpr_df = gpr_df[needed].dropna()
    gpr_df_resampled = gpr_df.resample('Q').mean()
    gpr_df_resampled.rename(columns={'Recent GPR (Index: 1985:2019=100)':'GPR'},inplace=True)
    return gpr_df_resampled


def get_data_for_what_if():
    db_config = get_db_config()
    conn = database_engine_user(db_config.userLD_ECON)
    pmi = pd.read_sql("""select OBS_DT, VALUE from VW_COI_PMI 
    where indicator_id = 'PMI_Whole Economy_Abu Dhabi_Three month Moving Average_Overall PMI_BACKLOGS'""",con=conn)
    pmi.columns = [i.upper() for i in pmi.columns]
    pmi.VALUE = pmi.VALUE.astype("float")    
    pmi.OBS_DT = pd.to_datetime(pmi.OBS_DT,format="%Y%m%d")
    pmi_mod = pmi.set_index("OBS_DT").resample("Q").mean()
    pmi_mod  = pmi_mod[["VALUE"]]
    pmi_mod.rename(columns={"VALUE":"PMI_Whole Economy_Abu Dhabi_Three month Moving Average_Overall PMI_BACKLOGS"},inplace=True)
    co1 = pd.read_sql("""select OBS_DT , VALUE from 
    VW_BLOOMBERG_ECO_ANALYSIS_KPIS where indicator_id = 'COA Comdty_MONTHLY'""",con=conn)
    co1.columns = [i.upper() for i in co1.columns]
    co1.VALUE = co1.VALUE.astype("float")
    co1.OBS_DT = pd.to_datetime(co1.OBS_DT,format="%Y%m%d")
    co1_mod = co1.set_index("OBS_DT").resample("Q").mean()
    co1_mod = co1_mod[["VALUE"]]
    co1_mod.rename(columns={"VALUE":"COA Comdty_MONTHLY"},inplace=True)
    co1_mod = pd.merge(co1_mod,pmi_mod,right_index=True,left_index=True,how='outer')
    srr = pd.read_sql("""SELECT OBS_DT , VALUE FROM VW_BLOOMBERG_ECO_ANALYSIS_KPIS WHERE INDICATOR_ID  = 'SRRGGDP Index_QUARTERLY'""",con=conn)
    srr.columns = [i.upper() for i in srr.columns]
    srr.VALUE = srr.VALUE.astype("float")
    srr.OBS_DT = pd.to_datetime(srr.OBS_DT,format="%Y%m%d")
    srr_mod = srr.set_index("OBS_DT").resample("Q").mean()
    srr_mod = srr_mod[["VALUE"]]
    srr_mod.rename(columns={"VALUE":"SRRGGDP Index_QUARTERLY"},inplace=True)
    out1 = pd.merge(co1_mod,srr_mod,right_index=True,left_index=True,how='outer')
    ust = pd.read_sql("""SELECT OBS_DT , VALUE FROM VW_BLOOMBERG_ECO_ANALYSIS_KPIS WHERE INDICATOR_ID  = 'USTWBGD Index_WEEKLY'""",con=conn)
    ust.columns = [i.upper() for i in ust.columns]
    ust.VALUE = ust.VALUE.astype("float")
    ust.OBS_DT = pd.to_datetime(ust.OBS_DT,format="%Y%m%d")
    ust_mod = ust.set_index("OBS_DT").resample("Q").mean()
    ust_mod = ust_mod[["VALUE"]]
    ust_mod.rename(columns={"VALUE":"USTWBGD Index_WEEKLY"},inplace=True)
    out2 = pd.merge(out1,ust_mod,right_index=True,left_index=True,how='outer')
    gov_spending_df = pd.read_sql("select obs_dt,VALUE,year,ACTIVITIES_EN , indicator_id as indicator_id , quarter_en from VW_STATISTICAL_INDICATORS where indicator_id='1830'",con=database_engine_user(db_config.user_SC))
    gov_spending_df["indicator_id"] = gov_spending_df["indicator_id"]+gov_spending_df["activities_en"].apply(lambda x : '_'+x)
    gov_spending_df = gov_spending_df[['obs_dt','value','indicator_id']]
    gov_spending_df.columns = [i.upper() for i in gov_spending_df.columns]
    gov_spending_df = gov_spending_df.pivot_table('VALUE',['OBS_DT'],'INDICATOR_ID').reset_index()
    gov_spending_df = gov_spending_df[['OBS_DT','1830_Public Administration and defence','1830_Total']]
    gov_spending_df.OBS_DT = pd.to_datetime(gov_spending_df.OBS_DT,format="%Y%m%d")
    gov_spending_df = gov_spending_df.set_index("OBS_DT").resample("Q").mean()
    out3 = pd.merge(out2,gov_spending_df,right_index=True,left_index=True,how='outer')
    gpr = get_gpr_data()
    final_drivers = pd.merge(out3,gpr,right_index=True,left_index=True,how='outer')
    min_val  = final_drivers.index.min()
    max_val = final_drivers.index.max() + pd.DateOffset(months= 15)
    ix = pd.date_range(start=min_val, end=max_val, freq='Q')
    final_drivers = final_drivers.reindex(ix)
    for col in lags_for_drivers:
        final_drivers[col] = final_drivers[col].shift(lags_for_drivers[col])
    return final_drivers



def lag_selection1(data, max_lag, min_lag, targets):
    print('##Start lag selection based on correlation')
    lag_table = pd.DataFrame()
    for i in range(min_lag,max_lag):
        #save target for use later without move forward the data
        target = data[targets]
        #save all data without the target
        data_matrix = data.drop(targets, axis = 1)
        #move forward or backward the data i months
        data_matrix = data_matrix.shift(i)
        #join the moved data with the target
        data_matrix =  pd.merge(target, data_matrix, left_index=True, right_index=True, how='left')
        #data_matrix = data_matrix[data_matrix.index>'2000-12-31']
        #correaltion matrix
        correlation_matrix = data_matrix.corr(method='pearson', min_periods=6)
        #select just first row of correlation matrix because is the correlation of all variables with he target
        lag_table_temp = correlation_matrix.iloc[[0]]
        #save the lag
        lag_table_temp['Lag'] = i
        #save all lags
        lag_table = pd.concat([lag_table, lag_table_temp], sort=False) 

    #clean data
    all_lags_table = lag_table
    all_lags_table.index = all_lags_table['Lag']
    all_lags_table = all_lags_table.drop('Lag', axis = 1) 
    all_lags_table = all_lags_table.drop(targets, axis = 1)

    lag_table = all_lags_table.fillna(0)
    # put all data in abslute value
    lag_table_abs = lag_table.abs()
    # select max correlation in abs value
    lag_table = lag_table_abs.idxmax(axis = 0)
    lag_table = pd.DataFrame(lag_table)
    lag_table = lag_table.rename(columns={0:'Lag No'})
    lag_table ['TARGET'] = targets
    lag_table['Correlation'] = lag_table_abs.max(axis =0)
    all_lags_table ['TARGET'] = targets
    return(lag_table, all_lags_table)

def scenarios_table_creator(dfall0,Tstart):
    db_config = get_db_config()
    params = get_default_parameters()
    engine = database_engine_user(db_config.userSDWH)
    if params.save_param:
        Tstart = datetime.datetime.strptime(Tstart,"%Y-%m-%d")
        # Tstart = Tstart.replace(day=1)
        tmp_cols =  dfall0.columns
        #specify ranges for drivers
        Srange1 =  [-0.25, -0.12, 0, 0.24, 0.49]
        Srange2 =  [-0.09,-0.04,0,0.04,0.09]    
        Srange3 = [-0.08, -0.04, 0, 0.05, 0.1]    
        Srange4 =  [-0.06, -0.03, 0, 0.04, 0.08]   
        Srange5 =  [-0.06, -0.03, 0, 0.04, 0.09]   
        Srange6 = [-0.07, -0.04, 0, 0.06, 0.13]  
        Srange7 = [-0.06, -0.03, 0, 0.04, 0.09]          
        # variables for driver
        scenario_variables_temp = [ 'COA Comdty_MONTHLY', 'PMI_Whole Economy_Abu Dhabi_Three month Moving Average_Overall PMI_BACKLOGS','SRRGGDP Index_QUARTERLY','USTWBGD Index_WEEKLY','1830_Public Administration and defence','GPR','1830_Total']
        fvar1 = scenario_variables_temp[0]
        fvar2 = scenario_variables_temp[1]
        fvar3 = scenario_variables_temp[2]
        fvar4 = scenario_variables_temp[3]
        fvar5 = scenario_variables_temp[4]
        fvar6 = scenario_variables_temp[5]
        fvar7 = scenario_variables_temp[6]
        SSrange1 = [] 
        SSrange2 = [] 
        SSrange3 = []
        SSrange4 = []
        SSrange5 = []
        SSrange6 = []
        SSrange7 = []
        for fcoeff1 in Srange1:
            dfall3 = dfall0.copy()
            fcoeff_monthly = fcoeff1
            dfall3.loc[Tstart][fvar1] =  dfall3.loc[Tstart][fvar1]*fcoeff_monthly
            SSrange1.append(dfall3.loc[Tstart][fvar1])
        for fcoeff2 in Srange2:
            dfall3 = dfall0.copy()
            fcoeff_monthly   = fcoeff2
            dfall3.loc[Tstart][fvar2] =  dfall3.loc[Tstart][fvar2]*fcoeff_monthly
            SSrange2.append(dfall3.loc[Tstart][fvar2])
        for fcoeff3 in Srange3:
            dfall3 = dfall0.copy()
            fcoeff_monthly   = fcoeff3
            dfall3.loc[Tstart][fvar3] =  dfall3.loc[Tstart][fvar3]*fcoeff_monthly
            SSrange3.append(dfall3.loc[Tstart][fvar3])
        for fcoeff4 in Srange4:
            dfall3 = dfall0.copy()
            fcoeff_monthly  = fcoeff4
            dfall3.loc[Tstart][fvar4] =  dfall3.loc[Tstart][fvar4]*fcoeff_monthly
            SSrange4.append(dfall3.loc[Tstart][fvar4])
        for fcoeff5 in Srange5:
            dfall3 = dfall0.copy()
            fcoeff_monthly  = fcoeff5
            dfall3.loc[Tstart][fvar5] =  dfall3.loc[Tstart][fvar5]*fcoeff_monthly
            SSrange5.append(dfall3.loc[Tstart][fvar5])
        for fcoeff6 in Srange6:
            dfall3 = dfall0.copy()
            fcoeff_monthly  = fcoeff6
            dfall3.loc[Tstart][fvar6] =  dfall3.loc[Tstart][fvar6]*fcoeff_monthly
            SSrange6.append(dfall3.loc[Tstart][fvar6]) 
        for fcoeff7 in SSrange7:
            dfall3 = dfall0.copy()
            fcoeff_monthly  = fcoeff7
            dfall3.loc[Tstart][fvar7] =  dfall3.loc[Tstart][fvar7]*fcoeff_monthly
            SSrange7.append(dfall3.loc[Tstart][fvar7])                        
        

        SSrange1 =[x-SSrange1[2] for x in SSrange1]
        SSrange2 =[x-SSrange2[2] for x in SSrange2]
        SSrange3 =[x-SSrange3[2] for x in SSrange3]
        SSrange4 =[x-SSrange4[2] for x in SSrange4]
        SSrange5 =[x-SSrange5[2] for x in SSrange5]
        SSrange6 =[x-SSrange6[2] for x in SSrange6]
        SSrange7 =[x-SSrange7[2] for x in SSrange7]

        value_set1 = pd.DataFrame(columns = ['PARAMETER_1_NAME',	    'PARAMETER_1_RANGE',  'PARAMETER_1_VALUE',  'PARAMETER_1_VALUE_PERCENT'])

        value_set1['PARAMETER_1_RANGE'] = pd.Series(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        value_set1['PARAMETER_1_VALUE'] = pd.Series(SSrange1)
        value_set1['PARAMETER_1_NAME'] = scenario_variables_temp[0]
        value_set1['PARAMETER_1_VALUE_PERCENT'] = pd.Series(Srange1)
        
        value_set2 = pd.DataFrame(columns = ['PARAMETER_2_NAME',	    'PARAMETER_2_RANGE',  'PARAMETER_2_VALUE',  'PARAMETER_2_VALUE_PERCENT'])       
        value_set2['PARAMETER_2_RANGE'] = pd.Series(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        value_set2['PARAMETER_2_VALUE'] = pd.Series(SSrange2)
        value_set2['PARAMETER_2_NAME'] = scenario_variables_temp[1]
        value_set2['PARAMETER_2_VALUE_PERCENT'] = pd.Series(Srange2)

        value_set3 = pd.DataFrame(columns = ['PARAMETER_3_NAME',	    'PARAMETER_3_RANGE',  'PARAMETER_3_VALUE',  'PARAMETER_3_VALUE_PERCENT'])       
        value_set3['PARAMETER_3_RANGE'] = pd.Series(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        value_set3['PARAMETER_3_VALUE'] = pd.Series(SSrange3)
        value_set3['PARAMETER_3_NAME'] = scenario_variables_temp[2]
        value_set3['PARAMETER_3_VALUE_PERCENT'] = pd.Series(Srange3)

        value_set3 = pd.DataFrame(columns = ['PARAMETER_3_NAME',	    'PARAMETER_3_RANGE',  'PARAMETER_3_VALUE',  'PARAMETER_3_VALUE_PERCENT'])       
        value_set3['PARAMETER_3_RANGE'] = pd.Series(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        value_set3['PARAMETER_3_VALUE'] = pd.Series(SSrange3)
        value_set3['PARAMETER_3_NAME'] = scenario_variables_temp[2]
        value_set3['PARAMETER_3_VALUE_PERCENT'] = pd.Series(Srange3)

        value_set4 = pd.DataFrame(columns = ['PARAMETER_4_NAME',	    'PARAMETER_4_RANGE',  'PARAMETER_4_VALUE',  'PARAMETER_4_VALUE_PERCENT'])       
        value_set4['PARAMETER_4_RANGE'] = pd.Series(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        value_set4['PARAMETER_4_VALUE'] = pd.Series(SSrange4)
        value_set4['PARAMETER_4_NAME'] = scenario_variables_temp[3]
        value_set4['PARAMETER_4_VALUE_PERCENT'] = pd.Series(Srange4)    

        value_set5 = pd.DataFrame(columns = ['PARAMETER_5_NAME',	    'PARAMETER_5_RANGE',  'PARAMETER_5_VALUE',  'PARAMETER_5_VALUE_PERCENT'])       
        value_set5['PARAMETER_5_RANGE'] = pd.Series(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        value_set5['PARAMETER_5_VALUE'] = pd.Series(SSrange5)
        value_set5['PARAMETER_5_NAME'] = scenario_variables_temp[4]
        value_set5['PARAMETER_5_VALUE_PERCENT'] = pd.Series(Srange5)    

        value_set6 = pd.DataFrame(columns = ['PARAMETER_6_NAME',	    'PARAMETER_6_RANGE',  'PARAMETER_6_VALUE',  'PARAMETER_6_VALUE_PERCENT'])       
        value_set6['PARAMETER_6_RANGE'] = pd.Series(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        value_set6['PARAMETER_6_VALUE'] = pd.Series(SSrange6)
        value_set6['PARAMETER_6_NAME'] = scenario_variables_temp[5]
        value_set6['PARAMETER_6_VALUE_PERCENT'] = pd.Series(Srange6)    

        value_set7 = pd.DataFrame(columns = ['PARAMETER_7_NAME',	    'PARAMETER_7_RANGE',  'PARAMETER_7_VALUE',  'PARAMETER_7_VALUE_PERCENT'])       
        value_set7['PARAMETER_7_RANGE'] = pd.Series(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        value_set7['PARAMETER_7_VALUE'] = pd.Series(SSrange7)
        value_set7['PARAMETER_7_NAME'] = scenario_variables_temp[6]
        value_set7['PARAMETER_7_VALUE_PERCENT'] = pd.Series(Srange7)    


        value_set1['key'] = 0
        value_set2['key'] = 0
        value_set3['key'] = 0
        value_set4["key"] = 0
        value_set5['key'] = 0
        value_set6["key"] = 0
        value_set7["key"] = 0

        value_set1 = value_set1.merge(value_set2, how='outer')
        param_table = value_set1.merge(value_set3, how='outer')
        param_table = param_table.merge(value_set4, how='outer')
        param_table = param_table.merge(value_set5, how='outer')
        param_table = param_table.merge(value_set6, how='outer')
        param_table = param_table.merge(value_set7, how='outer')


        param_table['PARAMETER_COMBO_ID'] = ['N'+format(x, '04d') for x in range(1,len(param_table)+1)]
        non_scenarios = param_table[(param_table['PARAMETER_1_RANGE'] == 'Medium') & (param_table['PARAMETER_2_RANGE'] == 'Medium') 
                                    & (param_table['PARAMETER_3_RANGE'] == 'Medium') & (param_table['PARAMETER_4_RANGE'] == 'Medium')
                                    & (param_table['PARAMETER_5_RANGE'] == 'Medium') & (param_table['PARAMETER_6_RANGE'] == 'Medium')
                                    & (param_table['PARAMETER_7_RANGE'] == 'Medium')].index
        param_table.loc[non_scenarios,'PARAMETER_COMBO_ID'] = 'N0000'
        cols = param_table.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        param_table = param_table[cols]
        param_table['INSERT_DT'] = datetime.datetime.today().strftime('%Y%m%d')
        obj_cols = [i for i in param_table.columns if is_object_dtype(param_table[i].dtype)]
        for col in obj_cols:
            param_table[col] = param_table[col].astype('string')
        dtyps = get_col_format(param_table)
        splidfs = np.array_split(param_table, 100)
        for dfsplit in splidfs:
            dfsplit.to_sql(f"DS_WHAT_IF_PARAMS".lower(),if_exists="replace",con=engine,dtype=dtyps,index=False)
        return param_table
    else:
        param_table = pd.read_sql("select * from DS_WHAT_IF_PARAMS",con=engine)
        param_table.columns = [i.upper() for i in param_table.columns]
        return param_table

