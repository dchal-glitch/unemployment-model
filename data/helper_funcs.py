
import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.constants import date_col, targets
from utils.db_connection import database_connection_user, get_db_config
from utils.time_funcs import getM

DB_CONFIG = get_db_config()

def table_filter(df_eco, df_eco_all):
    Indict = {}
    indlist = df_eco.INDICATOR_ID.unique().tolist()
    for ind in indlist:
        df_ind = df_eco[df_eco['INDICATOR_ID'] == ind]
        title = df_ind.INDICATOR_TITLE.unique()[0]
        reglist = df_ind.REGION.unique().tolist()
        if len(reglist) > 1:  # There is more than 1 region
            for reg in reglist :
                if reg==None:
                    reg=''
                df_reg = df_ind[df_ind['REGION'] == reg]
                comlist = df_reg.GROUPS_OF_COMDITIES_SERVIS.unique().tolist()
                if len(comlist) > 1:  # There is more than one Comodity service
                    for com in comlist:
                        df_val = df_reg[df_reg['GROUPS_OF_COMDITIES_SERVIS'] == com][[date_col, 'VALUE']]
                        if len(df_val[date_col]) != len(df_val[date_col].unique()):
                            df_val = df_val[[date_col, 'VALUE']].groupby(date_col).max().reset_index()
                            df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                            iname = ind + '_' + reg + '_' + com
                            ititle = title + '_' + reg + '_' + com
                            Indict.update([(iname, ititle)])
                            df_eco_all.rename(columns={'VALUE': iname}, inplace=True)
                        else:
                            df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                            iname = ind + '_' + reg + '_' + com
                            ititle = title + '_' + reg + '_' + com
                            Indict.update([(iname, ititle)])
                            df_eco_all.rename(columns={'VALUE': iname}, inplace=True)
                else:
                    df_val = df_reg[[date_col, 'VALUE']]
                    if len(df_val[date_col]) != len(df_val[date_col].unique()):
                        df_val = df_val[[date_col, 'VALUE']].groupby(date_col).max().reset_index()
                        df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                        iname = ind + '_' + reg
                        ititle = title + '_' + reg
                        Indict.update([(iname, ititle)])
                        df_eco_all.rename(columns={'VALUE': iname}, inplace=True)
                    else:
                        df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                        iname = ind + '_' + reg
                        ititle = title + '_' + reg
                        Indict.update([(iname, ititle)])
                        df_eco_all.rename(columns={'VALUE': iname}, inplace=True)

        else:
            comlist = df_ind.GROUPS_OF_COMDITIES_SERVIS.unique().tolist()
            if len(comlist) > 1:
                for com in comlist:
                    df_val = df_ind[df_ind['GROUPS_OF_COMDITIES_SERVIS'] == com][[date_col, 'VALUE']]
                    if len(df_val[date_col]) != len(df_val[date_col].unique()):
                        cols = df_ind.columns
                        for col in cols:
                            if len(df_val[col].unique()) > 1:
                                print(col)

                        df_val = df_val[[date_col, 'VALUE']].groupby(date_col).max().reset_index()
                        df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                        iname = ind + '_' + com
                        ititle = title + '_' + com
                        Indict.update([(iname, ititle)])
                        df_eco_all.rename(columns={'VALUE': iname}, inplace=True)
                    else:
                        df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                        iname = ind + '_' + com
                        ititle = title + '_' + com
                        Indict.update([(iname, ititle)])
                        df_eco_all.rename(columns={'VALUE': iname}, inplace=True)
            else:
                actlist = df_ind['ECO_ACT_2DIG'].unique().tolist()
                if len(actlist) > 1:
                    for act in actlist:
                        df_val = df_ind[df_ind['ECO_ACT_2DIG'] == act][[date_col, 'VALUE']]
                        if len(df_val[date_col]) != len(df_val[date_col].unique()):
                            df_val = df_val[[date_col, 'VALUE']].groupby(date_col).max().reset_index()
                            df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                            iname = ind + '_act' + act
                            ititle = title + '_act' + act
                            Indict.update([(iname, ititle)])
                            df_eco_all.rename(columns={'VALUE': iname}, inplace=True)
                        else:
                            df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                            if act is None:
                                act = 'none'
                            iname = ind + '_' + act
                            ititle = title + '_' + act
                            Indict.update([(iname, ititle)])
                            df_eco_all.rename(columns={'VALUE': iname}, inplace=True)
                else:
                    if len(df_ind[date_col]) != len(df_ind[date_col].unique()):
                        df_val = df_ind[[date_col, 'VALUE']].groupby(date_col).max().reset_index()
                        df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                        iname = ind
                        ititle = title
                        Indict.update([(iname, ititle)])
                        df_eco_all.rename(columns={'VALUE': iname}, inplace=True)
                    else:
                        df_val = df_ind[[date_col, 'VALUE']]
                        df_eco_all = df_eco_all.join(df_val.set_index(date_col), on=date_col)
                        iname = ind
                        ititle = title
                        Indict.update([(iname, ititle)])
                        df_eco_all.rename(columns={'VALUE': iname}, inplace=True)

    # print('df_eco_all shape', df_eco_all.shape)
    return df_eco_all, Indict

