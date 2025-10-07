# seed_prices.py
import os, datetime as dt, json, sys
from typing import List
import pandas as pd
import yfinance as yf
from tenacity import retry, wait_exponential, stop_after_attempt
from supabase import create_client
from dotenv import load_dotenv

# ---------- Config ----------
HISTORY_YEARS = 5           # how many years to backfill
TICKERS_FILE = "tickers.txt"  # one symbol per line, e.g., AAPL

# ---------- Helpers ----------
def load_tickers(path: str = TICKERS_FILE) -> List[str]:
    if not os.path.exists(path):
        print(f"[ERROR] '{path}' not found. Create it with one ticker per line.", file=sys.stderr)
        sys.exit(1)
    with open(path, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
    if not tickers:
        print(f"[ERROR] '{path}' is empty. Add at least one ticker.", file=sys.stderr)
        sys.exit(1)
    return tickers

def json_rows(df: pd.DataFrame) -> list:
    # Convert DataFrame to JSON-safe list[dict] (NaN->null, numpy types->native)
    return json.loads(df.to_json(orient="records"))

# ---------- Supabase client ----------
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]  # use Service Role key
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Date range ----------
END = dt.date.today()
START = END - dt.timedelta(days=HISTORY_YEARS * 365)

@retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5))
def fetch_history(ticker: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=START,
        end=END,
        auto_adjust=False,
        progress=False,
        threads=False
    )
    if df.empty:
        return df

    # yfinance can return MultiIndex columns like ('Adj Close','AAPL')
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

    # Dates as strings so payload is JSON-serializable
    df["dt"] = pd.to_datetime(df["dt"]).dt.strftime("%Y-%m-%d")
    df["ticker"] = ticker.upper()
    df["source"] = "yfinance"

    # Drop rows with missing adjusted close
    df = df[~df["adj_close"].isna()]

    # Keep only required columns in correct order
    return df[["ticker", "dt", "open", "high", "low", "close", "adj_close", "volume", "source"]]

def upsert_df(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    rows = json_rows(df)
    total = 0
    chunk = 1000
    for i in range(0, len(rows), chunk):
        sb.table("prices_daily").upsert(rows[i:i+chunk], on_conflict="ticker,dt").execute()
        total += len(rows[i:i+chunk])
    return total

def main():
    tickers = load_tickers()

    # allow optional single-ticker run, e.g. python seed_prices.py AAPL
    if len(sys.argv) > 1:
        tickers = [sys.argv[1].upper()]
        print(f"[INFO] Running single-ticker seed: {tickers[0]}")

    print(f"[INFO] Backfilling ~{HISTORY_YEARS}y for {len(tickers)} tickers ({START} → {END})")

    for t in tickers:
        try:
            df = fetch_history(t)
        except Exception as e:
            print(f"[ERROR] fetch failed for {t}: {e}", file=sys.stderr)
            continue

        if df.empty:
            print(f"[WARN] No data for {t} (yfinance returned empty).")
            continue

        try:
            n = upsert_df(df)
            print(f"[OK] Seeded {t}: {n} rows")
        except Exception as e:
            print(f"[ERROR] upsert failed for {t}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
