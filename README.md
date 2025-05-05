# Unemployment Forecast Model

## Introduction

This is a restructured version of the Unemployment Forecast Model. The code has been reorganized into a more modular and maintainable structure.

## Project Structure

```
unemp_restructured/
├── config/                 # Configuration parameters
│   ├── __init__.py
│   └── parameters.py       # Model parameters
├── data/                   # Data collection and processing
│   ├── __init__.py
│   └── collection.py       # Data collection functions
├── execution/              # Execution scripts
│   ├── __init__.py
│   └── unemployment_forecast.py  # Main execution script
├── models/                 # Model functions
│   ├── __init__.py
│   └── unemployment.py     # Unemployment model functions
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── db_connection.py    # Database connection utilities
├── __init__.py
├── main.py                 # Main entry point
└── README.md               # This file
```

## Usage

### Running the Model

To run the model with default parameters:

```python
from unemp_restructured.execution.unemployment_forecast import run_unemployment_forecast

run_unemployment_forecast()
```

Or from the command line:

```bash
python -m unemp_restructured.execution.unemployment_forecast
```

### Customizing Parameters

You can customize the model parameters:

```python
from unemp_restructured.config.parameters import get_default_parameters
from unemp_restructured.execution.unemployment_forecast import run_unemployment_forecast

# Get default parameters
params = get_default_parameters()

# Customize basic parameters
params.forecast_start = '2024-12-31'
params.forecast_end = '2025-06-30'
params.citizen_ids = ['Citizen']
params.target_regs = ['TOTAL_UNEM']
params.save_excel = True
params.save_oracle = False

# Customize advanced parameters
params.num_quarter = 2
params.forecast_horizon = 3
params.indicator_id = 'COI_REALGDP_CNST'
params.model_debug = True
params.scenario_flag = False
params.insert_user = 'your.email@example.com'

# Customize model study parameters
params.min_indicators = 5
params.r2_threshold = 0.6
params.corr_lag_threshold = 0.6
params.max_inaccuracy_best_models = 3.0

# Run with custom parameters
run_unemployment_forecast(params)
```

## Command Line Arguments

The model can be run with command line arguments:

```bash
python -m unemp_restructured.execution.unemployment_forecast --forecast_start 2024-12-31 --forecast_end 2025-06-30 --citizen_ids Citizen --target_regs TOTAL_UNEM --save_excel --debug
```

### Available Command Line Arguments

- `--forecast_start`: Forecast start date (YYYY-MM-DD)
- `--forecast_end`: Forecast end date (YYYY-MM-DD)
- `--num_quarter`: Number of quarters to forecast
- `--forecast_horizon`: Forecast horizon in quarters
- `--citizen_ids`: Citizen IDs to model (can specify multiple)
- `--target_regs`: Target regions to model (can specify multiple)
- `--indicator_id`: Indicator ID
- `--save_excel`: Save results to Excel
- `--save_oracle`: Save results to Oracle
- `--save_model`: Save model
- `--debug`: Enable debug mode
- `--scenario`: Enable scenario-based forecasting
- `--insert_user`: User for insertions
- `--min_indicators`: Minimum number of indicators for combination study
- `--r2_threshold`: R2 threshold for model evaluation

## Dependencies

- pandas
- numpy
- scikit-learn
- flaml
- darts
- cx_Oracle
- sqlalchemy