def data_collection(indicator_id, deflators_calc, target, userSE_ECON,  save_raw_analytical_df,
                    save_transformed_analytical_df, forecast_start):
    ##############################################
    ###### Connection to SCAD DB
    conn, c = database_connection_user(userSE_ECON)

    ##################################################
    # create table of content
    columns = ['TableName', 'Columns', 'Variables', 'FirstDay', 'LastDay', 'Type']
    content_table = pd.DataFrame(columns=columns)

    # Query for KOI Indicators
    print('Collecting data from KOI LIST')
    # dsn_tns = cx_Oracle.makedsn(host, port, service_name=service_name)
    # conn = cx_Oracle.connect(user=userSE_ECON, password=password, dsn=dsn_tns, encoding="UTF-8")
    query_str = "select * from DS_RI_KOI_LIST"
    var_list = pd.read_sql(query_str, con=conn)
    KOI_IDS = var_list['KOI_ID']
    kois = list(KOI_IDS.values)
    kois.append('4658')
    kois = [str(x) for x in kois]  # Almu added this because now is a list of strings not a numeric list
    strkois = (str(kois).strip('[]'))  # Almu added this because now is a list of strings not a numeric list

    ##################################################
    # Query for Economy Table set-up by Huda 28-09-2020
    #############################################
    print('Collecting data from SCAD CLEANSED OPEN DATA KOIS')
    # dsn_tns = cx_Oracle.makedsn(host, port, service_name=service_name)
    # conn = cx_Oracle.connect(user=userSE_ECON, password=password, dsn=dsn_tns, encoding="UTF-8")
    
    query_str = f"""select * from SCAD_CLNSD_OPEN_DATA_KOIS_1 where INDICATOR_ID in ({strkois})
    """
    df_eco3 = pd.read_sql(query_str, con=conn)
    print(df_eco3)
    df_eco3 = df_eco3.sort_values(by=date_col)
    #df_eco3[date_col] = df_eco3["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    df_eco3[date_col] =df_eco3['OBS_DT'].str[0:4] + '-' + df_eco3['OBS_DT'].str[4:6] + '-' + df_eco3['OBS_DT'].str[6:]
    df_eco3['VALUE'] = df_eco3['VALUE'].astype(float)
    Tmin = df_eco3.OBS_DT.min()
    Tmax = df_eco3.OBS_DT.max()
    months = getM(Tmin, Tmax)
    df_eco3_all = pd.DataFrame(columns=[date_col])
    df_eco3_all[date_col] = months

    [dfall, indlist] = table_filter(df_eco3, df_eco3_all)

    content_table = pd.DataFrame(columns=columns)

    content_table['Variables'] = pd.Series(df_eco3.INDICATOR_TITLE.unique())
    content_table['Columns'] = pd.Series(df_eco3.columns.tolist())
    FirstDay = min(df_eco3[date_col])
    content_table['FirstDay'] = FirstDay
    LastDay = max(df_eco3[date_col])
    content_table['LastDay'] = LastDay
    content_table['TableName'] = 'SCAD_CLNSD_OPEN_DATA_KOIS'

    # Dictionary contains all indicators definitions
    alldict = {**indlist}
    ipindex = df_eco3[df_eco3.INDICATOR_ID == '8719']['ECO_ACT_2DIG'].unique().tolist()
    ipidesc = df_eco3[df_eco3.INDICATOR_ID == '8719']['IPI_PPI_ACTIVITY_NAME'].unique()
    ppidesc = df_eco3[df_eco3.INDICATOR_ID == '1101']['IPI_PPI_ACTIVITY_NAME'].unique()

    for key, value in alldict.items():
        if value.startswith('IPI'):
            val = value.split('_')
            IPIindex = (val[1])
            if IPIindex in ipindex:
                ielem = ipindex.index(IPIindex)
                newval = ipidesc[ielem].replace('Manufacture Of ', '')
                alldict[key] = 'IPI ' + newval
        elif value.startswith('PPI'):
            val = value.split('_')
            IPIindex = (val[1])
            if IPIindex in ipindex:
                ielem = ipindex.index(IPIindex)
                newval = ipidesc[ielem].replace('Manufacture Of ', '')
                alldict[key] = 'PPI ' + newval
        elif value.startswith('Consumer Price Index'):
            print(value, )
            val = value.split('_')
            newval = 'CPI ' + val[1] + ' ' + val[2]
            alldict[key] = newval

    conn.close()

    # Connection to DB
    conn, c = database_connection_user(DB_CONFIG.userLD_ECON)

    #############################################
    # IND PROD INDEXES and METALS PRICE and UNEMPL
    print('Collecting data from FRED_ECONOMIC_KPIS')
    query_str = "select * from FRED_ECONOMIC_KPIS"
    df_external_tab = pd.read_sql(query_str, con=conn)

    content_table1 = pd.DataFrame(columns=columns)

    content_table1['Variables'] = pd.Series(df_external_tab.INDICATOR_NAME.unique())
    content_table1['Columns'] = pd.Series(df_external_tab.columns.tolist())
    FirstDay = min(df_external_tab[date_col])
    content_table1['FirstDay'] = FirstDay
    LastDay = max(df_external_tab[date_col])
    content_table1['LastDay'] = LastDay
    content_table1['TableName'] = 'FRED_ECONOMIC_KPIS'

    df_external_tab = df_external_tab.sort_values(by=date_col)
    # df_external_tab[date_col] = df_external_tab["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    df_external_tab[date_col] = df_external_tab['OBS_DT'].str[0:4] + '-' + df_external_tab['OBS_DT'].str[4:6] + '-' + df_external_tab['OBS_DT'].str[6:]
    Tmin = df_external_tab.OBS_DT.min()
    Tmax = pd.Timestamp.now().strftime('%Y-%m-%d')
    months = getM(Tmin, Tmax)
    df_external = pd.DataFrame(columns=[date_col])
    df_external[date_col] = months
    df_external_tab.rename(columns={'VALUE': 'Value'}, inplace=True)  # almu add this ñapa

    for col in df_external_tab.INDICATOR_NAME.unique().tolist():
        df_ind = df_external_tab[df_external_tab.INDICATOR_NAME == col][[date_col, 'Value']]
        df_external = df_external.merge(df_ind, on=date_col, how='left')
        df_external.rename(columns={'Value': 'EXT_' + col.strip()}, inplace=True)
        iname = 'EXT_' + col.strip()
        ititle = 'External data ' + col
        alldict.update([(iname, ititle)])

    #############################################
    # INFLATION
    print('Collecting data from IMF_ECONOMIC_KPIS')
    query_str = "select * from IMF_ECONOMIC_KPIS"
    df_external_tab2 = pd.read_sql(query_str, con=conn)
    df_external_tab2 = df_external_tab2.sort_values(by=date_col)
    # df_external_tab2[date_col] = df_external_tab2["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    df_external_tab2[date_col] = df_external_tab2['OBS_DT'].str[0:4] + '-' + df_external_tab2['OBS_DT'].str[4:6] + '-' + df_external_tab2['OBS_DT'].str[6:]

    ind1 = df_external_tab2.INDICATOR_NAME.unique()[0]
    df_ind = df_external_tab2[df_external_tab2.INDICATOR_NAME == ind1][[date_col, 'Value']]
    df_external = df_external.merge(df_ind, on=date_col, how='outer')
    df_external.rename(columns={'Value': 'EXT_Infl'}, inplace=True)
    iname = 'EXT_Infl'
    ititle = 'External data ' + ind1
    alldict.update([(iname, ititle)])

    ind2 = df_external_tab2.INDICATOR_NAME.unique()[1]
    df_ind = df_external_tab2[df_external_tab2.INDICATOR_NAME == ind2][[date_col, 'Value']]
    df_external = df_external.merge(df_ind, on=date_col, how='outer')
    df_external.rename(columns={'Value': 'EXT_worldGDP'}, inplace=True)
    iname = 'EXT_worldGDP'
    ititle = 'External data ' + ind2
    alldict.update([(iname, ititle)])

    content_table2 = pd.DataFrame(columns=columns)

    content_table2['Variables'] = pd.Series(df_external_tab2.INDICATOR_NAME.unique())
    content_table2['Columns'] = pd.Series(df_external_tab2.columns.tolist())
    FirstDay = min(df_external_tab2[date_col])
    content_table2['FirstDay'] = FirstDay
    LastDay = max(df_external_tab2[date_col])
    content_table2['LastDay'] = LastDay
    content_table2['TableName'] = 'IMF_ECONOMIC_KPIS'

    #############################################
    # Money supply
    print('Collecting data from CNTRL_BNK_MONEY_SUPPLY')
    query_str = "select * from CNTRL_BNK_MONEY_SUPPLY"
    df_external_tab3 = pd.read_sql(query_str, con=conn)
    df_external_tab3 = df_external_tab3.sort_values(by=date_col)
    # df_external_tab3[date_col] = df_external_tab3["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    df_external_tab3[date_col] = df_external_tab3['OBS_DT'].str[0:4] + '-' + df_external_tab3['OBS_DT'].str[4:6] + '-' + df_external_tab3['OBS_DT'].str[6:]

    content_table3 = pd.DataFrame(columns=columns)

    content_table3['Columns'] = pd.Series(df_external_tab3.columns.tolist())
    FirstDay = min(df_external_tab3[date_col])
    content_table3['FirstDay'] = FirstDay
    LastDay = max(df_external_tab3[date_col])
    content_table3['LastDay'] = LastDay
    content_table3['TableName'] = 'CNTRL_BNK_MONEY_SUPPLY'

    df_external_tab3['M1'] = df_external_tab3['M1'].astype(float)
    df_external_tab3['M2'] = df_external_tab3['M2'].astype(float)
    df_external_tab3['M3'] = df_external_tab3['M3'].astype(float)
    df_ind = df_external_tab3[[date_col, 'M1', 'M2', 'M3']]
    df_external = df_external.merge(df_ind, on=date_col, how='left')
    df_external.rename(columns={'M1': 'EXT_M1', 'M2': 'EXT_M2', 'M3': 'EXT_M3'}, inplace=True)
    iname = 'EXT_M1'
    ititle = 'External data M1'
    alldict.update([(iname, ititle)])
    iname = 'EXT_M2'
    ititle = 'External data M2'
    alldict.update([(iname, ititle)])
    iname = 'EXT_M3'
    ititle = 'External data M3'
    alldict.update([(iname, ititle)])

    #############################################
    # INVESTING BRENT DATA
    print('Collecting data from INVESTING_BRENT_DATA')
    query_str = "select * from INVESTING_BRENT_DATA"
    df_external_tab4 = pd.read_sql(query_str, con=conn)
    df_external_tab4 = df_external_tab4.sort_values(by=date_col)
    # df_external_tab4[date_col] = df_external_tab4["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    df_external_tab4[date_col] = df_external_tab4['OBS_DT'].str[0:4] + '-' + df_external_tab4['OBS_DT'].str[4:6] + '-' + df_external_tab4['OBS_DT'].str[6:]
    df_ind = df_external_tab4[[date_col, 'BRENT_FUTURE_PRICE']]
    df_external = df_external.merge(df_ind, on=date_col, how='left')
    iname = 'BRENT_FUTURE_PRICE'
    ititle = 'Brent Future Price'
    alldict.update([(iname, ititle)])

    content_table4 = pd.DataFrame(columns=columns)

    content_table4['Columns'] = df_external_tab4.columns.tolist()
    FirstDay = min(df_external_tab4[date_col])
    content_table4['FirstDay'] = FirstDay
    LastDay = max(df_external_tab4[date_col])
    content_table4['LastDay'] = LastDay
    content_table4['TableName'] = 'INVESTING_BRENT_DATA'

    #############################################
    # Brent Oil Price
    print('Collecting data from OPEC_OIL_PRICE')
    query_str = "select * from OPEC_OIL_PRICE"
    df_external_tab5 = pd.read_sql(query_str, con=conn)
    df_external_tab5 = df_external_tab5.sort_values(by=date_col)
    # df_external_tab5[date_col] = df_external_tab5["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    df_external_tab5[date_col] = df_external_tab5['OBS_DT'].str[0:4] + '-' + df_external_tab5['OBS_DT'].str[4:6] + '-' + df_external_tab5['OBS_DT'].str[6:]
    df_external_tab5['OIL_PRICE'] = df_external_tab5['OIL_PRICE'].astype(float)
    df_ind = df_external_tab5[[date_col, 'OIL_PRICE']]
    df_external = df_external.merge(df_ind, on=date_col, how='left')
    df_external.rename(columns={'OIL_PRICE': 'EXT_oil'}, inplace=True)
    iname = 'EXT_oil'
    ititle = 'External Oil Price'
    alldict.update([(iname, ititle)])

    content_table5 = pd.DataFrame(columns=columns)

    content_table5['Columns'] = df_external_tab5.columns.tolist()
    FirstDay = min(df_external_tab5[date_col])
    content_table5['FirstDay'] = FirstDay
    LastDay = max(df_external_tab5[date_col])
    content_table5['LastDay'] = LastDay
    content_table5['TableName'] = 'OPEC_OIL_PRICE'

    #############################################
    #  SCAD_GOV_INVESTMENT
    print('Collecting data from SCAD_GOV_INVESTMENT')
    query_str = "select * from SCAD_GOV_INVESTMENT"
    df_external_tab6 = pd.read_sql(query_str, con=conn)
    df_external_tab6 = df_external_tab6.sort_values(by='YEAR')
    df_external_tab6.loc[:, 'YEAR'] = df_external_tab6["YEAR"].astype(str) + '-01-01'
    df_ind = df_external_tab6[['YEAR', 'TOTAL_EXPEND']]
    df_ind['TOTAL_EXPEND'] = df_external_tab6['TOTAL_EXPEND'] - df_external_tab6['FOREIGN_EXPEND'] - df_external_tab6[
        'FEDERAL_EXPEND']
    df_ind.rename(columns={'YEAR': date_col}, inplace=True)
    df_ind.rename(columns={'TOTAL_EXPEND': 'SCENARIO_total_gov_expenditure'}, inplace=True)
    df_external = df_external.merge(df_ind, on=date_col, how='left')
    iname = 'SCENARIO_total_gov_expenditure'
    ititle = 'Scenario Total Government Expenditure'
    alldict.update([(iname, ititle)])

    content_table6 = pd.DataFrame(columns=columns)

    content_table6['Columns'] = df_external_tab6.columns.tolist()
    FirstDay = min(df_external_tab6['YEAR'])
    content_table6['FirstDay'] = FirstDay
    LastDay = max(df_external_tab6['YEAR'])
    content_table6['LastDay'] = LastDay
    content_table6['TableName'] = 'SCAD_GOV_INVESTMENT'

    #############################################
    #  Foreign Direct Investment
    print('Collecting data from SCAD_NA_FDI')
    query_str = "select * from SCAD_NA_FDI"
    df_external_tab7 = pd.read_sql(query_str, con=conn)
    df_external_tab7 = df_external_tab7.sort_values(by=date_col)
    # df_external_tab7[date_col] = df_external_tab7["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    df_external_tab7[date_col] = df_external_tab7['OBS_DT'].str[0:4] + '-' + df_external_tab7['OBS_DT'].str[4:6] + '-' + df_external_tab7['OBS_DT'].str[6:]
    df_ind = df_external_tab7[df_external_tab7.COUNTRY == 'Total'][[date_col, 'VALUE']]
    df_ind.rename(columns={'VALUE': 'SCAD_NA_FDI'}, inplace=True)
    df_external = df_external.merge(df_ind, on=date_col, how='left')
    iname = 'SCAD_NA_FDI'
    ititle = 'Scenario Foreign Direct Investment'
    alldict.update([(iname, ititle)])

    content_table7 = pd.DataFrame(columns=columns)

    content_table7['Variables'] = pd.Series(df_external_tab7.INDICATOR_TITLE.unique())
    content_table7['Columns'] = pd.Series(df_external_tab7.columns.tolist())
    FirstDay = min(df_external_tab7[date_col])
    content_table7['FirstDay'] = FirstDay
    LastDay = max(df_external_tab7[date_col])
    content_table7['LastDay'] = LastDay
    content_table7['TableName'] = 'SCAD_NA_FDI'

    # External data part: Bloomberg Data # Changed to new as old was missing some KPIs
    print('Collecting data from VW_BLOOMBERG_E_A_KPIS_REMAPPED')
        #bloomberg_data = query_sql(query='''SELECT * FROM BLOOMBERG_ECO_ANALYSIS_KPIS WHERE INDEX_NAME NOT IN ('CLA Comdty','ALDAR UH Equity','IOEA Comdty','COA Comdty2')''', c=c)
    # Updated the table with view to incorporate the alternate Bloomberg indicators for the expired indicators
    query_bloom = '''SELECT * FROM VW_BLOOMBERG_E_A_KPIS_REMAPPED WHERE INDEX_NAME NOT IN ('CLA Comdty','ALDAR UH Equity','IOEA Comdty','COA Comdty2')'''
    bloomberg_data = pd.read_sql(query_bloom, con=conn)
    Uindices = bloomberg_data[bloomberg_data.INDEX_NAME == 'U'].index
    bloomberg_data = bloomberg_data.drop(Uindices)
    Tind = bloomberg_data[bloomberg_data.OBS_DT == '20210431'].index
    bloomberg_data.loc[Tind, date_col] = '20210430'
    ind = bloomberg_data[bloomberg_data[date_col].isnull()].index
    bloomberg_data.drop(ind, inplace=True)
    Tmin = bloomberg_data.OBS_DT.min()
    Tmax = Tmax.replace('-', '')
    bloomberg_data = bloomberg_data.sort_values(by=date_col)
    # bloomberg_data[date_col] = bloomberg_data["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    bloomberg_data[date_col] = bloomberg_data['OBS_DT'].str[0:4] + '-' + bloomberg_data['OBS_DT'].str[4:6] + '-' + bloomberg_data['OBS_DT'].str[6:]
    bloomberg_data["BLG_ID"] = [i.replace("_daily","").replace("_monthly","").replace("_weekly","") for i in bloomberg_data["BLG_ID"]]
    months = getM(Tmin[:4] + '-' + Tmin[4:6] + '-01', Tmax[:4] + '-' + Tmax[4:6] + '-01')

    content_table8 = pd.DataFrame(columns=columns)

    content_table8['Variables'] = pd.Series(bloomberg_data.INDEX_NAME.unique())
    content_table8['Columns'] = pd.Series(bloomberg_data.columns.tolist())
    FirstDay = min(bloomberg_data[date_col])
    content_table8['FirstDay'] = FirstDay
    LastDay = max(bloomberg_data[date_col])
    content_table8['LastDay'] = LastDay
    content_table8['TableName'] = 'VW_BLOOMBERG_E_A_KPIS_REMAPPED'

    print('Collecting data from DS_RI_BLOOM_DICTIONARY')
    query_dim_bloom_kpi_master = 'SELECT * FROM DIM_BLOOMBERG_KPIS_MASTER'
    df_bloom_dict = pd.read_sql(query_dim_bloom_kpi_master, con=conn)

    content_table9 = pd.DataFrame(columns=columns)
    content_table9['Variables'] = pd.Series(df_bloom_dict.INDICATOR_NAME.unique())
    content_table9['Columns'] = pd.Series(df_bloom_dict.columns.tolist())
    content_table9['TableName'] = 'DIM_BLOOMBERG_KPIS_MASTER'

    irows = df_bloom_dict.DESCRIPTION.isnull()
    df_bloom_dict.loc[irows, 'DESCRIPTION'] = df_bloom_dict.loc[irows, 'INDICATOR_NAME']
    bloomberg_data[date_col] = bloomberg_data[date_col].str.lstrip()
    bloomberg_data[date_col] = bloomberg_data[date_col].str.rstrip()
    frequencies = ['monthly', 'quarterly', 'daily', 'weekly', 'yearly']

    df_bloom = pd.DataFrame(columns=[date_col])
    df_bloom[date_col] = months
    for col in bloomberg_data.INDEX_NAME.unique().tolist():
        df_ind = bloomberg_data[bloomberg_data.INDEX_NAME == col][[date_col, 'BLG_ID', 'INDEX_NAME', 'VALUE']]
        df_ind = df_ind.drop_duplicates()
        df_ind.dropna(axis=0, subset=[date_col], inplace=True)

        df_ind[date_col] = pd.to_datetime(df_ind[date_col], format='%Y-%m-%d')

        df_ind = df_ind.sort_values(by=date_col)
        df_ind = df_ind.set_index([date_col])

        if df_ind.shape[0] > 1:
            difftime = df_ind.index[-1] - df_ind.index[-2]
            if difftime.days == 1 or difftime.days == 7:
                # to monthly basis
                try:
                    df_ind = df_ind.resample('MS').apply(lambda ser: ser.iloc[-1,])
                except IndexError:
                    df_ind = df_ind.resample('MS').max()
                df_ind.reset_index(inplace=True, drop=False)
                df_ind.loc[:, date_col] = df_ind[date_col].astype(str)
            else:
                if df_ind.index[-1].day != 1:  # if it is not the first date of the month
                    df_ind.reset_index(inplace=True, drop=False)
                    df_ind[date_col] = pd.to_datetime(df_ind[date_col])
                    # df_ind.loc[:, date_col] = df_ind[date_col].apply(lambda x: x + pd.DateOffset(days=10))
                    df_ind.loc[:, date_col] = df_ind[date_col]+pd.DateOffset(days=10)
                    # df_ind.loc[:, date_col] = df_ind.loc[:, date_col].apply(lambda x: x.strftime('%Y-%m-01'))
                    df_ind.loc[:, date_col] = df_ind[date_col].dt.strftime('%Y-%m-01')
                    df_ind.loc[:, date_col] = df_ind[date_col].astype(str)

            unique_dates = df_ind.OBS_DT.unique()

            if len(df_ind.OBS_DT) != len(unique_dates):
                for date in unique_dates:
                    ind = df_ind[(df_ind.OBS_DT == date)].index
                    if len(ind) > 1:

                        # preference for 'quarterly' data
                        for frequency in frequencies:
                            inds_to_remove = df_ind.loc[ind][
                                (df_ind['BLG_ID'].str.contains(frequency) == False)].index

                            if inds_to_remove.empty:
                                df_ind_ = df_ind.loc[ind].groupby([date_col]).agg(col=(col, 'mean')).reset_index()
                                #df_ind_ = df_ind.loc[ind].groupby([date_col]).agg(col=("VALUE", 'mean')).reset_index()
                                df_ind_.columns = [date_col, col]
                                df_ind_['INDICATOR_ID'] = 'Aggregated'
                                df_ind.drop(ind, inplace=True)
                                df_ind = df_ind.append(df_ind_)
                                df_ind.sort_values(by='OBS_DT', inplace=True)

                            if len(inds_to_remove) < len(ind):
                                break

                        df_ind.drop(inds_to_remove, inplace=True)

            df_ind = df_ind.drop(['BLG_ID', 'INDEX_NAME'], axis=1).drop_duplicates()
            df_bloom['OBS_DT'] = pd.to_datetime(df_bloom['OBS_DT'])
            df_bloom = df_bloom.merge(df_ind, on=date_col, how='left')
            df_bloom.rename(columns={'VALUE': col}, inplace=True)
            iname = col
            irow = df_bloom_dict[df_bloom_dict.INDICATOR_NAME == col].index
            ititle = 'Bloomberg ' + df_bloom_dict.loc[irow, 'DESCRIPTION'].values[0]
            # print(col, ititle)
            if ititle == '':
                ititle = 'Bloomberg ' + col
            alldict.update([(iname, ititle)])

    df_bloom.rename(columns={'UEMSM0 Index': 'SCENARIO_M0_Index'}, inplace=True)
    iname = 'SCENARIO_M0_Index'
    ititle = 'Scenario Monetary Supply M0'
    alldict.update([(iname, ititle)])
    del alldict['UEMSM0 Index']

    #############################################

    # Europe Brent Oil Price
    print('Collecting data from EIA_BRENT_PRICE')
    query_str = "select * from EIA_BRENT_PRICE"
    df_external_tab8 = pd.read_sql(query_str, con=conn)
    df_external_tab8 = df_external_tab8.sort_values(by=date_col)

    content_table9 = pd.DataFrame(columns=columns)

    content_table9['Columns'] = df_external_tab8.columns.tolist()
    FirstDay = min(df_external_tab8[date_col])
    content_table9['FirstDay'] = FirstDay
    LastDay = max(df_external_tab8[date_col])
    content_table9['LastDay'] = LastDay
    content_table9['TableName'] = 'EIA_BRENT_PRICE'

    df_ind = df_external_tab8[[date_col, 'Europe Brent Spot Price FOB']]
    df_external_tab8['OBS_DT'] = pd.to_datetime(df_external_tab8['OBS_DT'])
    df_bloom = df_bloom.merge(df_external_tab8, on=date_col, how='left')
    iname = 'Europe Brent Spot Price FOB'
    ititle = 'Europe Brent Spot Price FOB'
    alldict.update([(iname, ititle)])
    iname = 'SCENARIO_oil_revenue'
    df_bloom[iname] = df_bloom['Europe Brent Spot Price FOB'] * df_bloom['PIWOABUD Index']
    ititle = 'Scenario Oil Revenue'
    alldict.update([(iname, ititle)])

    # Join to the master dataframe
    df_external['OBS_DT'] = pd.to_datetime(df_external['OBS_DT'])
    df_external = df_external.merge(df_bloom, on=date_col, how='left')
    Tmax = pd.Timestamp.now().strftime('%Y-%m-%d')
    mask = df_external[date_col] <= Tmax
    df_external = df_external.loc[mask]

    # Adding project contract awards data
    print('Collecting data from MEED_PROJECT_CONTRACT_AWARDS')
    query_str = "select * from MEED_PROJECT_CONTRACT_AWARDS"
    df_external_tab9 = pd.read_sql(query_str, con=conn)
    df_external_tab9 = df_external_tab9[['YEAR', 'MONTH', 'VALUE']]
    map_month = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    df_external_tab9.MONTH = df_external_tab9.MONTH.map(map_month)
    df_external_tab9[date_col] = df_external_tab9['YEAR'].astype(str) + '-' + df_external_tab9['MONTH'].astype(
        str) + '-01'
    df_external_tab9 = df_external_tab9[['VALUE', date_col]]
    df_external_tab9.columns = ['Meed_project_awards', date_col]
    # Join to the master dataframe
    df_external_tab9['OBS_DT'] = pd.to_datetime(df_external_tab9['OBS_DT'])
    df_external = df_external.merge(df_external_tab9, on=date_col, how='left')
    Tmax = pd.Timestamp.now().strftime('%Y-%m-%d')
    mask = df_external[date_col] <= Tmax
    df_external = df_external.loc[mask]
    # Add to the dict
    iname = 'Meed_project_awards'
    ititle = 'Meed project contract awards'
    alldict.update([(iname, ititle)])

    content_table10 = pd.DataFrame(columns=columns)

    content_table10['Columns'] = df_external_tab9.columns.tolist()
    FirstDay = min(df_external_tab9[date_col])
    content_table10['FirstDay'] = FirstDay
    LastDay = max(df_external_tab9[date_col])
    content_table10['LastDay'] = LastDay
    content_table10['TableName'] = 'MEED_PROJECT_CONTRACT_AWARDS'

    c.close()

    # Connection to Staging DB
    conn, c = database_connection_user(userSE_ECON)

    # TODO to be removed
    #############################################
    print('Collecting data from SCAD_VA_SECTORS')
    query_str = "select * from SCAD_VA_SECTORS"
    df_sector_tab = pd.read_sql(query_str, con=conn)
    df_sector_tab = df_sector_tab.sort_values(by=date_col)
    # df_sector_tab[date_col] = df_sector_tab["OBS_DT"].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    df_sector_tab[date_col] = df_sector_tab['OBS_DT'].str[0:4] + '-' + df_sector_tab['OBS_DT'].str[4:6] + '-' + df_sector_tab['OBS_DT'].str[6:]
    Tmin = df_sector_tab.OBS_DT.min()
    Tmax = pd.Timestamp.now().strftime('%Y-%m-%d')
    months = getM(Tmin, Tmax)

    df_sector = pd.DataFrame(columns=[date_col])
    df_sector[date_col] = months
    sectors = df_sector_tab.SECTOR.unique().tolist()
    for col in sorted(sectors):
        df_ind = df_sector_tab[df_sector_tab.SECTOR == col][[date_col, 'VALUE']]
        df_sector = df_sector.merge(df_ind, on=date_col, how='left')
        df_sector.rename(columns={'VALUE': col}, inplace=True)
        iname = col
        ititle = 'Target ' + col
        alldict.update([(iname, ititle)])

    c.close()

    content_table11 = pd.DataFrame(columns=columns)
    content_table11['Variables'] = pd.Series(df_sector_tab.SECTOR.unique())
    content_table11['Columns'] = pd.Series(df_sector_tab.columns.tolist())
    FirstDay = min(df_sector_tab[date_col])
    content_table11['FirstDay'] = FirstDay
    LastDay = max(df_sector_tab[date_col])
    content_table11['LastDay'] = LastDay
    content_table11['TableName'] = 'SCAD_VA_SECTORS'

    content_table = pd.concat([content_table, content_table1, content_table2,
                               content_table3, content_table4, content_table5,
                               content_table6, content_table7, content_table8,
                               content_table9, content_table10, content_table11], axis=0)
    content_table['Review_date'] = datetime.date.today()

    # Merge Sectors, Indicators, External
    df_sector_ind = df_sector.merge(dfall, on=date_col, how='outer', sort=True)
    df_sector_ind['OBS_DT'] = pd.to_datetime(df_sector_ind['OBS_DT'])
    df_complete = df_sector_ind.merge(df_external, on=date_col, how='outer', sort=True)

    # Formating to write to DB @Nicil
    df_complete[date_col] = df_complete[date_col].apply(lambda x: str(x).replace('-', ''))

    # Get  RUN_SEQ_ID
    # dsn_tns = cx_Oracle.makedsn(host, port, service_name=service_name)
    conn,c = database_connection_user(userSE_ECON)
    try:
        df_dict = pd.read_sql('select * from ds_ri_dictionary1', con=conn)
        run_seq_ind = df_dict[df_dict['Column Name'] == 'RUN_SEQ_ID']['Indicator'].values[0]
        Olddata = pd.read_sql("SELECT * from ds_ri_analytics_input1", con=conn)
        RUN_SEQ_ID = Olddata[run_seq_ind].max() + 1  # Last column is always RUN_SEQ_ID
    except:
        RUN_SEQ_ID = 1

    today = datetime.date.today()
    today = str(today).replace('-', '')
    INSERT_DT = today
    df_complete['INSERT_DT'] = INSERT_DT
    df_complete['RUN_SEQ_ID'] = RUN_SEQ_ID

    conn.close()

    # replace column names to fit into SQL restrictions
    colnames_dict = {}
    for cnum in range(df_complete.shape[1]):
        colnames_dict.update([(df_complete.columns[cnum], 'Ind_' + str(cnum))])

    df_complete.columns = df_complete.columns.to_series().map(colnames_dict)

    df_dict = pd.DataFrame(colnames_dict.items())
    df_dict.rename(columns={0: 'Column Name', 1: 'Indicator'}, inplace=True)
    df_dict['Description'] = ''
    for key in alldict.keys():
        ind = df_dict[df_dict['Column Name'] == key].index[0]
        df_dict.loc[ind, 'Description'] = alldict[key]

    # writing df_complete to Landing
    # Connection
    # oracle_connection_string = (
    #         'oracle+cx_oracle://{username}:{password}@' +
    #         cx_Oracle.makedsn('{hostname}', '{port}', service_name='{service_name}')
    # )

    # engine = create_engine(
    #     oracle_connection_string.format(
    #         username=user_MISC,
    #         password=password,
    #         hostname=host,
    #         port=port,
    #         service_name=service_name,
    #     )
    # )

    df_complete = df_complete.drop_duplicates(subset=['Ind_0'])

    ################################################################################

    if indicator_id == "COI_REALGDP_CNST":
        deflators_type = 'CONSTANT'
    else:
        deflators_type = 'CURRENT'
    type_pmi = '3_MONTH_MOVING_AVERAGE'

    print('Collecting data from SCAD_CLNSD_GDP_PRICES')
    # Load industry data
    industry_data = industry_fun(indicator_id=indicator_id)
    # Main function for data preparation. In this model, we will only use the analytical_df.
    conn, c = database_connection_user(userSE_ECON)
    analytical_df = data_preparation(
        analytical_df_raw=df_complete,
        analytical_colname_dict=df_dict,
        deflators_input=industry_data.copy(),
        deflators_calc=deflators_calc,
        deflators_type=deflators_type,
        target=target,
        conn=conn,
        save_raw_analytical_df=save_raw_analytical_df,
        save_transformed_analytical_df=save_transformed_analytical_df)
    # Remove target present in data
    a = analytical_df.columns.to_list()
    b = [x for x in targets if x in a]
    analytical_df.drop(columns=b, inplace=True)

    print('Collecting data from VW_BLOOMBERG_E_A_KPIS_REMAPPED')
    df_ext = additional_cb()
    analytical_df = analytical_df.merge(df_ext, left_index=True, right_index=True, how='outer')

    print('Collecting data from COI_PMI')
    # Add new indicators PMI Sector
    analytical_df = additional_pmi_cb(analytical_df)

    # analytical_df = analytical_df.merge(df_ext, left_index=True, right_index=True, how='outer')
    print('Collecting data from SCAD_GOV_SPENDING_ECONOMIC')
    # Add new indicators Government Expenditure
    df_gov_spend = additional_gov_exp()
    analytical_df = analytical_df.merge(df_gov_spend, left_index=True, right_index=True, how='outer')

    print('Collecting data from DS_ALDAR')
    # Add Aldar Historical Prices Indicators
    df_aldar = aldar_hist_price_func()
    analytical_df = analytical_df.merge(df_aldar, left_index=True, right_index=True, how='outer')

    print('Collecting data from UTILITIES ABU DHABI & AL AIN')
    # Add water_elec data
    #utilities_fname = 'UTILITY_BY_SECTOR_ABU_DHABI.xlsx'
    # df_utilities = utilities_func(utilities_fname)
    # analytical_df = analytical_df.merge(df_utilities, left_index=True, right_index=True, how='outer')

   
    df_utilities = additional_data_se_db('DS_UTILITIES')
    analytical_df = analytical_df.merge(df_utilities, left_index=True, right_index=True, how='outer')

    # print('Collecting data from UTILITIES AL AIN')
    # utilities_fname = 'UTILITY_BY_SECTOR_AL_AIN.xlsx'
    # df_utilities = utilities_func(utilities_fname)
    # analytical_df = analytical_df.merge(df_utilities, left_index=True, right_index=True, how='outer')

    print('Collecting data from PMI_FINANCE (extended)')
    # df_finance = additional_pmi_finance()
    # # add_extended_pmi_to_db(df_finance)
    # cols_finance = list(df_finance)
    # analytical_df.drop(cols_finance, axis=1, inplace=True, errors='ignore')
    # analytical_df = analytical_df.merge(df_finance, left_index=True, right_index=True, how='outer')
    df_finance = extended_coi_pmi('Finance and Insurance')
    cols_finance = list(df_finance)
    analytical_df.drop(cols_finance, axis=1, inplace=True, errors='ignore')
    analytical_df = analytical_df.merge(df_finance, left_index=True, right_index=True, how='outer')

    print('Collecting data from PMI_REAL_ESTATE (extended)')
    # df_re = additional_pmi_real_estate()
    # cols_re = list(df_re)
    # analytical_df.drop(cols_re, axis=1, inplace=True, errors='ignore')
    # analytical_df = analytical_df.merge(df_re, left_index=True, right_index=True, how='outer')
    df_re = extended_coi_pmi('RealEstate Business Services')
    # df_re = additional_pmi_real_estate()
    # add_extended_pmi_to_db(df_re)
    cols_re = list(df_re)
    analytical_df.drop(cols_re, axis=1, inplace=True, errors='ignore')
    analytical_df = analytical_df.merge(df_re, left_index=True, right_index=True, how='outer')

    print('Collecting data from STOCK_MARKET')
    # df_stock = additional_stock_market()
    # analytical_df = analytical_df.merge(df_stock, left_index=True, right_index=True, how='outer')
    df_stock = additional_data_se_db('DS_STOCK_MARKET')
    analytical_df = analytical_df.merge(df_stock, left_index=True, right_index=True, how='outer')

    # Non-Liquid Trade Data
    print('Collecting data from NON-LIQUID TRADE DATA HS2 & HS4')
    # trade_fname = 'hs2_amt.csv'
    # df_trade = trade_data(trade_fname)
    # analytical_df = analytical_df.merge(df_trade, left_index=True, right_index=True, how='outer')

    # print('Collecting data from NON-LIQUID TRADE DATA HS4')
    # trade_fname = 'hs4_amt.csv'
    # df_trade = trade_data(trade_fname)
    # analytical_df = analytical_df.merge(df_trade, left_index=True, right_index=True, how='outer')
    df_trade = additional_data_se_db('DS_TRADE')
    # df_trade_opt = additional_data_se_db_optimized('DS_TRADE', userSE_ECON, password, host, port, service_name, date_col)
    analytical_df = analytical_df.merge(df_trade, left_index=True, right_index=True, how='outer')

    print('Collecting data from DS_MEED')
    # Add Meed Project Awards indicators
    df_meed = meed_awards_func()
    analytical_df = analytical_df.merge(df_meed, left_index=True, right_index=True, how='outer')
    # analytical_df = pd.concat([analytical_df,df_meed])
    # add Target
    target_val = analytical_df[target]
    analytical_df.drop([target], axis=1, inplace=True, errors='ignore')

    target_val = target_val.reset_index()
    target_val.rename(columns={'index': date_col}, inplace=True)

    # target_val[date_col] = target_val[date_col].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])
    target_val[date_col] = pd.to_datetime(target_val[date_col])
    target_val.set_index(date_col, inplace=True)
    target_val = target_val[target_val.index < forecast_start]

    # analytical_df = analytical_df.merge(target_val, left_index=True, right_index=True, how='outer')
    analytical_df = pd.concat([analytical_df,target_val])
    return analytical_df

