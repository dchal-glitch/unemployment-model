# -*- coding: utf-8 -*-
"""
Parameters for the unemployment forecast model.
"""

import os

# Variable Parameters
##### Model execution folder  #####
# Base directory for the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory for predictions
PREDICTIONS_DIR = os.path.join(BASE_DIR, "predictions")

FORECAST_TYPE = '2Q'

# Create predictions directory if it doesn't exist
os.makedirs(PREDICTIONS_DIR, exist_ok=True)

################# Define Forecast Period ####################

# Default forecast parameters
DEFAULT_FORECAST_START = '2024-12-31'
DEFAULT_FORECAST_END = '2025-06-30'   # Two quarters ahead from start for 2Q models

# used for 2Q forecast
# forecast_1Q = '2024-09-30'

# forecast_end_2q = '2023-12-31'

# Number of Quarters to Forecast
DEFAULT_NUM_QUARTER = 2
DEFAULT_FORECAST_HORIZON = 3

################# Select Target to be model ####################
# Default citizen types to model
DEFAULT_CITIZEN_IDS = ['Citizen', 'Non-Citizen']
# DEFAULT_CITIZEN_IDS = ['Non-Citizen']

################# Select Region to be model ####################
# DEFAULT_TARGET_REGS = ['Al Ain','Al Dhafra','Abu Dhabi']
DEFAULT_TARGET_REGS = ['TOTAL_UNEM', 'Abu Dhabi', 'Al Ain', 'Al Dhafra']
# DEFAULT_TARGET_REGS = ['Abu Dhabi']
# DEFAULT_TARGET_REGS = ['TOTAL_UNEM']

# Default indicator ID
DEFAULT_INDICATOR_ID = 'COI_REALGDP_CNST'

# Debug mode flag
DEFAULT_MODEL_DEBUG = False

# Save options
DEFAULT_SAVE_EXCEL = True
DEFAULT_SAVE_ORACLE = False
DEFAULT_SAVE_MODEL = False

# Deflators calculation flag
DEFAULT_DEFLATORS_CALC = True

# Descaling coefficients flag
DEFAULT_DESCALING_COEFFICIENTS = True

# Scenario flag
DEFAULT_SCENARIO_FLAG = False

# Save parameters flag
DEFAULT_SAVE_PARAM = False

# Default user for insertions
DEFAULT_INSERT_USER = 'dravi@scad.gov.ae'

# MLFlow parameters for tracking experiments
DEFAULT_ML_FLOW_PARAMS = {
    'Citizen': {
        'Al Ain': 0,
        'Al Dhafra': 0,
        'Abu Dhabi': 0,
        'TOTAL_UNEM': '517159818264510724'
    },
    'Non-Citizen': {
        'Al Ain': 0,
        'Al Dhafra': 0,
        'Abu Dhabi': 0,
        'TOTAL_UNEM': '497727559741225437'
    }
}

######## Correlation-lag scan parameters #####
DEFAULT_CORR_LAG_THRESHOLD = 0.6  # minimum correlation indicator-target @ peak lag required to be accepted
DEFAULT_MINIMUM_END_DATE = '2022-12-31'  # last observation date of the indicator

######## Combination study parameters #####
DEFAULT_MIN_INDICATORS = 5  # number of indicators for minimum group of indicators to be scan. Typical values 5, 6 or 7
DEFAULT_SUM_INACC = 6  # sum of inaccuracies of last 2 observations should be <6%. This parameters depends heavily on the region and citizenship
DEFAULT_R2_THRESHOLD = 0.6  # r2 threshold value to be satisfied to evaluate FI of the model being scanned by the combination scan. Typical range [0.5 to 0.9]
DEFAULT_MAX_INACCURACY_BEST_MODELS = 3.0  # tune threshold according to best innacuracies obtained by the best models. It depends on region and citizenship

class ModelParameters:
    """Model parameters class that can be customized for each run"""

    def __init__(self):
        # Forecast parameters
        self.forecast_start = DEFAULT_FORECAST_START
        self.forecast_end = DEFAULT_FORECAST_END
        self.num_quarter = DEFAULT_NUM_QUARTER
        self.forecast_horizon = DEFAULT_FORECAST_HORIZON

        # Target parameters
        self.citizen_ids = DEFAULT_CITIZEN_IDS
        self.target_regs = DEFAULT_TARGET_REGS
        self.indicator_id = DEFAULT_INDICATOR_ID

        # Debug and save options
        self.model_debug = DEFAULT_MODEL_DEBUG
        self.save_excel = DEFAULT_SAVE_EXCEL
        self.save_oracle = DEFAULT_SAVE_ORACLE
        self.save_model = DEFAULT_SAVE_MODEL

        # Processing options
        self.deflators_calc = DEFAULT_DEFLATORS_CALC
        self.descaling_coefficients = DEFAULT_DESCALING_COEFFICIENTS
        self.scenario_flag = DEFAULT_SCENARIO_FLAG
        self.save_param = DEFAULT_SAVE_PARAM

        # Raw and transformed analytical dataframe save options
        self.save_raw_analytical_df = False
        self.save_transformed_analytical_df = False

        # User information
        self.insert_user = DEFAULT_INSERT_USER

        # MLFlow parameters
        self.ml_flow_params = DEFAULT_ML_FLOW_PARAMS

        # Correlation-lag scan parameters
        self.corr_lag_threshold = DEFAULT_CORR_LAG_THRESHOLD
        self.minimum_end_date = DEFAULT_MINIMUM_END_DATE

        # Combination study parameters
        self.min_indicators = DEFAULT_MIN_INDICATORS
        self.sum_inacc = DEFAULT_SUM_INACC
        self.r2_threshold = DEFAULT_R2_THRESHOLD
        self.max_inaccuracy_best_models = DEFAULT_MAX_INACCURACY_BEST_MODELS

        # Directory for predictions
        self.predictions_dir = PREDICTIONS_DIR


def get_default_parameters():
    """Returns a ModelParameters object with default settings"""
    return ModelParameters()
