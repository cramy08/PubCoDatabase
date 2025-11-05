import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import matplotlib.pyplot as plt
from utils.db import get_supabase
from utils.factors import ensure_factor, upsert_factor_values


# -------------------------------
# Fetch average basket prices
# -------------------------------
def fetch_basket_prices(sb, slug):
    # Step 1: Get tickers for this basket
    tickers_res = sb.table("basket_members").select("ticker").eq("slug", slug).execute()
    tickers = [r["ticker"] for r in tickers_res.data]
    if not tickers:
        raise ValueError(f"No tickers found for basket '{slug}'")

    # Step 2: Fetch prices for those tickers
    prices_res = sb.table("prices_daily") \
                   .select("ticker, dt, adj_close") \
                   .in_("ticker", tickers) \
                   .execute()
    df = pd.DataFrame(prices_res.data)
    if df.empty:
        raise ValueError(f"No price data found for basket '{slug}'")

    # Step 3: Average prices per day for the basket
    df = df.groupby("dt", as_index=False)["adj_close"].mean()
    df.rename(columns={"adj_close": "avg_price"}, inplace=True)
    return df

# -------------------------------
# Compute spread and returns
# -------------------------------
def compute_spread(df_a, df_b):
    df = pd.merge(df_a, df_b, on="dt", suffixes=("_a", "_b"))
    df["spread"] = 100 * df["avg_price_a"] / df["avg_price_b"]
    df["r_1d"] = df["spread"].pct_change()
    df["r_20d"] = df["spread"].pct_change(20)
    df["r_60d"] = df["spread"].pct_change(60)
    df["r_252d"] = df["spread"].pct_change(252)
    return df

# -------------------------------
# Add rolling mean/std/z-score
# -------------------------------
def add_zscore(df, window=252):
    df["rolling_mean"] = df["r_20d"].rolling(window).mean()
    df["rolling_std"] = df["r_20d"].rolling(window).std()
    df["z_20v252"] = (df["r_20d"] - df["rolling_mean"]) / df["rolling_std"]
    return df
# -------------------------------
# Visualization helper
# -------------------------------
def plot_spread(df, pair_a, pair_b):
    plt.figure(figsize=(12, 6))
    plt.plot(df["dt"], df["z_20v252"], label="Z-score")
    plt.axhline(1.96, color="red", linestyle="--")
    plt.axhline(-1.96, color="red", linestyle="--")
    plt.title(f"Z-Score: {pair_a} vs {pair_b}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"outputs/{pair_a}_vs_{pair_b}_zscore.png", dpi=150)
    plt.close()

    plt.figure(figsize=(12, 6))
    plt.plot(df["dt"], df["r_20d"], label="20-Day Return")
    plt.axhline(df["r_20d"].mean(), color="orange", linestyle="--", label="Mean (252d)")
    plt.axhline(df["r_20d"].mean() + 2*df["r_20d"].std(), color="red", linestyle="--", label="+2σ")
    plt.axhline(df["r_20d"].mean() - 2*df["r_20d"].std(), color="red", linestyle="--", label="-2σ")
    plt.title(f"20-Day Return: {pair_a} vs {pair_b}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"outputs/{pair_a}_vs_{pair_b}_returns.png", dpi=150)
    plt.close()

    print(f"📊 Charts saved for {pair_a}_vs_{pair_b}")

# -------------------------------
# Main entry
# -------------------------------
if __name__ == "__main__":
    pairs = [
        ("vertical_software", "semi_cap"),
        ("healthcare_tools", "card_networks"),
        ("merchant_acquirers", "info_services"),
    ]

if __name__ == "__main__":
    import os
    from datetime import datetime

    # create /outputs folder if it doesn't exist
    os.makedirs("outputs", exist_ok=True)

    # optionally: give each daily run its own Excel file
    output_path = f"outputs/bucket_spreads_{datetime.now():%Y-%m-%d}.xlsx"

    pairs = [
        ("vertical_software", "semi_cap"),
        ("healthcare_tools", "card_networks"),
        ("merchant_acquirers", "info_services"),
    ]

    for a, b in pairs:
        sb = get_supabase()
        try:
            df_a = fetch_basket_prices(sb, a)
            df_b = fetch_basket_prices(sb, b)
        except ValueError as e:
            print(f"⚠️ Skipping pair {a}_vs_{b}: {e}")
            continue
        df = compute_spread(df_a, df_b)
        df = add_zscore(df)
        plot_spread(df, a, b)

        # --- Excel export logic ---
        if os.path.exists(output_path):
            mode = "a"  # append if file already exists
        else:
            mode = "w"  # create new workbook

        with pd.ExcelWriter(
            output_path,
            mode=mode,
            engine="openpyxl",
            if_sheet_exists="replace" if mode == "a" else None
        ) as writer:
            df.to_excel(writer, sheet_name=f"{a}_vs_{b}", index=False)

        print(f"✅ Saved sheet '{a}_vs_{b}' to {output_path}")