def arrange_analytical_df(deflators_input, conn, deflators_calc, target, analytical_df: pd.DataFrame,
                          analytical_colname_dict: pd.DataFrame):
    colnames_dict_inv = dict(analytical_colname_dict[['Indicator', 'Column Name']].values.tolist())
    analytical_df.columns = analytical_df.columns.to_series().map(colnames_dict_inv)
    analytical_df = analytical_df.sort_values(by='OBS_DT')
    RUN_SEQ_ID = analytical_df['RUN_SEQ_ID'].max()
    analytical_df = analytical_df[analytical_df['RUN_SEQ_ID'] == RUN_SEQ_ID]
    # analytical_df = analytical_df.drop(columns=['INSERT_DT','RUN_SEQ_ID'])
    # Change None by na: TODO: Why do we have None????
    # analytical_df = analytical_df.fillna(value=np.nan)
    deflators_input.reset_index(inplace=True)
    if deflators_calc == True:
        targets_deflators = ['Business services', 'Commerce and goods transport',
                             'Construction and real estate', 'Leisure', 'Manufacturing Activities',
                             'Oil', 'Total GDP', 'Total Non -Oil GDP']  # targets that we want to predict
        analytical_df = analytical_df.drop(targets_deflators, axis=1)  # only variables, not the target
        analytical_df = pd.merge(deflators_input[['OBS_DT']], analytical_df, on='OBS_DT', how='right')
        analytical_df['OBS_DT'] = pd.to_datetime(analytical_df['OBS_DT'])
        analytical_df.set_index(['OBS_DT'], inplace=True)
    return analytical_df


