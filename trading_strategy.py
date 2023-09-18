import db_backend
import argparse
import pandas as pd
import random
from datetime import datetime, date
import concurrent.futures
from functools import partial


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
    def generate_price_forecast(price: pd.Series, max_error: pd.Series):
        return random.uniform(price - max_error, price + max_error)

    @staticmethod
    def run_simulation_for_node(current_date: date, num_simulations: int, node: str) -> pd.DataFrame:
        ...
        historical_observed = db_backend.get_historical_price(current_date, node)
        recent_forecast = db_backend.get_recent_price_forecast(current_date, node)
        historical_forecasted = db_backend.get_historical_price_forecast(current_date, node)
        current_day = (historical_observed.merge(historical_forecasted, 
                                                left_on=["observed_datetime", "node"],
                                                right_on=["forecast_datetime", "node"], 
                                                suffixes=("_observed", "_forecasted"))
                        .query("forecast_datetime.dt.date == @current_date")
                        .copy()
                        .reset_index(drop=True)
        )

        current_day["max_error"] = abs(current_day["price_observed"] - current_day["price_forecasted"])

        tmp = pd.DataFrame()
        for sim in range(num_simulations):
            tmp["forecast_datetime"] = recent_forecast["forecast_datetime"]
            tmp["node"] = node
            tmp["price_forecast"] = TradingStrategy.generate_price_forecast(recent_forecast["price"], 
                                                                            current_day["max_error"])                 
            tmp["sim_number"] = sim + 1
        return tmp

    @staticmethod
    def generate_price_forecast_df(current_date: date, num_simulations: int) -> pd.DataFrame:
        """Generate a price forecast df by randomly sampling from the forecasts historical range of errors

        Args:
            current_date: The date to generate day-ahead forecasts for
            num_simulations: The number of simulations to use when generating price forecasts

        Returns:
            Dataframe with columns: forecast_datetime, price_forecast, sim_number

        """
        
        all_nodes = db_backend.get_all_online_nodes(current_date)
        price_forecast = pd.DataFrame()


        func = partial(TradingStrategy.run_simulation_for_node, current_date, num_simulations)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = list(executor.map(func, all_nodes))
            
        for result in results:
            price_forecast = pd.concat([price_forecast, result], ignore_index=True)

        return price_forecast




    @staticmethod
    def get_most_profitable_sinks(node: str, price_forecast_df: pd.DataFrame) -> pd.DataFrame:
        """Recommend hourly day-ahead trades on the most profitable sinks for the provided node

        Args:
            node: The node to recommend trades for
            price_forecast_df: Dataframe of price forecasts to use for informing the trades to make

        Returns:
            DataFrame with columns: forecast_datetime, sink
        """

        most_profitable_sinks = pd.DataFrame()

        for i in range(24):
            hourly = (price_forecast_df.query("forecast_datetime.dt.hour == @i")  
                .groupby(["node"])
                .agg(["mean", "min", "max"]) # get average, minimum, and maximum forecasted values over range of simulations
            )
            source = hourly.query("index == @node")
            sink_candidates = (hourly.query('@hourly.price_forecast["mean"] < @source.price_forecast["mean"].iloc[0]') # avg price of source across sims < avg price of sink(s) across sims
                            .query('@source.price_forecast["max"].iloc[0] <= @hourly.price_forecast["min"] * 3')) # max price of sim for source <= 3 * min_price of sink(s)
            sink_candidates["price_delta"] = abs(sink_candidates.price_forecast["mean"] - source.price_forecast["mean"].iloc[0]) # calculate difference between averages for remaining sinks and the source
            top_sinks = sink_candidates.sort_values(by=['price_delta'], ascending=False).head(3) # take *UP TO* top 3 sinks according to price_delta field
            most_profitable_sinks = pd.concat([most_profitable_sinks, top_sinks])

        most_profitable_sinks = (most_profitable_sinks["forecast_datetime"]["mean"]
            .to_frame()
            .reset_index()
            .rename(columns={"node": "sink","mean": "forecast_datetime"})
            .reindex(columns=["forecast_datetime", "sink"]))

        return most_profitable_sinks

def validate_arguments(date: date, num_sims: int, node: str) -> None:
    existing_nodes = db_backend.get_all_valid_nodes() 
    online_nodes = db_backend.get_all_online_nodes(date)
    valid_dates = db_backend.get_valid_dates()
    if not isinstance(num_sims, int):
        raise ValueError("must provider an integer for number of simulations to run")
    if num_sims <= 0:
        raise ValueError("provided number of simulations to run must be >= 1")
    if node not in existing_nodes:
        raise ValueError("invalid node identifier provided")
    if node not in online_nodes:
        raise ValueError("node not online")
    if not (valid_dates[0] <= date <= valid_dates[-1]):
        raise ValueError(f"invalid date provided. must be in the range [{valid_dates[0]}, {valid_dates[-1]}]")

        


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', dest='current_date', action='store', required=False,
                        default=date(2023, 8, 14), help='Date to process')
    parser.add_argument('-n', dest='num_sims', action='store', required=False,
                        default=5, help='Number of simulations to use')
    parser.add_argument('--node', dest='node', action='store', required=False,
                        default='node_1', help='Name of the node for generating trades')
    parser.add_argument('-o', dest='output', required=False, 
                        help='Name of file to output trade recommendation dataframe to')
    args = parser.parse_args()
    if type(args.current_date) is str:
        current_date = datetime.strptime(args.current_date, '%Y-%m-%d').date()
    else:
        current_date = args.date

    validate_arguments(current_date, int(args.num_sims), args.node)


    trade_recommendations = TradingStrategy().get_trade_recommendations(current_date, args.node, int(args.num_sims))
    if args.output:
        trade_recommendations.to_csv(path_or_buf=args.output, index=False)
    else:
        print(trade_recommendations)
        


if __name__ == '__main__':
    main()




