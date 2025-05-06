# -*- coding: utf-8 -*-
"""
Main entry point for the unemployment forecast model.
"""

from execution.unemployment_forecast import run_unemployment_forecast
from config.parameters import get_default_parameters

def main():
    """
    Main function to run the unemployment forecast model
    """
    # Get default parameters
    params = get_default_parameters()

    # Run the forecast
    run_unemployment_forecast(params)


if __name__ == "__main__":
    main()