def data_preparation(analytical_df_raw, analytical_colname_dict, deflators_input, deflators_calc, deflators_type,
                     target, conn, save_raw_analytical_df: bool,
                     save_transformed_analytical_df: bool):
    # Get the original data:
    # analytical_df_raw, analytical_colname_dict = get_analytical_datatables(conn)
    # Arrange together analytical dataset and columns dictionary db
    raw_analytical_df = arrange_analytical_df(deflators_input, conn, deflators_calc, target,
                                              analytical_df=analytical_df_raw.copy(),
                                              analytical_colname_dict=analytical_colname_dict)

    return raw_analytical_df


def industry_fun(indicator_id):
    # Connection to Landing Layer
    # dsn_tns = cx_Oracle.makedsn(host, port, service_name=service_name)
    # conn = cx_Oracle.connect(user=userLD_ECON, password=password, dsn=dsn_tns, encoding="UTF-8")
    conn,c = database_connection_user(DB_CONFIG.userLD_ECON)
    c = conn.cursor()
    df_lk = pd.read_sql("select * from lk_industry_sector_map", con=conn)
    c.close()
    # Connection to Staging Layer
    # dsn_tns = cx_Oracle.makedsn(host, port, service_name=service_name)
    # conn = cx_Oracle.connect(user=userSE_ECON, password=password, dsn=dsn_tns, encoding="UTF-8")
    conn,c  = database_connection_user(DB_CONFIG.userSE_ECON)
    c = conn.cursor()
    gdp_table = 'scad_clnsd_gdp_prices'
    # execution_date_old_data = '20220113'
    execution_date_new_data = '20220706'
    # query_before_2014 = f"select * from {gdp_table} where " \
    #                     f"INSERT_DT='{execution_date_old_data}' and " \
    #                     f"to_date(OBS_DT, 'YYYY-MM-DD') < TO_TIMESTAMP('20140101', 'YYYY-MM-DD')"
    query_after_2014 = f"select * from {gdp_table} where " \
                       f"INSERT_DT='{execution_date_new_data}'"

    # df_gdp_before = pd.read_sql(query_before_2014, con=conn)
    # # df_gdp = pd.read_sql("select * from scad_clnsd_gdp_prices_test", con=conn)
    # df_gdp_before = df_gdp_before.sort_values(by='OBS_DT')
    df_gdp_after = pd.read_sql(query_after_2014, con=conn)
    # df_gdp = pd.read_sql("select * from scad_clnsd_gdp_prices_test", con=conn)
    df_gdp_after = df_gdp_after.sort_values(by='OBS_DT')

    df_gdp = df_gdp_after.copy()
    # df_gdp = pd.concat([df_gdp_before, df_gdp_after])

    # current and constant GDPs Data into DF
    df_gdp_cons = df_gdp[df_gdp.INDICATOR_ID == indicator_id]

    # Remove Government and unknown sectors from look-up table
    irows = df_lk[df_lk.SECTOR == 'Government'].index
    df_lk = df_lk.drop(irows)
    irows = df_lk[df_lk.SECTOR.isnull()].index
    df_lk = df_lk.drop(irows)

    # do the summation by sector
    List1 = df_lk[df_lk.SECTOR == 'Business services']['INDUSTRY_GROUP'].tolist()
    List2 = df_lk[df_lk.SECTOR == 'Commerce and goods transport']['INDUSTRY_GROUP'].tolist()
    List3 = df_lk[df_lk.SECTOR == 'Construction and real estate']['INDUSTRY_GROUP'].tolist()
    List4 = df_lk[df_lk.SECTOR == 'Leisure']['INDUSTRY_GROUP'].tolist()
    List5 = df_lk[df_lk.SECTOR == 'Manufacturing Activities']['INDUSTRY_GROUP'].tolist()
    List6 = df_lk[df_lk.SECTOR == 'Oil']['INDUSTRY_GROUP'].tolist()
    List7 = df_lk[df_lk.SECTOR == 'Total GDP']['INDUSTRY_GROUP'].tolist()
    List8 = List1 + List2 + List3 + List4 + List5

    df_gdp_cons_industry = df_gdp_cons[['INDUSTRY', 'VALUE', 'OBS_DT']]
    df_gdp_cons_industry = pd.DataFrame(df_gdp_cons_industry.groupby(['INDUSTRY', 'OBS_DT'])['VALUE'].sum())
    df_gdp_cons_industry = df_gdp_cons_industry.pivot_table(index='OBS_DT', columns='INDUSTRY', values='VALUE',
                                                            aggfunc='sum')

    return (df_gdp_cons_industry)

