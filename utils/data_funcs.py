from sqlalchemy import types
from ..config.parameters import get_default_parameters

def save_to_sql(forecast_index, engine, output_table):
    # save index data
    params = get_default_parameters()
    if params.save_oracle:
        dtyp = {c: types.VARCHAR(300)
                for c in forecast_index.columns[forecast_index.dtypes == 'object'].tolist()}
        dtyp_float = {c: types.VARCHAR(500)
                        for c in forecast_index.columns[forecast_index.dtypes == 'float64'].tolist()}
        dtyp_all = {**dtyp, **dtyp_float}
        forecast_index.to_sql(output_table.lower(), con=engine, if_exists='append', index=False, dtype=dtyp_all)