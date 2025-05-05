import datetime

import pandas as pd
from sqlalchemy import types

from ....config.parameters import get_default_parameters
from ....utils.db_connection import database_engine_user, get_db_config

#Migrated
def save_results(df_out, save_excel, save_oracle, citizen_id, target_reg, cdir):
    params = get_default_parameters()
    db_config = get_db_config()
    fout = 'unemployment_'+citizen_id+'_'+target_reg+'.xlsx'
    if save_excel:
        fout_name = cdir + '\\'+ fout
        df_out['run_dt'] = datetime.datetime.now()
        df_out.to_excel(fout_name)
        print(f"Final Model for %s %s have been saved to excel file %s" % (citizen_id, target_reg, fout_name))
    if save_oracle:
        if params.scenario_flag:
            dtyp = {c: types.VARCHAR(200)
                for c in df_out.columns[df_out.dtypes == 'object'].tolist()}
            dtyp_float = {c: types.NUMERIC(10, 5)
                for c in df_out.columns[df_out.dtypes == 'float64'].tolist()}
            dtyp_all = {**dtyp, **dtyp_float}
            engine = database_engine_user(db_config.userS_JobVac)
            try:
                run_df = pd.read_sql(f"select max(run_seq_id) as MAX_ID from DS_UNEM_RATE_FORECAST_WHT_IF",con=engine)
                max_id = int(run_df["max_id"].values[0]) + 1
            except Exception as e:
                max_id = 1 
            df_out['run_seq_id'] = max_id
            df_out['run_dt'] = datetime.datetime.now()
            df_out.to_sql('DS_UNEM_RATE_FORECAST_WHT_IF'.lower(), con=engine, if_exists='append',
                                    index=False,
                                    dtype=dtyp_all)
            run_seq_id_val = df_out.run_seq_id.values[0]
            print(f"Final Model for %s %s have been saved to 'DS_UNEM_RATE_FORECAST_WHT_IF' in the Staging LF layer with RUN_SEQ_ID =%i" % (citizen_id, target_reg, max_id))
        else:
            dtyp = {c: types.VARCHAR(200)
                for c in df_out.columns[df_out.dtypes == 'object'].tolist()}
            dtyp_float = {c: types.NUMERIC(10, 5)
                for c in df_out.columns[df_out.dtypes == 'float64'].tolist()}
            dtyp_all = {**dtyp, **dtyp_float}
            engine = database_engine_user(db_config.userS_JobVac)
            try:
                run_df = pd.read_sql(f"select max(run_seq_id) as MAX_ID from DS_UNEM_RATE_FORECAST",con=engine)
                max_id = int(run_df["max_id"].values[0]) + 1
            except Exception as e:
                max_id = 1 
            df_out['run_seq_id'] = max_id
            df_out['run_dt'] = datetime.datetime.now()
            df_out.to_sql('DS_UNEM_RATE_FORECAST'.lower(), con=engine, if_exists='append',
                                    index=False,
                                    dtype=dtyp_all)
            run_seq_id_val = df_out.run_seq_id.values[0]
            print(f"Final Model for %s %s have been saved to 'DS_UNEM_RATE_FORECAST' in the Staging LF layer with RUN_SEQ_ID =%i" % (citizen_id, target_reg, max_id))
    if not save_excel and not save_oracle:
        print("Results not saved")
    return

