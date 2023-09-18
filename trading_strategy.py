import db_backend
import os
import argparse
import pandas as pd
from datetime import time, datetime, date



class TradingStrategy:
    @staticmethod
    def get_trade_recommendations(current_date: date, node: str,
                                                       num_simulations: int) -> pd.DataFrame:
        """Recommend day-ahead trades for the provided node

        Args:
            current_date: The date to make day-ahead trades for
            node: The node to base trades around
            num_simulations: The number of simulations to use when making price forecasts

        Returns:
            DataFrame with columns: forecast_datetime, sink
        """
        df = TradingStrategy.generate_price_forecast_df(current_date, num_simulations)
        return TradingStrategy.get_most_profitable_sinks(node, df)


    @staticmethod
    def generate_price_forecast_df(current_date: date, num_simulations: int) -> pd.DataFrame():
        """Generate a price forecast df by randomly sampling from the forecasts historical range of errors

        Args:
            current_date: The date to generate day-ahead forecasts for
            num_simulations: The number of simulations to use when generating price forecasts

        Returns:
            Dataframe with columns: forecast_datetime, price_forecast, sim_number

        """
        all_nodes = db_backend.get_all_online_nodes(current_date)
        for node in all_nodes:
            historical_observed = db_backend.get_historical_price(current_date, node)
            recent_forecast = db_backend.get_recent_price_forecast(current_date, node)
            historical_forecasted = db_backend.get_historical_price_forecast(current_date, node)
        # TODO:
        # For each node, compute the maximum error as the delta between the node's observed price and its
        # forecasted price. Then for each simulation generate a random price forecast for each node that is
        # within the range of the maximum error for that node from its current price forecast. The length of
        # this output dataframe should be: num_online_nodes * 24 (number of hours forecasted) * num_simulations
        raise NotImplementedError


    @staticmethod
    def get_most_profitable_sinks(node, price_forecast_df) -> pd.DataFrame:
        """Recommend hourly day-ahead trades on the most profitable sinks for the provided node

        Args:
            node: The node to recommend trades for
            price_forecast_df: Dataframe of price forecasts to use for informing the trades to make

        Returns:
            DataFrame with columns: forecast_datetime, sink
        """
        # TODO:
        # The provided node will be referred to below as the "source" whereas all other nodes in the dataframe
        # will be referred to as "sinks".
        #
        # Trade recommendations should be made using the following criteria:
        # - The average price of the source across all sims for a given hour < average price of a sink across all
        #   sims for that hour
        # - The max price of the source for any sim for a given hour cannot be more than 3x the min price of the
        #   sink for any simulation for that same hour
        # - The top 3 sinks (or fewer if not enough meet the above criteria) per hour should be selected. The top trades are
        #   defined as those with the largest delta between source and sink when averaging across all sims for the given hour
        # 
        # The output dataframe should have a length of at most: 24 (number of hours forecasted) * 3 (top sinks) 
        raise NotImplementedError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', dest='current_date', action='store', required=False,
                        default=date(2023, 8, 14), help='Date to process')
    parser.add_argument('-n', dest='num_sims', action='store', required=False,
                        default=5, help='Number of simulations to use')
    parser.add_argument('--node', dest='node', action='store', required=False,
                        default='node_1', help='Name of the node for generating trades')
    args = parser.parse_args()
    if type(args.current_date) is str:
        current_date = datetime.strptime(args.current_date, '%Y-%m-%d').date()
    else:
        current_date = args.date

    TradingStrategy().get_trade_recommendations(current_date, args.node, int(args.num_sims))


if __name__ == '__main__':
    main()




