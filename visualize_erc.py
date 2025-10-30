# visualize_erc.py
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

OUTDIR = Path("outputs")
SCENARIOS = {
    "ledoit_wolf": OUTDIR / "erc_ledoit_wolf_pretty.csv",
    "winsor_lw":   OUTDIR / "erc_winsor_lw_pretty.csv",     # optional
    "blend_70_30": OUTDIR / "erc_blend_70_30_pretty.csv"    # optional
}

# --- Edit this cluster map to your liking ---
CLUSTERS = {
    # Payments / Fintech
    "MA": "Payments", "V": "Payments", "FOUR": "Payments", "FICO": "Payments",
    # Index / Ratings / Market Infra
    "SPGI": "Index/Ratings", "MCO": "Index/Ratings", "MSCI": "Index/Ratings",
    "ICE": "Market Infra", "TW": "Market Infra", "MKTX": "Market Infra",
    # EDA / Semis
    "SNPS": "EDA/Semis", "CDNS": "EDA/Semis", "ASML": "EDA/Semis", "TSM": "EDA/Semis",
    # Enterprise Software
    "NOW": "Enterprise SW", "WDAY": "Enterprise SW", "ADSK": "Enterprise SW", "TYL": "Enterprise SW",
    # MedTech / Bio
    "ISRG": "MedTech/Bio", "DHR": "MedTech/Bio", "MRVI": "MedTech/Bio",
    # Real Estate / Info Services
    "CSGP": "Info Services",
    # Intl / Other
    "6861.T": "Intl/Other",
    "VACNY": "Intl/Other"
}

def print_cluster_members():
    print("\n[Cluster Memberships]")
    cluster_map = {}
    for t, c in CLUSTERS.items():
        cluster_map.setdefault(c, []).append(t)
    for c, tickers in cluster_map.items():
        print(f"{c:15s}: {', '.join(sorted(tickers))}")

def load_scenario(path: Path) -> pd.DataFrame:
    """
    Returns df with columns: weight_%, risk_share_%, risk_contrib_vol
    Index is ticker.
    """
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, index_col=0)
    need = {"weight_%", "risk_share_%", "risk_contrib_vol"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"{path.name} missing columns: {missing}")
    return df

def apply_clusters(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    tickers = df.index.tolist()
    df["cluster"] = [CLUSTERS.get(t, "Other") for t in tickers]
    return df

def bar_weights_vs_risk(df: pd.DataFrame, title: str, fname: str):
    if df.empty:
        return
    dfp = df.copy().sort_values("risk_share_%", ascending=False)
    x = np.arange(len(dfp.index))
    w = 0.4
    plt.figure(figsize=(14, 6))
    plt.bar(x - w/2, dfp["weight_%"].values, width=w, label="Weight %")
    plt.bar(x + w/2, dfp["risk_share_%"].values, width=w, label="Risk Share %")
    plt.xticks(x, dfp.index, rotation=60, ha="right")
    plt.title(title)
    plt.ylabel("Percent")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTDIR / fname, dpi=150)
    plt.close()

# ---------- NEW: helpers to put tickers INSIDE bar segments ----------

def tickers_by_cluster_for_scenario(df: pd.DataFrame) -> dict:
    """Return {cluster: [tickers...]} for the given scenario DataFrame (index=tickers)."""
    lab = {}
    for cl, g in df.groupby("cluster"):
        lab[cl] = sorted(g.index.tolist())
    return lab

def wrap_tickers(tickers, per_line=3):
    """Wrap tickers into multiple lines: 'A, B, C\\nD, E, F' to fit inside a segment."""
    lines = []
    for i in range(0, len(tickers), per_line):
        lines.append(", ".join(tickers[i:i+per_line]))
    return "\n".join(lines)

# --------------------------------------------------------------------

def cluster_stacked_bars(dfs: dict, title: str, fname: str):
    """
    dfs: dict name -> DataFrame (with 'cluster' and 'risk_contrib_vol')
    Produces a stacked bar of risk_contrib_vol by cluster across scenarios,
    and annotates each segment with that scenario's tickers for the cluster.
    """
    # Build a combined cluster x scenario table of absolute contributions
    rows = []
    per_scen_labels = {}  # scenario -> {cluster: "T1, T2, ..."}
    for scen, df in dfs.items():
        if df.empty:
            continue
        g = df.groupby("cluster")["risk_contrib_vol"].sum()
        for cl, val in g.items():
            rows.append({"scenario": scen, "cluster": cl, "rc_vol": float(val)})
        # build per-scenario labels
        per_scen_labels[scen] = {cl: wrap_tickers(tks, per_line=3)
                                 for cl, tks in tickers_by_cluster_for_scenario(df).items()}

    if not rows:
        return

    tab = pd.DataFrame(rows)
    piv = tab.pivot_table(index="cluster", columns="scenario",
                          values="rc_vol", aggfunc="sum").fillna(0.0)
    piv = piv.sort_index()  # alphabetical clusters

    # Save a CSV summary too
    piv.to_csv(OUTDIR / "erc_cluster_risk_contrib_vol.csv")

    scenarios = list(piv.columns)
    clusters = list(piv.index)
    ind = np.arange(len(scenarios))
    bottom = np.zeros(len(scenarios))

    plt.figure(figsize=(12, 6))
    # draw stacked bars
    for cl in clusters:
        vals = piv.loc[cl, :].values
        bars = plt.bar(ind, vals, bottom=bottom, label=cl)
        # annotate each scenario's segment with tickers for that cluster
        for i, b in enumerate(bars):
            scen = scenarios[i]
            h = b.get_height()
            if h <= 0:
                continue
            # Skip very thin segments to avoid clutter
            if h < 0.01:  # ~1% vol units threshold; adjust if needed
                bottom[i] += h
                continue
            tickers_label = per_scen_labels.get(scen, {}).get(cl, cl)
            # center text vertically within the segment
            y = b.get_y() + h / 2.0
            plt.text(b.get_x() + b.get_width()/2.0, y, tickers_label,
                     ha="center", va="center", fontsize=8)
        bottom += vals

    plt.title(title)
    plt.xticks(ind, scenarios, rotation=0)
    plt.ylabel("Absolute Risk Contribution (volatility units)")
    # Keep legend for colors -> cluster names (tickers are printed inside bars)
    plt.legend(loc="best", ncols=2, fontsize=9, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(OUTDIR / fname, dpi=150)
    plt.close()

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print_cluster_members()

    # Load scenarios (skip missing ones)
    data = {}
    for scen, path in SCENARIOS.items():
        df = load_scenario(path)
        if not df.empty:
            df = apply_clusters(df)
            data[scen] = df

    if not data:
        print("[WARN] No ERC files found in outputs/. Run compute_erc.py first.")
        return

    # Per-scenario: Weights vs Risk Shares plot
    for scen, df in data.items():
        title = f"Weights vs Risk Shares — {scen}"
        fname = f"viz_weights_vs_risk_{scen}.png"
        bar_weights_vs_risk(df, title, fname)
        print(f"[OK] Saved {fname}")

    # Cross-scenario: Stacked bars of cluster risk contributions WITH TICKERS INSIDE
    cluster_stacked_bars(
        data,
        "Risk Contributions by Cluster (absolute, across scenarios)",
        "viz_cluster_risk_contribs.png"
    )
    print("[OK] Saved viz_cluster_risk_contribs.png")

if __name__ == "__main__":
    main()