def additional_cb():
    # Connection to Landing Layer
    conn,c = database_connection_user(DB_CONFIG.userLD_ECON)
    c = conn.cursor()
    bloomberg = pd.read_sql("select * from VW_BLOOMBERG_E_A_KPIS_REMAPPED", con=conn)
    c.close()

    df_m1 = bloomberg[bloomberg.BLG_ID == 'BLG_UEMSM1Y'][[date_col, 'VALUE']]
    df_m1[date_col] = pd.to_datetime(df_m1[date_col], format='%Y%m%d')
    df_m1 = df_m1.groupby(pd.Grouper(key=date_col, freq='1M')).mean()  # groupby each 1 month
    df_m1 = df_m1.reset_index()
    df_m1[date_col] = df_m1[date_col].dt.strftime('%Y-%m-01')
    df_m1.sort_values(by=date_col, inplace=True)
    df_m1[date_col] = pd.to_datetime(df_m1[date_col], format='%Y-%m-%d')
    df_m1 = df_m1.set_index(date_col)
    df_m1.rename(columns={'VALUE': 'M1_Bloom'}, inplace=True)

    df_m2 = bloomberg[bloomberg.BLG_ID == 'BLG_UAMMM2M'][[date_col, 'VALUE']]
    df_m2[date_col] = pd.to_datetime(df_m2[date_col], format='%Y%m%d')
    df_m2 = df_m2.groupby(pd.Grouper(key=date_col, freq='1M')).mean()  # groupby each 1 month
    df_m2 = df_m2.reset_index()
    df_m2[date_col] = df_m2[date_col].dt.strftime('%Y-%m-01')
    df_m2.sort_values(by=date_col, inplace=True)
    df_m2[date_col] = pd.to_datetime(df_m2[date_col], format='%Y-%m-%d')
    df_m2 = df_m2.set_index(date_col)
    df_m2.rename(columns={'VALUE': 'M2_Bloom'}, inplace=True)

    df_bloom_ms = df_m1.merge(df_m2['M2_Bloom'], left_index=True, right_index=True, how='outer')

    df_m3 = bloomberg[bloomberg.BLG_ID == 'BLG_UAMMM3M'][[date_col, 'VALUE']]
    df_m3[date_col] = pd.to_datetime(df_m3[date_col], format='%Y%m%d')
    df_m3 = df_m3.groupby(pd.Grouper(key=date_col, freq='1M')).mean()  # groupby each 1 month
    df_m3 = df_m3.reset_index()
    df_m3[date_col] = df_m3[date_col].dt.strftime('%Y-%m-01')
    df_m3.sort_values(by=date_col, inplace=True)
    df_m3[date_col] = pd.to_datetime(df_m3[date_col], format='%Y-%m-%d')
    df_m3 = df_m3.set_index(date_col)
    df_m3.rename(columns={'VALUE': 'M3_Bloom'}, inplace=True)

    df_bloom_ms = df_bloom_ms.merge(df_m3['M3_Bloom'], left_index=True, right_index=True, how='outer')

    stock_exchange = bloomberg[bloomberg.BLG_ID == 'BLG_ADSMI'][[date_col, 'VALUE']]
    stock_exchange[date_col] = pd.to_datetime(stock_exchange[date_col], format='%Y%m%d')
    stock_exchange = stock_exchange.groupby(pd.Grouper(key=date_col, freq='1M')).mean()  # groupby each 1 month
    stock_exchange = stock_exchange.reset_index()
    stock_exchange[date_col] = stock_exchange[date_col].dt.strftime('%Y-%m-01')
    stock_exchange[date_col] = pd.to_datetime(stock_exchange[date_col], format='%Y-%m-%d')
    stock_exchange = stock_exchange.set_index(date_col)
    stock_exchange.rename(columns={'VALUE': 'STOCK_EXCHANGE'}, inplace=True)

    df_ext = df_bloom_ms.merge(stock_exchange, left_index=True, right_index=True, how='outer')

    return df_ext


