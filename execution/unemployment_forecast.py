# -*- coding: utf-8 -*-
"""
Main execution script for the unemployment forecast model.
"""

import argparse
import os
import warnings


import pandas as pd

from config.parameters import (FORECAST_TYPE, PREDICTIONS_DIR,
                                 get_default_parameters)
from utils.db_connection import get_db_config

if FORECAST_TYPE == '2Q':
    from data.q2.collection import (load_indicators_data, load_target_data,
                                      load_target_reg_data)
    from models.q2.funcs.helpers import prepare_output, save_results
    from models.q2.unemployment import (forecast_accuracy_1q_func, get_model,
                                          prepare_df_model,
                                          short_term_model_accuracy_1q)
elif FORECAST_TYPE == '1Q':
    from data.q1.collection import (load_indicators_data, load_target_data,
                                      load_target_reg_data)
    from models.q1.funcs.helpers import prepare_output, save_results
    from models.q1.unemployment import (forecast_accuracy_1q_func, get_model,
                                          prepare_df_model,
                                          short_term_model_accuracy_1q)
else:
    raise Exception('Forecast type not implemented')

def run_unemployment_forecast(params=None):
    """
    Run the unemployment forecast model

    Args:
        params: Optional ModelParameters object

    Returns:
        None
    """
    # Suppress warnings
    warnings.filterwarnings("ignore")

    # Get parameters
    if params is None:
        params = get_default_parameters()

    # Get database configuration
    db_config = get_db_config()

    print('1.- Load Use Case Parameters')

    # Create predictions directory if it doesn't exist
    if not hasattr(params, 'predictions_dir'):
        params.predictions_dir = PREDICTIONS_DIR
    os.makedirs(params.predictions_dir, exist_ok=True)

    # Run forecast for each target region and citizen type
    for target_reg in params.target_regs:
        for citizen_id in params.citizen_ids:
            # Set region name for display
            if target_reg == "TOTAL_UNEM":
                use_case_region = "Emirate of Abu Dhabi"
            else:
                use_case_region = target_reg

            print(f'1.1 Use Case - Unemployment Rate Forecast for {use_case_region} - {citizen_id}')

            # Set input target data table based on region and citizen type
            if target_reg == 'TOTAL_UNEM':
                input_target_data = 'VW_DS_UNEMP_TEST'
            else:
                if citizen_id == 'Citizen':
                    input_target_data = 'VW_DS_UNEMP_CITIZEN_TEST'
                else:
                    input_target_data = 'VW_DS_UNEMP_NON_CIT_TEST'

            # Load data
            print('2. Loading data')
            print('_____2.1.- Load Target data')

            if target_reg == 'TOTAL_UNEM':
                df_unem_q_filt_int = load_target_data(input_target_data, params.forecast_start, citizen_id, target_reg)
                if params.model_debug:
                    print("DF for df_unem_q_filt_int:")
                    print(df_unem_q_filt_int)
            else:
                df_unem_q_filt_int = load_target_reg_data(input_target_data, citizen_id, target_reg)
                if params.model_debug:
                    print("DF for df_unem_q_filt_int:")
                    print(df_unem_q_filt_int)

            # Load indicators data
            print('_____2.2.- Load Variables data')
            df_indicators = load_indicators_data(
                params.indicator_id,
                params.predictions_dir,
                db_config.userSE_ECON,
                db_config.userLD_ECON,
                db_config.user_MISC,
                target_reg,
                params.deflators_calc
            )

            if params.model_debug:
                print("DF for df_indicators:")
                print(df_indicators)

            # Merge target and indicators data
            print('_____2.3.- Merge Target and Variables data')
            df0 = pd.merge(df_indicators, df_unem_q_filt_int[target_reg], left_index=True, right_index=True, how='outer')

            if params.model_debug:
                print("DF for df0:")
                print(df0)

            # Get model
            print(f'3.- Collect latest Unemployment Model for {citizen_id} @ {target_reg}')
            model_id = f'Unem_rate_{target_reg}_{citizen_id}'
            inds, df_clu = get_model(model_id, params.indicator_id, citizen_id, target_reg)

            if params.model_debug:
                print("DF for df_clu:")
                print(df_clu)

            # Prepare data for model
            print('4.- Prepare Data to build and execute forecast Model')
            analytical_df_var2, df_all_pred, quarters = prepare_df_model(target_reg, inds, df0, df_clu)

            if params.model_debug:
                print("DF for analytical_df_var2:")
                print(analytical_df_var2)

            # Execute forecast model
            print('5.- Build and Execute Forecast Model')
            print(f"Scenario Flag: {params.scenario_flag}")

            if not params.scenario_flag:
                # Calculate model accuracy
                r2_value, lasso_mse, y_pred, nans_projected, n_points, r2_cv, r2_cv_std, y_fore, df_pred, model, Acc_l1, Acc_l2, delta_inacc, training_set = short_term_model_accuracy_1q(
                params.indicator_id,
                analytical_df_var2,
                target=target_reg,
                forecast_start=params.forecast_start,
                forecast_end=params.forecast_end,citizen_ = citizen_id)
            else:
                    #coeff_df, 
                    r2_value, lasso_mse, y_pred, nans_projected, n_points, r2_cv, r2_cv_std, y_fore, df_pred, model, Acc_l1, Acc_l2, delta_inacc, training_set = short_term_model_accuracy_1q(
                    params.indicator_id,
                    analytical_df_var2,
                    target=target_reg,
                    forecast_start=params.forecast_start,
                    forecast_end=params.forecast_end_2q) 
            
            if params.model_debug:
                print("DF for df_pred :")
                print(df_pred)

            # Calculate inaccuracies
            print('____5.1- Calculate Model Inaccuracy')
            forecast_accuracy_1q, forecast_accuracy_1q_std = forecast_accuracy_1q_func(quarters, analytical_df_var2, params.indicator_id, target_reg)
            print('r2 %.2f fore acc %.4f  +/- %.4f' % (r2_value, forecast_accuracy_1q, forecast_accuracy_1q_std))
            if params.model_debug:
                print("DF for df_pred :")
                print(forecast_accuracy_1q)

            print('6.- Prepare Output Data to be consumed by FE')
        # Model and Real unemployment results store in df_all_pred variable
        df_all_pred = pd.merge(df_all_pred, df_pred, left_index=True, right_index=True, how='left')
        df_all_pred.dropna(how='all', inplace=True)
        if params.model_debug:
            print("DF for df_pred :")
            print(df_all_pred)
        # Prepare output results
        print('____6.1- Populate Output dataframe with Model\'s Results')
        if params.scenario_flag:
            df_out = prepare_output(df_all_pred, df_clu, citizen_id, target_reg, forecast_accuracy_1q,params.forecast_end_2q)
        else:
            df_out = prepare_output(df_all_pred, df_clu, citizen_id, target_reg, forecast_accuracy_1q, params.forecast_end)
        if params.model_debug:
            print("DF for df_out :")
            print(df_out)

        print(df_out)      
        # Save results to DS_UNEM_RATE_FORECAST Table in Staging Labour Force
        print('____6.2.- Save results on DB')
        save_results(df_out, params.save_excel, params.save_oracle, citizen_id, target_reg, params.predictions_dir)
    print('Unemployment forecast completed successfully')


