# update_prices_tiingo.py
import os, sys, json, time, uuid
import datetime as dt
from zoneinfo import ZoneInfo

import requests
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# ---------- Config ----------
TICKER_MAP_FILE = "ticker_map.csv"        # optional: columns: ticker,tiingo_ticker
UPSERT_CHUNK = 1000
NY_TZ = ZoneInfo("America/New_York")
INCREMENTAL_BUFFER_DAYS = 1               # re-fetch a small window to catch late adj.

# ---------- Setup ----------
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_ANON_KEY"]
TIINGO_TOKEN = os.environ["TIINGO_TOKEN"]
FORCE_REBUILD_ENV = (os.environ.get("FORCE_REBUILD") or "").strip()

if not TIINGO_TOKEN:
    raise SystemExit("Missing TIINGO_TOKEN in environment.")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

session = requests.Session()
session.headers.update({"Accept": "application/json"})

RUN_ID = str(uuid.uuid4())

# ---------- Helpers ----------
#def load_tickers(path=TICKERS_FILE):
#    with open(path, "r") as f:
#        lines = [ln.strip() for ln in f]
#    out = []
#    for ln in lines:
#        if not ln or ln.startswith("#"):
#            continue
#        out.append(ln.upper())
#    return out

def load_tickers_from_db() -> list[str]:
    """Load ticker symbols directly from the Supabase 'tickers' table."""
    try:
        res = sb.table("tickers").select("symbol").execute()
        if not res.data:
            print("[ERROR] No tickers found in database table 'tickers'.", file=sys.stderr)
            sys.exit(1)
        tickers = [r["symbol"].strip().upper() for r in res.data if r.get("symbol")]
        print(f"[INFO] Loaded {len(tickers)} tickers from database.")
        return tickers
    except Exception as e:
        print(f"[ERROR] Failed to load tickers from Supabase: {e}", file=sys.stderr)
        sys.exit(1)

def load_ticker_map(path=TICKER_MAP_FILE):
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    mp = {}
    for _, row in df.iterrows():
        mp[str(row["ticker"]).upper()] = str(row["tiingo_ticker"]).strip()
    return mp

TICKER_MAP = load_ticker_map()

def vendor_symbol(ticker: str) -> str:
    return TICKER_MAP.get(ticker.upper(), ticker.upper())

def json_rows(df: pd.DataFrame) -> list:
    return json.loads(df.to_json(orient="records"))

def get_last_date(ticker: str):
    r = (sb.table("prices_daily")
          .select("dt")
          .eq("ticker", ticker.upper())
          .order("dt", desc=True)
          .limit(1)
          .execute())
    if not r.data:
        return None
    return dt.datetime.strptime(r.data[0]["dt"], "%Y-%m-%d").date()