def pmi_sector_func(pmi_sector):
    conn_lk, c_ld = database_connection_user(DB_CONFIG.userLD_ECON)
    query = "select * from coi_pmi where region='Abu Dhabi' \
        and sector='" + pmi_sector + "' \
            and pmi_date is not null \
                and type='Three month Moving Average'"

    if pmi_sector == 'Whole Economy':
        query = query + " and Company_Size='Overall PMI'"
        company_size = '_Overall PMI_'
    else:
        company_size = '__'

    column_name = 'PMI_' + pmi_sector + '_Abu Dhabi_Three month Moving Average' + company_size

    coi_pmi_data0 = pd.read_sql(query, con=conn_lk)

    coi_pmi_data0['PMI_DATE'] = pd.to_datetime(coi_pmi_data0['PMI_DATE'], format='%Y-%b-%d')
    coi_pmi_data0.sort_values(by='PMI_DATE', inplace=True)
    coi_pmi_data0.drop(['ID', 'YEAR_ID'], axis=1, inplace=True)
    coi_pmi_data = coi_pmi_data0.drop_duplicates()

    coi_pmi_data['PMI_INDEX'] = coi_pmi_data['PMI_INDEX'].astype(float)
    coi_pmi_data = pd.pivot_table(coi_pmi_data,
                                  values='PMI_INDEX',
                                  index='PMI_DATE',
                                  columns='INDICIES')

    coi_pmi_data.columns = [column_name + x.upper() for x in coi_pmi_data.columns]

    coi_pmi_data = coi_pmi_data.astype(float)
    coi_pmi_data.index.name = str(date_col)
    # coi_pmi_data = coi_pmi_data.rename(index={'PMI_DATE': date_col})

    return coi_pmi_data


