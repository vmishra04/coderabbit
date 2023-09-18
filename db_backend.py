import pandas as pd
from datetime import date, datetime, timedelta
from typing import List
from os import getenv

# You can leave this connection string as is even though there's a password visible in the codebase
# Otherwise, make as many changes to this file as you feel are necessary.

PG_USER = getenv("PGUSER")
PG_PASSWORD = getenv("PGPASSWORD")
PG_HOST = getenv("PGHOST")
CONNECTION_STRING = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/market_data'

def get_all_valid_nodes() -> List[str]:
    """Return all valid node identifiers

    Returns:
        List of all valid node identifiers

    """
    sql = f'''
        SELECT DISTINCT node FROM public.node_status;
    '''
    return pd.read_sql(sql, CONNECTION_STRING)['node'].tolist()

def get_valid_dates() -> List[date]:
    """Return all of the dates forecast analyses have been run on 

    Returns:
        List of dates that forecasts analyses have been run on 

    """
    sql = f'''
        SET timezone = 'GMT';
        SELECT DISTINCT forecasted_price.analysis_datetime::DATE FROM public.forecasted_price 
        ORDER BY analysis_datetime ASC;
    '''
    return pd.read_sql(sql, CONNECTION_STRING)['analysis_datetime'].tolist()

def get_all_online_nodes(current_date: date) -> List[str]:
    """Given a date, return all the nodes that are online at the start of that date

    Args:
        current_date: The date to match for online nodes

    Returns:
        List of online nodes
    """
    sql = f'''
        SET timezone = 'GMT';
        SELECT node FROM public.node_status
        WHERE online = true AND observed_datetime = \'{current_date}\'
       '''
    return pd.read_sql(sql, CONNECTION_STRING)['node'].tolist()


def get_recent_price_forecast(current_date: date, node: str) -> pd.DataFrame:
    """Get price forecasts for the next day for the provided node

    It can be assumed that forecasts are only made once per day and that each set of forecasts for
    that analysis day corresponds to the 24 hours of the next day. It can also be assumed that each node will
    have a forecast.

    Args:
        current_date: The date from which forecasts are being made
        node: The name of the node to get forecasts for

    Returns:
        DataFrame with columns: forecast_datetime, node, price
    """
    sql = f'''
        SET timezone = 'GMT';
        SELECT forecast_datetime, node, price FROM public.forecasted_price
        WHERE forecast_datetime::DATE = (\'{current_date + timedelta(days=1)}\'::DATE)
        AND node = \'{node}\';
       '''
    return pd.read_sql(sql, CONNECTION_STRING)


def get_historical_price_forecast(current_date: date, node: str):
    """Get historical day-ahead price forecasts for the provided node

    It can be assumed that forecasts are only made once per analysis_date and that each set of forecasts for
    that analysis_date corresponds to the 24 hours of the next day. It can also be assumed that each node will
    have a forecast.

    Args:
        current_date: Get all price forecasts from before this date
        node: The name of the node to get forecasts for

    Returns:
        DataFrame with columns: forecast_datetime, node, price
    """
    sql = f'''
        SET timezone = 'GMT';
        SELECT forecast_datetime, node, price FROM public.forecasted_price
        WHERE analysis_datetime < \'{current_date}\'
        AND node = \'{node}\'
       '''
    return pd.read_sql(sql, CONNECTION_STRING)


def get_historical_price(current_date: date, node: str):
    """Get the observed historical prices for the node

    It can be assumed that only one historical price exists per node per hour

    Args:
        current_date: Get all observed prices up to and including this date
        node: The name of the node to get observed price points for

    Returns:
        DataFrame with columns: observed_datetime, node, price
    """
    sql = f'''
        SET timezone = 'GMT';
        SELECT observed_datetime, node, price FROM public.observed_price
        WHERE observed_datetime < (\'{current_date + timedelta(days=1)}\'::date)
        AND node = \'{node}\'
       '''
    return pd.read_sql(sql, CONNECTION_STRING)
