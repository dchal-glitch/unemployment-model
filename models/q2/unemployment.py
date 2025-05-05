# -*- coding: utf-8 -*-
"""
Unemployment model functions.
"""

import datetime
import os

import matplotlib
import numpy as np
import pandas as pd
from flaml import AutoML
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from ...config.parameters import get_default_parameters
from ...utils.data_funcs import save_to_sql
from ..scenario_functions import (get_data_for_what_if,
                                       scenarios_table_creator)

matplotlib.use('Agg')

import os
from datetime import datetime

import matplotlib.pyplot as plt
from flaml import AutoML
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from ...utils.db_connection import database_engine_user, get_db_config

# from darts.models import NHiTSModel
# from darts.models import NBEATSModel





# from autots import AutoTS

# from darts.datapreprocessing.transformer import Scaler
# from darts.utils.timeseries_generation import datetime_attribute_timeseries

# import mlflow

# mlflow.set_tracking_uri('http://10.40.107.137:8501')


#Migrated
def get_model(model_id, indicator_id, target, target_reg):
    """
    Get model from database
    
    Args:
        model_id: Model ID
        indicator_id: Indicator ID
        target: Target citizen type
        target_reg: Target region
        
    Returns:
        Tuple of (indicators list, model DataFrame)
    """
    db_config = get_db_config()
    engine = database_engine_user(db_config.user_MISC)
    query_sql = f"select * from IFP_DS_INPUT_INDICATORS_V2 where model_id = '%s' and INDICATOR_ID!='EHPIAE Index'" % (model_id)
    
    df_models = pd.read_sql(query_sql,  con=engine)
    df_clu_cons = df_models[df_models.insert_dt==max(df_models.insert_dt.unique())]
    df_clu_cons.rename(columns={'indicator_id':'Indicator',
                                'ds_indicator_lag_m':'lag_pos'}, inplace=True)
    if indicator_id == 'COI_REALGDP_CNST':
        inds = df_clu_cons['Indicator'].tolist()
        df_clu = df_clu_cons    
    inds.append(target_reg)
    return inds, df_clu

#Migrated
def prepare_df_model(target, inds, df0, df_clu):
    """
    Prepare data for model execution
    
    Args:
        target: Target region
        inds: List of indicators
        df0: Input DataFrame
        df_clu: Model DataFrame
        
    Returns:
        Tuple of (analytical DataFrame, predictions DataFrame, quarters)
    """
    last_quarter = df0[target].dropna().index[-1]
    # Get SCAD data
    forecast_start = str(last_quarter).split()[0]
    forecast_end = str(last_quarter + pd.DateOffset(months=6)).split()[0]
    analytical_df_var_sel = df0[inds].copy()

    
    if any(analytical_df_var_sel.index > forecast_end):
        # remove indices
        analytical_df_var_sel.drop(analytical_df_var_sel.loc[analytical_df_var_sel.index > forecast_end].index,
                                   inplace=True)
    elif all(analytical_df_var_sel.index < forecast_end):
        # add indices
        idx = pd.date_range(analytical_df_var_sel.index[-1] + pd.DateOffset(months=1), forecast_end, freq='MS')
        df_temp = pd.DataFrame(index=idx, columns=analytical_df_var_sel.columns)
        analytical_df_var_sel = pd.concat([analytical_df_var_sel, df_temp])
    max_id = analytical_df_var_sel.index.max() + pd.DateOffset(months=6)
    new_id = pd.date_range(start=analytical_df_var_sel.index.min(), end=max_id, freq='Q')
    time_df = pd.DataFrame()
    time_df.index = new_id
    time_df.index = time_df.index + pd.offsets.QuarterEnd()
    analytical_df_var_sel = time_df.merge(analytical_df_var_sel,left_index=True,right_index=True,how='left')
    print(analytical_df_var_sel)
    # shift indicators
    for ind in inds[0:-1]:
        lag = df_clu[df_clu['Indicator'] == ind]['lag_pos'].values[0]
        analytical_df_var_sel[ind] = analytical_df_var_sel[ind].shift(int(lag))
        print('Shifting ', ind, ' by ', lag, ' quarters')
    
    # Filter indicators data to target data interval
    ind = analytical_df_var_sel[analytical_df_var_sel.index>=df0[target].dropna().index[0]].index
    analytical_df_var_sel = analytical_df_var_sel.loc[ind]
    
    df_unem_q = (analytical_df_var_sel[target].dropna().groupby(
            pd.PeriodIndex(analytical_df_var_sel[target].dropna().index, freq='Q'))
                    .sum()).to_frame()
    last_q = str(df_unem_q.index[-1])
    quarters = df_unem_q[(df_unem_q.index > '2020Q1') & (df_unem_q.index <= last_q)].index
    # df Predictions
    df_all_pred = df0[target].to_frame()
 
    #var_sel = list(df_clu['Indicator'].to_list())
    #analytical_df_var2 = analytical_df_var_sel[var_sel].copy()

    return analytical_df_var_sel, df_all_pred, quarters


