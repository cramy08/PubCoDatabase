import os, datetime as dt, json
import pandas as pd
import yfinance as yf
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

T = "AAPL"
START = (dt.date.today() - dt.timedelta(days=365*2))
END   = dt.date.today()

print("Fetching", T, START, "→", END)
df = yf.download(T, start=START, end=END, auto_adjust=False, progress=False, threads=False)

# FLATTEN possible MultiIndex columns from yfinance (e.g., ('Adj Close','AAPL'))
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [str(c[0]) for c in df.columns]

print("Raw df shape:", df.shape)
print(df.head(3))

if df.empty:
    print("No data returned from yfinance.")
    raise SystemExit(0)

df = df.reset_index().rename(columns={
    "Date":"dt","Open":"open","High":"high","Low":"low","Close":"close",
    "Adj Close":"adj_close","Volume":"volume"
})

# Dates to strings (YYYY-MM-DD) so they’re JSON-serializable
df["dt"] = pd.to_datetime(df["dt"]).dt.strftime("%Y-%m-%d")

df["ticker"] = T.upper()
df["source"] = "yfinance"
df = df[~df["adj_close"].isna()]

# Build a JSON-safe list[dict] (numbers as native types, NaN -> null)
rows = json.loads(
    df[["ticker","dt","open","high","low","close","adj_close","volume","source"]]
      .to_json(orient="records")
)

print("Prepared rows:", len(rows))
print("Upserting first 5 rows...")
sb.table("prices_daily").upsert(rows[:5], on_conflict="ticker,dt").execute()
print("Upsert done.")

# Verify a few rows
r = sb.table("prices_daily").select("ticker, dt, adj_close").eq("ticker", T).order("dt", desc=True).limit(3).execute()
print("DB sample:", r.data)