def additional_gov_exp():
    conn_ld, c_ld = database_connection_user(DB_CONFIG.userLD_ECON)

    # Additional indicators Government spending to be investigated
    df_gov = pd.read_sql("select * from SCAD_GOV_SPENDING_ECONOMIC", con=conn_ld)
    df_gov[date_col] = pd.to_datetime(df_gov[date_col], format='%Y%m%d')
    df_gov = df_gov.sort_values(by=date_col)

    gov_sec = df_gov.SECTOR.unique().tolist()
    gov_types = df_gov.TYPE.unique().tolist()
    df_gov_spend = pd.DataFrame(index=df_gov.OBS_DT.unique())
    for i in gov_sec:
        for j in gov_types:
            a = df_gov[(df_gov.SECTOR == i) & (df_gov.TYPE == j)][[date_col, 'VALUE']]
            a.set_index(date_col, inplace=True)
            df_gov_spend[i + '_' + j] = a.VALUE
    return df_gov_spend


def aldar_hist_price_func():
    # conn_ld, c_ld = database_connection_user(userLD_ECON)
    # dsn_tns = cx_Oracle.makedsn(host, port, service_name=service_name)
    # conn = cx_Oracle.connect(user=userSE_ECON, password=password, dsn=dsn_tns, encoding="UTF-8")
    conn,c = database_connection_user(DB_CONFIG.userSE_ECON)

    # # Indicators from ALDAR Prices
    df_aldar2 = pd.read_sql("select * from DS_ALDAR", con=conn)
    df_aldar2 = df_aldar2.sort_values(by=date_col)
    df_aldar2.set_index(date_col, inplace=True)
    df_aldar_selected = df_aldar2.copy()
    return df_aldar_selected


def meed_awards_func():
    # conn_ld, c_ld = database_connection_user(userLD_ECON)
    # dsn_tns = cx_Oracle.makedsn(host, port, service_name=service_name)
    # conn = cx_Oracle.connect(user=userSE_ECON, password=password, dsn=dsn_tns, encoding="UTF-8")
    conn,c = database_connection_user(DB_CONFIG.userSE_ECON)

    # # Indicators from MEED PROJECTS
    df_meed2 = pd.read_sql("select * from DS_MEED", con=conn)
    
    df_meed2.rename(columns={'MEEDAwardedDate': date_col}, inplace=True)
    df_meed2[date_col] = pd.to_datetime(df_meed2[date_col], format='%Y-%m-%d')
    df_meed2 = df_meed2.sort_values(by=date_col)
    df_meed2.set_index(date_col, inplace=True)
    list2 = df_meed2.columns.to_list()
    list_ = [x for x in list2 if x.startswith('_')]
    list2 = [x for x in list2 if not x.startswith('_')]
    df_meed2.drop(columns=list_, inplace=True)
    list2 = [x.replace('Abu_Dhabi', 'Abu Dhabi') for x in list2]
    list2 = [x.replace('Region_MEEDContractVal', 'Region_MEEDContractValue') for x in list2]
    list2 = [x.replace('Western_Region', 'Western Region') for x in list2]
    list2 = [x.replace('Al_Ain', 'Al Ain') for x in list2]
    list2 = [x.replace('Ar_Ruways', 'Ar Ruways') for x in list2]

    df_meed2.columns = list2
    df_meed2 = df_meed2[list2]
    df_meed = df_meed2.copy()

    return df_meed