def short_term_model_accuracy_1q(indicator_id, analytical_for_test, target, forecast_start, forecast_end,citizen_):
    """
    Calculate short-term model accuracy for 1 quarter ahead
    
    Args:
        analytical_df_var_sel: Analytical DataFrame
        target_reg: Target region
        df_clu: Model DataFrame
        quarters: Quarters for analysis
        
    Returns:
        Tuple of (forecast accuracy, model)
    """
    # fill forward the latest known data point to cope for not up-to-date indicators
    params = get_default_parameters()
    db_config = get_db_config()
    analytical_for_test = analytical_for_test.fillna(method='ffill')
    analytical_for_merge = analytical_for_test.copy()

    # Test Codes - Start
    # List of elements to be excluded
    # exclude_elements = [
    #     "M1_Bloom", "IAC1 COMB Comdty", "PX_VOLUME_Copper", 
    #     "PX_LAST_MSCI Air Freight", "OPCRUAE Index", 
    #     "PX_PROD_Steel", "UEMSM1Y Index"
    # ]

    # # Sample list of columns
    # cols = analytical_for_test.columns

    # # Exclude elements from cols
    # filtered_cols = [col for col in cols if col not in exclude_elements]
    # analytical_for_test = analytical_for_test[filtered_cols]
     # Test Codes - End    

    training_set = analytical_for_test[analytical_for_test.index <= forecast_start]
    # training_set.fillna(method='ffill') # for TS test
    # training_set.fillna(method='bfill') # for TS test
    training_set.dropna(inplace=True)
    X_data = training_set[training_set.columns[0:-1]]
    y_data = training_set[target].values.ravel()
    testing_features = analytical_for_test.loc[
        (analytical_for_test.index > forecast_start) & (analytical_for_test.index <= forecast_end)]
    actual = testing_features[target]
    testing_features = testing_features.drop(columns=target)

    #test
    # from statsmodels.tsa.stattools import grangercausalitytests
    # def grangers_causation_matrix(data, variables, test='ssr_chi2test', verbose=False):    
    #     """Check Granger Causality of all possible combinations of the Time series.
    #     The rows are the response variable, columns are predictors. The values in the table 
    #     are the P-Values. P-Values lesser than the significance level (0.05), implies 
    #     the Null Hypothesis that the coefficients of the corresponding past values is 
    #     zero, that is, the X does not cause Y can be rejected.

    #     data      : pandas dataframe containing the time series variables
    #     variables : list containing names of the time series variables.
    #     """
    #     df = pd.DataFrame(np.zeros((len(variables), len(variables))), columns=variables, index=variables)
    #     for c in df.columns:
    #         for r in df.index:
    #             test_result = grangercausalitytests(data[[r, c]], maxlag=4, verbose=False)
    #             p_values = [round(test_result[i+1][0][test][1],4) for i in range(4)]
    #             if verbose: print(f'Y = {r}, X = {c}, P Values = {p_values}')
    #             min_p_value = np.min(p_values)
    #             df.loc[r, c] = min_p_value
    #     df.columns = [var + '_x' for var in variables]
    #     df.index = [var + '_y' for var in variables]
    #     return df
    # grangers_causation_matrix(training_set,training_set.columns)
    # breakpoint()

    #test

    print('-----------analytical_for_test-----------')
    print(analytical_for_test)

    ######## Model Input ########
    input_data_export = analytical_for_test
    cdir = os.path.dirname(os.path.abspath("__file__"))
    wdir = cdir + '\\Model_Inputs\\'

    if not os.path.isdir(wdir):
        os.mkdir(wdir)
    input_data_export.to_excel(wdir+f"Model_Input_of_{indicator_id}_{target}_1Q.xlsx")

    ######################################
    validation_start = '2017-01-01'
    r2 = []
    lasso_global_error = []

    # validation purpose
    for k in range(40):
        X_train, X_test, y_train, y_test = train_test_split(X_data, y_data, test_size=0.2, random_state=k)
        model = Lasso(alpha=0.005)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        validation_target = training_set.loc[(training_set.index >= validation_start), target]
        validation_features = training_set.loc[(training_set.index >= validation_start), training_set.columns[0:-1]]
        validation_pred = model.predict(validation_features)
        r2_value = r2_score(validation_target, validation_pred)
        r2.append(r2_value)
        lasso_mse = mean_squared_error(validation_target, validation_pred)
        lasso_global_error.append(np.sqrt(lasso_mse) / (y_train.shape[0] - 1))
    model = AutoML()
    model.fit(X_train, y_train,task='regression',estimator_list = ['rf', 'xgboost', 'extra_tree', 'xgb_limitdepth'],time_budget=60)
    # model.fit(X_train, y_train,task='regression',estimator_list = ['rf', 'extra_tree'],time_budget=5)
    # model = Lasso(alpha=0.005)
    # model.fit(X_train, y_train)
    validation_pred = model.predict(validation_features)
    r2_value = r2_score(validation_target, validation_pred)
    r2_cv = np.mean(r2)
    r2_cv_std = np.std(r2)


    print("----- ROLLING AUTOML REGRESSION---------------")

    forecast_length,pred_list = 2 , []
    
    columns_to_shift = X_data.columns
    training_set_lag = training_set.copy()

    X_data = training_set_lag[training_set_lag.columns[0:-1]]

    testing_features_1 = training_set_lag[-forecast_length:]
    testing_features_1 = testing_features_1.drop(columns=target)
    for col in columns_to_shift:
        training_set_lag[col] = training_set_lag[col].shift(forecast_length)
    training_set_lag.dropna(inplace = True)

    model = AutoML()

    for i in range((testing_features_1.shape[0])):
        x_train = training_set_lag[training_set_lag.columns[0:-1]]
        y_train = training_set_lag[target].values.ravel()

        # model = AutoML()
        model.fit(x_train, y_train,task='regression',
                    estimator_list = ['rf', 'xgboost', 'extra_tree', 'xgb_limitdepth'],time_budget=20)
        # model.fit(x_train, y_train,task='regression',estimator_list = ['rf', 'extra_tree'],time_budget=5)

        first_row = testing_features_1.iloc[0].values.reshape(1,-1) 

        pred = model.predict(first_row)[0]
        pred_list.append(pred)

        first_row  = first_row.tolist()[0]  
        first_row.append(pred)
        # print(len(first_row),training_set_lag.shape[1])
        
        training_set_lag.loc[len(training_set_lag)] = first_row
        # print("===================best model inside===============",model.best_estimator)
    print("===================best model===============",model.best_estimator)
    print("=================== Actual ================================\n",actual)

    print('===================Rolling AutoML Predictions===============================\n',pred_list)
    coee_table = "DS_MODEL_COEFFICENTS"
    conn = database_engine_user(db_config.user_MISC)
    try:
        run_df = pd.read_sql(f"select max(run_seq_id) as MAX_ID from {coee_table} where model = '{target+citizen_}' ",con=conn)
        max_id = int(run_df["max_id"].values[0]) + 1
    except:
        max_id = 1
    #model_coefficents = pd.DataFrame({'Coefficient': model.coef_, 'Intercept': model.intercept_},index=training_set.columns[0:-1])
    # model_coefficents["RUN_SEQ_ID"] = max_id
    # model_coefficents["MODEL"] = target+citizen_
    # model_coefficents["INSERT_DT"] = datetime.datetime.now()
    # model_coefficents.reset_index(inplace=True)
    # model_coefficents.rename(columns={'index':"INDICATOR_ID"},inplace=True)
    # model_coefficents.columns = [i.upper() for i in model_coefficents.columns]
    # model_coefficents['INDICATOR_ID'] = model_coefficents['INDICATOR_ID'].apply(lambda x : x.split("_lag")[0])
    # save_to_sql(model_coefficents,conn,coee_table)
    # cross/validation
    n_points = training_set.shape[0]
    # Create the prediction
    if testing_features.isna().sum().sum() > 0:
        nans_projected = 'yes'
        # Filling nan values with last non-nan on columns
        testing_features.fillna(method='ffill', inplace=True)
    else:
        nans_projected = 'no'
    print("---------------MODEL_PREDICTION--------------------")
    # y_fore = model.predict(testing_features)
    y_fore = pred_list
    forecast = pd.DataFrame(y_fore)
    forecast.columns = ['Forecasted Unemp_'+target]
    # forecast.index = pd.DataFrame(testing_features).index
    start_date = pd.to_datetime(forecast_start) + pd.DateOffset(months=3)
    forecast.index = [start_date + pd.DateOffset(months=3*i+1, day=1) - pd.DateOffset(days=1) for i in range(forecast_length)]    
    print('===================Predictions==============\n',forecast)
    original_forecast = forecast.copy()
    validation_target = training_set.loc[(training_set.index >= validation_start), target]
    # prediction of validation target
    validation_features = training_set.loc[(training_set.index >= validation_start), training_set.columns[0:-1]]

    # validation_features = validation_features.reset_index(inplace = False).sort_values(by='index')  #TS test

    validation_pred = model.predict(validation_features)
    validation_train = model.predict(X_data)
    df_target = training_set[target].to_frame()
    # print('================df_target===========',df_target)
    # print('================validation_train===========',validation_train)
    df_target[target + '_pred'] = validation_train

    y_pred = validation_pred[-2:]

    # Forecast Accuracy
    q1_ind = str(training_set.index[-1]).split()[0]
    reall1 = training_set.loc[q1_ind, target].sum()
    predl1 = df_target[target + '_pred'].loc[q1_ind].sum()
    Acc_l1 = (predl1 - reall1) / reall1
    q2_ind = str(training_set.index[-2]).split()[0]
    predl2 = df_target[target + '_pred'].loc[q2_ind].sum()
    reall2 = training_set.loc[q2_ind, target].sum()
    Acc_l2 = (predl2 - reall2) / reall2

    delta_model = predl1 - predl2
    delta_real = reall1 - reall2

    delta_difference = abs(delta_model - delta_real) / abs(delta_real)

    if delta_model < 0:
        signal_model = -1
    else:
        signal_model = 1

    if delta_real < 0:
        signal_real = -1
    else:
        signal_real = 1
    metric_table = "DS_MODEL_QUALITY_METRICS_V2"
    try:    
        run_df = pd.read_sql(f"select max(run_seq_id) as MAX_ID from {metric_table} where model = '{target+citizen_}'",con=conn)
        max_val = int(run_df["max_id"].values[0])
    except:
        max_val = 0
    n = len(validation_features)
    p = len(validation_features.columns)
    adj_r2 = 1- ((1-r2_value) * (n -1)/(n-p-1))
    model_metrics = pd.DataFrame()
    model_metrics["MODEL"] = [target+citizen_]
    model_metrics["MSE"] = lasso_mse
    model_metrics["R2 SCORE"] = r2_value
    model_metrics["ADJUSTED R2 SCORE"] = adj_r2
    model_metrics["ACCURACY"] = round(((Acc_l2+Acc_l1)/2)*100,2)
    model_metrics["RUN_SEQ_ID"] = max_val + 1
    model_metrics["INSERT_DT"] = datetime.datetime.now() 
    print(model_metrics)
    save_to_sql(model_metrics,conn,metric_table)
    delta_inacc = delta_difference * signal_model * signal_real
    # mlflow.end_run()
    if params.scenario_flag:
        # Added for What If Drivers
        final_drivers = get_data_for_what_if()
        tmp_cols = [i.split("_lag")[0] for i in analytical_for_test.columns] 
        final_cols = [i for i in final_drivers.columns if i not in tmp_cols]
        final_drivers = final_drivers[final_cols]
        # final_drivers.index = final_drivers.index.normalize() - pd.offsets.MonthBegin(1)
        analytical_for_test_drivers = analytical_for_test.copy()
        analytical_for_test_drivers.columns = [i.split("_lag")[0] for i in analytical_for_test_drivers.columns] 
        analytical_for_test_drivers = pd.concat([analytical_for_test_drivers,final_drivers],axis=1)
        final_cols.append(target)
        param_table = scenarios_table_creator(analytical_for_test_drivers,forecast_start)
        if analytical_for_test_drivers.isna().sum().sum() > 0:
            nans_projected = 'yes'
            analytical_for_test_drivers.fillna(method='ffill', inplace=True)
        else:
            nans_projected = 'no'
        analytical_for_test_drivers.dropna(axis = 0,inplace=True)
        testing_features = analytical_for_test_drivers.loc[
            (analytical_for_test_drivers.index > forecast_start) & (analytical_for_test_drivers.index <= params.forecast_end_2q)]
        testing_features = testing_features.drop(columns=target)
        # Training set X and Y
        training_set = analytical_for_test_drivers.loc[(
                analytical_for_test_drivers.index < forecast_start)]
        X_data = training_set.drop([target],axis=1)
        y_data = training_set[target].values.ravel() 
        model_for_driver = Lasso(alpha=0.005)      
        # Fit the model into our training features
        model_for_driver.fit(X_data, y_data)
        # pd.DataFrame(model_for_driver.coef_,index=X_data.columns).to_excel("Unemp_Citizen.xlsx")
        # param_table.columns = [cl.upper() for cl in param_table.columns]
        analytical_sce = testing_features.copy()
        tmp_cols =  analytical_sce.columns
        analytical_sce.columns = [i.split("_lag")[0] for i in tmp_cols]
        reset_df = analytical_sce.copy()
    
        # Added for What If Drivers

        for jind in param_table.PARAMETER_COMBO_ID.values:
            if jind != "N0000":
                    param_values = param_table[param_table['PARAMETER_COMBO_ID'] == jind][['PARAMETER_1_VALUE_PERCENT', 
                                                                                        #'PARAMETER_12_VALUE',
                                                                                        'PARAMETER_2_VALUE_PERCENT','PARAMETER_3_VALUE_PERCENT','PARAMETER_4_VALUE_PERCENT','PARAMETER_5_VALUE_PERCENT','PARAMETER_6_VALUE_PERCENT','PARAMETER_7_VALUE_PERCENT']].values[0]
                    testing_features = param_table[param_table['PARAMETER_COMBO_ID'] == jind][['PARAMETER_1_NAME', 
                                                                                        #'PARAMETER_12_NAME',
                                                                                        'PARAMETER_2_NAME','PARAMETER_3_NAME','PARAMETER_4_NAME','PARAMETER_5_NAME','PARAMETER_6_NAME','PARAMETER_7_NAME']].values[0]
                    
                    Trows = analytical_sce[(analytical_sce.index>=forecast_start) & 
                                        (analytical_sce.index<=params.forecast_end_2q)].index
                    # predict scenario
                    # testing_features = pd.Series([i.replace(" ","").strip() for i in testing_features])
                    analytical_sce.loc[Trows,testing_features] = (analytical_sce.loc[Trows][testing_features.tolist()]*param_values) + analytical_sce.loc[Trows][testing_features.tolist()]
                    if analytical_sce.loc[Trows,:].isna().sum().sum()>0:
                        nans_projected = 'yes'
                        analytical_sce.fillna(method='ffill', inplace=True)
                    else:
                        nans_projected = 'no'  
                    y_pred = model_for_driver.predict(analytical_sce.loc[Trows,:].values)
                    # analytical_sce.loc[Trows,testing_features] = analytical_sce.loc[Trows][testing_features.tolist()]-(analytical_sce.loc[Trows][testing_features.tolist()]*param_values)
                    analytical_sce = reset_df.copy()
                    forecast_scenarios = pd.DataFrame(y_pred)
                    forecast_scenarios.index = Trows
                    forecast_scenarios.columns = ['Forecasted Unemp_'+target]
                    forecast_scenarios["COMBO"] = jind
                    forecast= forecast.append(forecast_scenarios) 
    if params.scenario_flag:
       original_forecast["COMBO"] = "N0000"
    else:
        original_forecast["COMBO"] = "E0000"
    forecast = forecast._append(original_forecast)
    final_df = analytical_for_merge.join(pd.DataFrame(forecast))


    # Coefficients table creation
    #coefficients_df = pd.DataFrame({'Coefficient': model.coef_, 'Intercept': model.intercept_})
    # validation target
    final_df = final_df.merge(df_target, left_index=True, right_index=True, how='outer')
    # final_df = pd.concat([final_df,df_target],axis=1)
    final_df.reset_index(inplace=True)
    final_df.rename(columns={'index':'OBS_DT'},inplace=True)
    indna = final_df[final_df[target + '_pred'].isna()].index
    final_df.loc[indna, target + '_pred'] = final_df.loc[indna, 'Forecasted Unemp_'+target]
    final_df.set_index('OBS_DT',inplace=True)
    df_target = final_df[[target + '_pred',"COMBO"]]
    df_target.dropna(inplace=True)


    # Calculate metrics R2 and MSE
    lasso_mse = mean_squared_error(validation_target, validation_pred)
    r2_value = r2_score(validation_target, validation_pred)

    if r2_value > 1:
        plt.plot(training_set.index, validation_train)
        plt.scatter(training_set.index, training_set[target], s=40)



    #return coefficients_df, 
    return r2_value, lasso_mse, y_pred, nans_projected, n_points, r2_cv, r2_cv_std, y_fore, df_target, model, Acc_l1, Acc_l2, delta_inacc, training_set