#Migrated
def prepare_output(df_all_pred, df_clu, citizen_id, target_reg, forecast_accuracy_1q, forecast_end):
    """
    Prepare output DataFrame with model results
    
    Args:
        df_all_pred: Predictions DataFrame
        df_clu: Model DataFrame
        citizen_id: Citizen ID
        target_reg: Target region
        forecast_accuracy_1q: Forecast accuracy
        forecast_end: Forecast end date
        
    Returns:
        Output DataFrame
    """
    db_config = get_db_config()
    params = get_default_parameters()
    today_time = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S")
    engine = database_engine_user(db_config.userS_JobVac)
    
    df_unem_forecast = pd.read_sql('SELECT * FROM DS_UNEM_RATE_FORECAST', con=engine)
    max_run_seq_id = df_unem_forecast[(df_unem_forecast.oil_nonoil==citizen_id)  & (df_unem_forecast.sector == target_reg) ]['run_seq_id'].max()
    tab_columns = pd.read_sql('SELECT * FROM DS_UNEM_RATE_FORECAST where 1=0', con=engine)
    # real observations table
    df_out_real = pd.DataFrame(columns=tab_columns)
    df_out_real['value'] = df_all_pred[target_reg].values
    df_out_real['obs_dt'] = df_all_pred.index
    df_out_real.loc[:,'parameter_combo_id'] = 'E0000'
    df_out_real.loc[:,'run_seq_id'] = int(max_run_seq_id)+1
    df_out_real.loc[:,'run_dt'] = df_clu.insert_dt.unique()[0]
    df_out_real.loc[:,'type'] = 'REAL UNEMPLOYMENT'
    df_out_real.loc[:,'opt'] = 0
    df_out_real.loc[:,'unit'] =  '%'
    df_out_real.loc[:,'sector'] = target_reg
    df_out_real.loc[:,'oil_nonoil'] = citizen_id
    df_out_real.loc[:,'insert_dt'] = today_time
    
    # prediction table
    df_out_pred = pd.DataFrame(columns=tab_columns)
    df_out_pred['obs_dt'] = df_all_pred.index
    df_out_pred['value'] = df_all_pred[target_reg+'_pred'].values
    df_out_pred.loc[:,'parameter_combo_id'] = 'E0000'
    df_out_pred.loc[:,'run_seq_id'] = int(max_run_seq_id)+1
    df_out_pred.loc[:,'run_dt'] = df_clu.insert_dt.unique()[0]
    df_out_pred.loc[:,'type'] = 'MODEL UNEMPLOYMENT'
    df_out_pred.loc[:,'opt'] = 0
    df_out_pred.loc[:,'unit'] =  '%'
    df_out_pred.loc[:,'sector'] = target_reg
    df_out_pred.loc[:,'oil_nonoil'] = citizen_id
    df_out_pred.loc[:,'insert_dt'] = today_time
    
    # edit forecast rows
    ind = df_out_pred[df_out_pred.obs_dt.isin([forecast_end])].index
    df_out_pred.loc[ind, 'opt']=1
    df_out_pred.loc[ind, 'type']='FORECAST UNEMPLOYMENT'
    tmp = df_all_pred.reset_index()
    df_out_pred.loc[ind,'parameter_combo_id'] = tmp[tmp.OBS_DT.isin([forecast_end])]["COMBO"]
    #disabling confidence interval as it is not accuracte.
    # df_out_pred.loc[ind, 'value_ll'] = df_out_pred.loc[ind, 'value']*(1-forecast_accuracy_1q*2.98)
    # df_out_pred.loc[ind, 'value_ul'] = df_out_pred.loc[ind, 'value']*(1+forecast_accuracy_1q*2.98) # 2.98 assuming normal distribution CI assures 99.8% of chances to capture real value
    df_out_pred.loc[ind, 'value_ll'] = df_out_pred.loc[ind, 'value']*(1-forecast_accuracy_1q*1.96)
    df_out_pred.loc[ind, 'value_ul'] = df_out_pred.loc[ind, 'value']*(1+forecast_accuracy_1q*1.96) 
    df_out = pd.concat([df_out_real, df_out_pred])
    
    
    # assign same value to last obs_dt of real observation tovisualiza CI @ FE
    df_out = df_out.reset_index(drop=True)
    ind = df_out_real[(df_out_real.type == 'REAL UNEMPLOYMENT') &
                      (df_out_real.obs_dt == df_all_pred.index[-2]) ].index
    
    ind_value = df_out.loc[ind]['value']
    df_out.loc[ind,'value_ll'] = ind_value
    df_out.loc[ind,'value_ul'] = ind_value
    return df_out