def normalize_prices_df(df: pd.DataFrame, ticker: str, source: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    # Tiingo returns ISO timestamps in 'date'
    df["dt"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    if "adjClose" not in df.columns:
        df["adjClose"] = df.get("adj_close", df["close"])
    df.rename(columns={
        "open": "open", "high": "high", "low": "low", "close": "close",
        "adjClose": "adj_close", "volume": "volume",
    }, inplace=True)
    df["ticker"] = ticker.upper()
    df["source"] = source
    keep = ["ticker","dt","open","high","low","close","adj_close","volume","source"]
    for col in keep:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[keep]
    df = df[~df["adj_close"].isna()]
    return df

def _tiingo_get(url: str, params: dict, max_retries=5) -> requests.Response:
    """Handle polite retries on 429/5xx."""
    for attempt in range(max_retries):
        r = session.get(url, params=params, timeout=60)
        if r.status_code not in (429, 500, 502, 503, 504):
            return r
        sleep_s = min(2 ** attempt, 30)
        print(f"[WARN] {url} retry {attempt+1}/{max_retries} (status {r.status_code}); sleeping {sleep_s}s")
        time.sleep(sleep_s)
    # Last attempt result:
    r.raise_for_status()
    return r

def fetch_tiingo_range(ticker: str, start: dt.date, end_exclusive: dt.date) -> pd.DataFrame:
    vend = vendor_symbol(ticker)
    end_inclusive = (end_exclusive - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.tiingo.com/tiingo/daily/{vend}/prices"
    params = {
        "startDate": start.strftime("%Y-%m-%d"),
        "endDate": end_inclusive,
        "format": "json",
        "token": TIINGO_TOKEN,
    }
    r = _tiingo_get(url, params)
    if r.status_code == 404:
        print(f"[WARN] {ticker}: 404 from Tiingo (symbol not found?)")
        return pd.DataFrame()
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    return normalize_prices_df(df, ticker, "tiingo")

def fetch_tiingo_max(ticker: str) -> pd.DataFrame:
    vend = vendor_symbol(ticker)
    today_ny = dt.datetime.now(NY_TZ).date()
    url = f"https://api.tiingo.com/tiingo/daily/{vend}/prices"
    params = {
        "startDate": "1900-01-01",
        "endDate": today_ny.strftime("%Y-%m-%d"),
        "format": "json",
        "token": TIINGO_TOKEN,
    }
    r = _tiingo_get(url, params)
    if r.status_code == 404:
        print(f"[WARN] {ticker}: 404 from Tiingo (symbol not found?)")
        return pd.DataFrame()
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    return normalize_prices_df(df, ticker, "tiingo")

def upsert_df(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    rows = json_rows(df)
    total = 0
    for i in range(0, len(rows), UPSERT_CHUNK):
        sb.table("prices_daily").upsert(
            rows[i:i+UPSERT_CHUNK], on_conflict="ticker,dt"
        ).execute()
        total += len(rows[i:i+UPSERT_CHUNK])
    return total

def log_ticker_result(
    ticker: str,
    source: str,
    fetch_start: dt.date | None,
    fetch_end_excl: dt.date | None,
    rows: int,
    status: str,
    error_message: str | None = None
):
    """Safely log each ticker’s outcome to prices_daily_log (stringify dates)."""
    fetch_end = (fetch_end_excl - dt.timedelta(days=1)) if fetch_end_excl else None

    payload = {
        "run_id": RUN_ID,
        "ticker": ticker.upper(),
        "source": source,
        "fetch_start": fetch_start.isoformat() if isinstance(fetch_start, dt.date) else None,
        "fetch_end": fetch_end.isoformat() if isinstance(fetch_end, dt.date) else None,
        "rows_upserted": rows,
        "status": status,
        "error_message": error_message,
    }

    sb.table("prices_daily_log").insert(payload).execute()


def parse_force_rebuild(env_val: str) -> tuple[bool, set[str]]:
    if not env_val:
        return False, set()
    v = env_val.strip().upper()
    if v in {"ALL", "*", "TRUE", "YES", "1"}:
        return True, set()
    syms = {s.strip().upper() for s in v.split(",") if s.strip()}
    return False, syms

# ---------- Main ----------
def main():
    tickers = load_tickers_from_db()
    if len(sys.argv) > 1:
        tickers = [sys.argv[1].upper()]
        print(f"[INFO] Single-ticker update: {tickers[0]}")

    force_all, force_set = parse_force_rebuild(FORCE_REBUILD_ENV)
    today = dt.datetime.now(NY_TZ).date()
    end_exclusive = today + dt.timedelta(days=1)

    for t in tickers:
        try:
            force = force_all or (t in force_set)
            last = get_last_date(t)

            if last is None or force:
                # Full MAX backfill (first seen or forced rebuild)
                df = fetch_tiingo_max(t)
                n = upsert_df(df)
                log_ticker_result(t, "tiingo",
                                  fetch_start=dt.date(1900,1,1),
                                  fetch_end_excl=end_exclusive,
                                  rows=n, status="ok")
                tag = "forced MAX" if force and last is not None else "initial MAX"
                print(f"[OK] {t}: {tag} backfill upserted {n} rows (through {today})")

            else:
                # Incremental from last-1 day to today
                start = max(last - dt.timedelta(days=INCREMENTAL_BUFFER_DAYS), dt.date(1900, 1, 1))
                if start >= end_exclusive:
                    log_ticker_result(t, "tiingo", start, end_exclusive, 0, status="skip")
                    print(f"[SKIP] {t} already up to date (last={last})")
                    continue
                df = fetch_tiingo_range(t, start, end_exclusive)
                n = upsert_df(df)
                log_ticker_result(t, "tiingo", start, end_exclusive, n, status="ok")
                print(f"[OK] {t}: upserted {n} rows from {start} to {today} (last was {last})")

            # be polite to the API
            time.sleep(0.1)

        except Exception as e:
            # record the error but keep going
            try:
                log_ticker_result(t, "tiingo", fetch_start=None, fetch_end_excl=None,
                                  rows=0, status="err", error_message=str(e))
            except Exception:
                pass
            print(f"[ERR] {t}: {repr(e)}", file=sys.stderr)

if __name__ == "__main__":
    main()
