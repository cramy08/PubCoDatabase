# update_prices.py
import os, datetime as dt, json, sys
import pandas as pd
import yfinance as yf
from supabase import create_client
from dotenv import load_dotenv

TICKERS_FILE = "tickers.txt"  # one ticker per line

def load_tickers(path=TICKERS_FILE):
    with open(path, "r") as f:
        return [line.strip().upper() for line in f if line.strip()]

def json_rows(df: pd.DataFrame) -> list:
    return json.loads(df.to_json(orient="records"))

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

def get_last_date(ticker: str):
    r = (
        sb.table("prices_daily")
          .select("dt")
          .eq("ticker", ticker.upper())
          .order("dt", desc=True)
          .limit(1)
          .execute()
    )
    if not r.data:
        return None
    # r.data[0]["dt"] is "YYYY-MM-DD"
    return dt.datetime.strptime(r.data[0]["dt"], "%Y-%m-%d").date()

def fetch_since(ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=start,
        end=end,          # yfinance end is exclusive
        auto_adjust=False,
        progress=False,
        threads=False
    )
    if df.empty:
        return df

    # Flatten possible MultiIndex like ('Adj Close','AAPL')
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(c[0]) for c in df.columns]

    df = df.reset_index().rename(columns={
        "Date": "dt",
        "Open": "open",
        "High": "high",
        "Low":  "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume"
    })
    df["dt"] = pd.to_datetime(df["dt"]).dt.strftime("%Y-%m-%d")
    df["ticker"] = ticker.upper()
    df["source"] = "yfinance"
    df = df[~df["adj_close"].isna()]
    return df[["ticker","dt","open","high","low","close","adj_close","volume","source"]]

def upsert_df(df: pd.DataFrame) -> int:
    if df.empty:
        return