#Migrated
def forecast_accuracy_1q_func(quarters, analytical_df_var2, indicator_id, target):
    accuracies = []
    for Q_forecast in quarters[-4:]:
        c = quarters.tolist().index(Q_forecast)
        Q_start = quarters[c]
        forecast_beg = Q_start.start_time
        forecast_fin = Q_forecast.end_time
        analytical_df_ext = analytical_df_var2[analytical_df_var2.index <= forecast_fin].copy()
        analytical_df_ext = analytical_df_ext.fillna(method='ffill')
        analytical_df_ext.dropna(inplace=True)
    
        Acc_l1 = short_term_model_accuracy_study(indicator_id,
                                                 analytical_for_test=analytical_df_ext,
                                                 target=target,
                                                 forecast_start=forecast_beg,
                                                 forecast_end=forecast_fin)
        accuracies.append(abs(Acc_l1))
        print('Inaccuracy of Quarter : ', str(Q_forecast), ' = ', abs(Acc_l1) * 100, '%')
        print('==============Inaccuracies==============',[i*100 for i in accuracies])

    return np.mean(np.abs(accuracies)), np.std(accuracies)

def short_term_model_accuracy_study(indicator_id, analytical_for_test, target, forecast_start, forecast_end):
    testing_features = analytical_for_test.loc[
        (analytical_for_test.index >= forecast_start) & (analytical_for_test.index <= forecast_end)]
    testing_features = testing_features.drop(columns=target)
    # Training set X and Y
    training_set = analytical_for_test.dropna()
    training_set = training_set[training_set.index < forecast_start]
    X_data = training_set[training_set.columns[0:-1]]
    y_data = training_set[target].values.ravel()
    #model = Lasso(alpha=1.0)
    model = Lasso(alpha=0.005)
    model.fit(X_data, y_data)
    # model = AutoML()
    # model.fit(X_data, y_data,task='regression',estimator_list = ['rf', 'xgboost', 'extra_tree', 'xgb_limitdepth'],time_budget=5)
    y_fore = model.predict(testing_features)
    forecast = pd.DataFrame(y_fore)
    forecast.columns = ['Forecasted Unem_'+target]
    forecast.index = pd.DataFrame(testing_features).index
    # Calculate metrics R2 and MSE
    # Forecast Accuracy
    q1_index = analytical_for_test.index[-1:]
    reall1 = analytical_for_test.loc[q1_index, target].sum()
    Acc_l1 = (forecast.loc[q1_index, 'Forecasted Unem_'+target].sum() - reall1) / reall1
    return Acc_l1