def main():
    """
    Main function for command-line execution
    """
    parser = argparse.ArgumentParser(description='Run unemployment forecast model')
    parser.add_argument('--forecast_start', type=str, help='Forecast start date (YYYY-MM-DD)')
    parser.add_argument('--forecast_end', type=str, help='Forecast end date (YYYY-MM-DD)')
    parser.add_argument('--num_quarter', type=int, help='Number of quarters to forecast')
    parser.add_argument('--forecast_horizon', type=int, help='Forecast horizon in quarters')
    parser.add_argument('--citizen_ids', type=str, nargs='+', help='Citizen IDs to model')
    parser.add_argument('--target_regs', type=str, nargs='+', help='Target regions to model')
    parser.add_argument('--indicator_id', type=str, help='Indicator ID')
    parser.add_argument('--save_excel', action='store_true', help='Save results to Excel')
    parser.add_argument('--save_oracle', action='store_true', help='Save results to Oracle')
    parser.add_argument('--save_model', action='store_true', help='Save model')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--scenario', action='store_true', help='Enable scenario-based forecasting')
    parser.add_argument('--insert_user', type=str, help='User for insertions')
    parser.add_argument('--min_indicators', type=int, help='Minimum number of indicators for combination study')
    parser.add_argument('--r2_threshold', type=float, help='R2 threshold for model evaluation')

    args = parser.parse_args()

    # Get default parameters
    params = get_default_parameters()

    # Override with command-line arguments if provided
    if args.forecast_start:
        params.forecast_start = args.forecast_start

    if args.forecast_end:
        params.forecast_end = args.forecast_end

    if args.num_quarter:
        params.num_quarter = args.num_quarter

    if args.forecast_horizon:
        params.forecast_horizon = args.forecast_horizon

    if args.citizen_ids:
        params.citizen_ids = args.citizen_ids

    if args.target_regs:
        params.target_regs = args.target_regs

    if args.indicator_id:
        params.indicator_id = args.indicator_id

    if args.save_excel:
        params.save_excel = True

    if args.save_oracle:
        params.save_oracle = True

    if args.save_model:
        params.save_model = True

    if args.debug:
        params.model_debug = True

    if args.scenario:
        params.scenario_flag = True

    if args.insert_user:
        params.insert_user = args.insert_user

    if args.min_indicators:
        params.min_indicators = args.min_indicators

    if args.r2_threshold:
        params.r2_threshold = args.r2_threshold

    # Run the forecast
    run_unemployment_forecast(params)


if __name__ == "__main__":
    main()
