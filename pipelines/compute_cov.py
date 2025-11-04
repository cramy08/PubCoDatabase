# compute_cov.py
import os, sys, json, datetime as dt
import numpy as np
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

# --------- Config ---------
TICKERS_FILE = "tickers.txt"            # one ticker per line
YEARS = 3                               # how many years to pull for the cov calc
ANNUALIZATION_FACTOR = 252              # trading days per year

USE_LEDOIT_WOLF = True                  # set False if you didn't install scikit-learn
HALFLIFE_EWMA = 21                      # ~1 month; change to 60/126 for smoother EWMA
# --------------------------

def load_tickers(path=TICKERS_FILE):
    with open(path, "r") as f:
        return [line.strip().upper() for line in f if line.strip()]

def get_client():
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)

def fetch_adj_close(sb, tickers, start_dt, end_dt):
    """
    Pull adj_close for all tickers between start_dt and end_dt (inclusive).
    Returns a wide DataFrame: index=dt (datetime), columns=tickers, values=adj_close.
    """
    frames = []
    for t in tickers:
        r = (
            sb.table("prices_daily")
              .select("dt, adj_close")
              .eq("ticker", t)
              .gte("dt", start_dt.strftime("%Y-%m-%d"))
              .lte("dt", end_dt.strftime("%Y-%m-%d"))
              .order("dt", desc=False)
              .execute()
        )
        df = pd.DataFrame(r.data)
        if df.empty:
            print(f"[WARN] No data for {t} in range {start_dt}..{end_dt}")
            continue
        df["dt"] = pd.to_datetime(df["dt"])
        df = df.rename(columns={"adj_close": t}).set_index("dt")[[t]]
        frames.append(df)

    if not frames:
        raise SystemExit("[ERROR] No data retrieved for any ticker.")
    # Inner-join on dates so all columns share the same rows (avoid look-ahead bias)
    wide = pd.concat(frames, axis=1, join="inner").sort_index()
    # Drop any residual NaNs (if any)
    wide = wide.dropna(how="any")
    return wide

def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return np.log(prices).diff().dropna(how="any")

def sample_cov(returns: pd.DataFrame, annualize=True, af=ANNUALIZATION_FACTOR) -> pd.DataFrame:
    cov_d = returns.cov()     # daily sample covariance
    return cov_d * af if annualize else cov_d

def ewma_cov(returns: pd.DataFrame, halflife=HALFLIFE_EWMA, af=ANNUALIZATION_FACTOR):
    """
    Pairwise EWMA covariance via pandas ewm on raw returns with bias correction.
    For small universes this loop is fine; for larger use vectorized methods.
    """
    cols = returns.columns
    cov_mat = pd.DataFrame(np.zeros((len(cols), len(cols))), index=cols, columns=cols)
    for i, ci in enumerate(cols):
        for j, cj in enumerate(cols):
            prod = (returns[ci] * returns[cj]).ewm(halflife=halflife, adjust=False).mean()
            mi = returns[ci].ewm(halflife=halflife, adjust=False).mean()
            mj = returns[cj].ewm(halflife=halflife, adjust=False).mean()
            cov_ij = (prod - mi * mj).iloc[-1]    # last EWMA estimate
            cov_mat.iloc[i, j] = cov_ij
    return cov_mat * af

def ledoit_wolf_cov(returns: pd.DataFrame, af=ANNUALIZATION_FACTOR):
    try:
        from sklearn.covariance import LedoitWolf
    except Exception as e:
        raise RuntimeError("scikit-learn not installed. Run: pip install scikit-learn") from e
    lw = LedoitWolf().fit(returns.values)
    cov = pd.DataFrame(lw.covariance_, index=returns.columns, columns=returns.columns)
    return cov * af

def main():
    # load tickers and time window
    tickers = load_tickers()
    end_dt = dt.date.today()
    start_dt = end_dt - dt.timedelta(days=int(YEARS * 365))

    print(f"[INFO] Building covariance from adj_close for {len(tickers)} tickers")
    print(f"[INFO] Window: {start_dt} → {end_dt} (~{YEARS}y)")
    sb = get_client()

    # 1) prices → 2) returns
    prices = fetch_adj_close(sb, tickers, start_dt, end_dt)
    print(f"[INFO] Prices shape: {prices.shape} (rows=trading days, cols=tickers)")
    rets = compute_log_returns(prices)
    print(f"[INFO] Returns shape: {rets.shape}")

    # 3) sample covariance (daily and annualized)
    cov_annual = sample_cov(rets, annualize=True)
    cov_daily  = sample_cov(rets, annualize=False)

    # Prepare output dir early (so we can save correlation too)
    outdir = "outputs"
    os.makedirs(outdir, exist_ok=True)

    # --- Correlation matrix from cov_annual ---
    std = np.sqrt(np.diag(cov_annual.values))
    # Guard against zero std (avoid divide-by-zero)
    std = np.where(std == 0.0, np.finfo(float).eps, std)
    corr_vals = cov_annual.values / np.outer(std, std)
    corr = pd.DataFrame(corr_vals, index=cov_annual.index, columns=cov_annual.columns)
    corr.to_csv(os.path.join(outdir, "corr_annual.csv"))

    # Rank pairs by correlation (exclude diagonal)
    pairs = []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((cols[i], cols[j], float(corr.iloc[i, j])))
    pairs_sorted = sorted(pairs, key=lambda x: x[2], reverse=True)

    print("\nTop 10 correlations:")
    for a, b, r in pairs_sorted[:10]:
        print(f"{a}-{b}: {r:.3f}")

    print("\nBottom 10 correlations:")
    for a, b, r in sorted(pairs, key=lambda x: x[2])[:10]:
        print(f"{a}-{b}: {r:.3f}")

    # 4) optional EWMA and Ledoit–Wolf (annualized)
    cov_ewma = ewma_cov(rets)  # annualized
    cov_lw   = None
    if USE_LEDOIT_WOLF:
        try:
            cov_lw = ledoit_wolf_cov(rets)
        except Exception as e:
            print(f"[WARN] Ledoit-Wolf skipped: {e}")

    # Save core outputs
    prices.to_csv(os.path.join(outdir, "prices_adj_close.csv"))
    rets.to_csv(os.path.join(outdir, "returns_log_daily.csv"))
    cov_daily.to_csv(os.path.join(outdir, "cov_daily.csv"))
    cov_annual.to_csv(os.path.join(outdir, "cov_annual.csv"))
    cov_ewma.to_csv(os.path.join(outdir, f"cov_annual_ewma_hl{HALFLIFE_EWMA}.csv"))
    if cov_lw is not None:
        cov_lw.to_csv(os.path.join(outdir, "cov_annual_ledoit_wolf.csv"))

    # Small on-screen summary
    print("\n[SUMMARY]")
    print("Tickers:", ", ".join(rets.columns))
    print("Covariance (annualized) – top-left 5x5:")
    print(cov_annual.iloc[:5, :5].round(6))

if __name__ == "__main__":
    main()
