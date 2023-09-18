from typing import List
from fastapi import FastAPI
from datetime import date, datetime
import json
import time
from pydantic import BaseModel

from trading_strategy import TradingStrategy 

app = FastAPI()

class Forecast(BaseModel):
    top_sinks: List[str]
    forecast_datetime: datetime

@app.get("/trade_recommendation")
async def get_trade_recommendations(analysis_date: date, node: str, num_simulations: int) -> List[Forecast]:
    start = time.time_ns()
    analysis = (TradingStrategy.get_trade_recommendations(analysis_date, node, num_simulations)
        .groupby("forecast_datetime")["sink"]
        .apply(list)
        .reset_index()
        .rename(columns={"sink": "top_sinks"}))
    print(f"Response Time: {(time.time_ns() - start) / 1e6} ms")
    return json.loads(analysis.to_json(orient="records", date_format='iso'))