########################################
# Additional data sets
def additional_pmi_cb(analytical_df):
    # Add PMI data

    pmi_sectors = ['Wholesale and Retail Services',
                   'Finance and Insurance',
                   'Transportation Information and Communication',
                   'Construction',
                   'Manufacturing',
                   'Whole Economy',
                   'Services',
                   'RealEstate Business Services',
                   'Travel & Tourism',
                   'WholesaleRetail']
    for pmi_sector in pmi_sectors:
        df_pmi_sector = pmi_sector_func(pmi_sector)
        analytical_df = analytical_df.merge(df_pmi_sector, left_index=True, right_index=True, how='outer')

    return analytical_df

# Method for reading 'utilities', 'stock/commodities' and 'non-liquid trade' data from the DB
def additional_data_se_db(db_table):
    # dsn_tns = cx_Oracle.makedsn(host, port, service_name=service_name)
    # conn = cx_Oracle.connect(user=userSE_ECON, password=password, dsn=dsn_tns, encoding="UTF-8")
    conn,c = database_connection_user(DB_CONFIG.userSE_ECON)
    c = conn.cursor()
    df = pd.read_sql(f"select * from {db_table}", con=conn)
    c.close()

    inds = df['INDICATOR_ID'].unique()
    dlist = []
    df_all = pd.DataFrame()
    for ind in inds:
        df_ind = df[df.INDICATOR_ID == ind][[date_col, 'VALUE']]
        df_ind.fillna(value=np.nan, inplace=True)
        df_ind['VALUE'] = pd.to_numeric(df_ind['VALUE'])
        df_ind[date_col] = pd.to_datetime(df_ind[date_col])

        df_ind = df_ind.reset_index()
        df_ind[date_col] = df_ind[date_col].dt.strftime('%Y-%m-01')
        df_ind.sort_values(by=date_col, inplace=True)
        df_ind[date_col] = pd.to_datetime(df_ind[date_col], format='%Y-%m-%d')
        df_ind = df_ind.set_index(date_col)
        df_ind.rename(columns={'VALUE': ind}, inplace=True)
        df_ind.drop(columns=['index'], inplace=True)
        dlist.append(df_ind)
    # df_all = reduce(lambda x,y: pd.merge(x,y, left_index=True, right_index=True, how = "outer"), dlist)
    df_all = pd.concat(dlist)
        # df_all = df_all.merge(df_ind, left_index=True, right_index=True, how='outer')
    return df_all

# Add Extended PMI data
def extended_coi_pmi(pmi_sector):

    conn_lk, c_ld = database_connection_user(DB_CONFIG.userLD_ECON)
    query = "select * from coi_pmi_extended where sector='" + pmi_sector + "' \
            and pmi_date is not null"

    if pmi_sector == 'Whole Economy':
        query = query + " and Company_Size='Overall PMI'"
        company_size = '_Overall PMI_'
    else:
        company_size = '__'

    column_name = 'PMI_' + pmi_sector + '_Abu Dhabi_Three month Moving Average' + company_size

    coi_pmi_data0 = pd.read_sql(query, con=conn_lk)

    coi_pmi_data0['PMI_DATE'] = pd.to_datetime(coi_pmi_data0['PMI_DATE'])
    coi_pmi_data0.sort_values(by='PMI_DATE', inplace=True)
    coi_pmi_data0.drop(['ID', 'YEAR_ID'], axis=1, inplace=True)
    coi_pmi_data = coi_pmi_data0.drop_duplicates()

    coi_pmi_data['PMI_INDEX'] = coi_pmi_data['PMI_INDEX'].astype(float)
    coi_pmi_data = pd.pivot_table(coi_pmi_data,
                                  values='PMI_INDEX',
                                  index='PMI_DATE',
                                  columns='INDICIES')

    coi_pmi_data.columns = [column_name + x.upper() for x in coi_pmi_data.columns]

    coi_pmi_data = coi_pmi_data.astype(float)
    coi_pmi_data.index.name = str(date_col)
    # coi_pmi_data = coi_pmi_data.rename(index={'PMI_DATE': date_col})

    return coi_pmi_data

def query_sql(query, c):
    """
    Execute a SQL query and return the results as a DataFrame
    
    Args:
        query: SQL query string
        c: Database cursor
        
    Returns:
        DataFrame with query results
    """
    c.execute(query)
    names = [x[0] for x in c.description]
    rows = c.fetchall()
    df = pd.DataFrame(rows, columns=names)
    return df

def get_jv_tawteen(target):
    """
    Get job vacancies data from Tawteen
    
    Args:
        target: Target region
        
    Returns:
        DataFrame with job vacancies data
    """
    print('Collecting data from Tawteen Job Vacancies')
    print('Collecting data from Tawteen Job Vacancies')
    #df_jv0 = pd.read_excel(cdir + '\\' + fname)
    db_config = get_db_config()
    conn_jv, c_ld = database_connection_user(db_config.userS_JobVac)
    df_jv = pd.read_sql(" select * from DS_JV_TAWTEEN_UNEMPLOYMENT", con = conn_jv)
#    df_jv = df_jv1.copy()
    # remove “Posted by Mistake”, “Moved to subsidiary”
    ind = df_jv[df_jv['Reason English'].isin(['Posted by Mistake','Moved to Subsidiary'])].index
    df_jv.drop(ind, inplace=True)
    df_jv_total = df_jv.groupby('Created Date').agg({'No of Vacancies':'sum'})
    df_jv_total.reset_index(inplace=True)
    df_jv_total= df_jv_total.groupby(df_jv_total['Created Date'].dt.to_period('Y')).agg({'No of Vacancies':'sum'})
    df_jv_total.reset_index(inplace=True)
    qs = df_jv_total['Created Date'].astype(str)
    qs = pd.PeriodIndex(qs, freq='Y').to_timestamp()
    qs = qs + pd.offsets.YearEnd(0)
    
    df_jv_total['OBS_DT'] = qs
    df_jv_total.set_index('OBS_DT',inplace=True)
    fig, ax1 = plt.subplots()
    ax1.plot(df_jv_total.index, df_jv_total['No of Vacancies'], 'r-o', label = 'Monthly', marker='.')
    ax1.legend(loc = 'upper right')
    ax1.set_ylabel('No of Vacancies - Total', color='g')
    plt.show()
    # add regions
    regions = ['Abu Dhabi', 'Abu Dhabi - Abu Dhabi', 
               'Abu Dhabi - Al Dhafra', 'Al Ain', 
               'Al Ain - Al Dhafra', 'Al Dhafra', 
               'Al Dhafra - Al Dhafra']
    df_jv_regions = df_jv[df_jv['Vacancy Location'].isin(regions)]
    df_jv_regions_count = df_jv_regions.groupby('Vacancy Location').agg({'No of Vacancies':'sum'})
#    df_jv_regions_count.to_excel('temp.xlsx')
    for region in regions:
        df_temp = df_jv_regions[df_jv_regions['Vacancy Location']==region]
        df_jv_reg_total = df_temp.groupby('Created Date').agg({'No of Vacancies':'sum'})
        df_jv_reg_total.reset_index(inplace=True)
        df_jv_reg_total= df_jv_reg_total.groupby(df_jv_reg_total['Created Date'].dt.to_period('Y')).agg({'No of Vacancies':'sum'})
        df_jv_reg_total.reset_index(inplace=True)
        qs = df_jv_reg_total['Created Date'].astype(str)
        qs = pd.PeriodIndex(qs, freq='Y').to_timestamp()
        qs = qs + pd.offsets.YearEnd(0)
        df_jv_reg_total['OBS_DT'] = qs
        df_jv_reg_total.set_index('OBS_DT',inplace=True)
        df_jv_reg_total.rename(columns={'No of Vacancies':region}, inplace=True)
        df_jv_total = pd.merge(df_jv_total, df_jv_reg_total[region], left_index=True,  right_index=True, how='outer')
    df_jv_final = df_jv_total.drop(columns=['Created Date'])
    
    fig, ax1 = plt.subplots()
    ax1.plot(df_jv_total.index, df_jv_total['No of Vacancies'], 'r-o', color='black', linewidth = 3,  label='Job Vacancies')
    ax1.legend(loc = 'upper right')
    ax1.set_ylabel(target, color='g')
    plt.show()
    return df_jv_final
