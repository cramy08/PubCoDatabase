import pandas as pd
from utils.db import get_supabase
from utils.factors import ensure_factor, upsert_factor_values

LOOKBACK = 252

def fetch_basket_returns(sb, slug: str) -> pd.DataFrame:
    res = sb.rpc("exec_sql", {  # or use .table("...").select() on v_basket_returns if exposed
        "sql": f"SELECT dt, ew_r1d FROM v_basket_returns WHERE slug = '{slug}' ORDER BY dt;"
    }).execute()
    df = pd.DataFrame(res.data)
    return df

def add_rolls(df: pd.DataFrame) -> pd.DataFrame:
    s = df["ew_r1d"]
    df["mean_r1d_252"] = s.rolling(LOOKBACK).mean()
    df["std_r1d_252"]  = s.rolling(LOOKBACK).std(ddof=0)
    df["z_r1d_252"]    = (s - df["mean_r1d_252"]) / df["std_r1d_252"]
    return df

def run(slug: str):
    sb = get_supabase()
    df = fetch_basket_returns(sb, slug)
    if df.empty:
        print(f"No data for {slug}")
        return
    df = add_rolls(df)

    factor_slug = f"basket:{slug}:r1d"
    ensure_factor(factor_slug, name=f"{slug} EW R1D", category="basket", method="ew_r1d")
    rows = [
        {
          "slug": factor_slug,
          "dt": r.dt,
          "r_1d": r.ew_r1d,
          "mean_r1d_252": r.mean_r1d_252,
          "std_r1d_252": r.std_r1d_252,
          "z_r1d_252": r.z_r1d_252,
          "source": "db"
        }
        for r in df.itertuples(index=False)
    ]
    upsert_factor_values(factor_slug, rows)

if __name__ == "__main__":
    for slug in ["vertical_software","semi_cap"]:
        run(slug)
