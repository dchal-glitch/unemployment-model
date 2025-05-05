import pandas as pd

def getM(start_date, end_date):
    """
    Get a list of months between start_date and end_date
    
    Args:
        start_date: Start date string in format 'YYYY-MM-DD'
        end_date: End date string in format 'YYYY-MM-DD'
        
    Returns:
        List of month strings in format 'YYYY-MM-DD'
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    return pd.date_range(start=start, end=end, freq='MS').strftime('%Y-%m-%d').tolist()
