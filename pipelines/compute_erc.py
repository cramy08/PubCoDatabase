# compute_erc.py
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

# -------- Config --------
OUTDIR = Path("outputs")
LW_FILE = OUTDIR / "cov_annual_ledoit_wolf.csv"
EWMA_FILE = OUTDIR / "cov_annual_ewma_hl21.csv"            # optional
WINSOR_FILE = OUTDIR / "cov_annual_winsor4sigma.csv"        # optional (if you created it)

RISK_SHARE_CAP = 0.10     # 10% max per-name risk share (soft penalty)
WEIGHT_CAP = None         # e.g., 0.08 to hard-cap weights; None to disable
TOL = 1e-9
MAX_ITERS = 500
# ------------------------

def load_cov(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing covariance file: {path}")
    cov = pd.read_csv(path, index_col=0)
    assert (cov.columns == cov.index).all(), "Cov CSV must have same row/column tickers in same order"
    cov = (cov + cov.T) / 2.0  # enforce symmetry
    return cov

def blend_cov(cov_a: pd.DataFrame, cov_b: pd.DataFrame, alpha: float) -> pd.DataFrame:
    assert (cov_a.index == cov_b.index).all() and (cov_a.columns == cov_b.columns).all()
    return alpha * cov_a + (1.0 - alpha) * cov_b

def project_to_simplex(v: np.ndarray) -> np.ndarray:
    """Euclidean projection onto {w >= 0, sum w = 1}."""
    n = v.size
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, n + 1) > (cssv - 1))[0][-1]
    theta = (cssv[rho] - 1.0) / (rho + 1)
    return np.maximum(v - theta, 0.0)

def risk_contribs(S: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Absolute risk contributions RC_i = w_i * (S w)_i (variance units)."""
    return w * (S @ w)

def erc_objective(w: np.ndarray, S: np.ndarray, cap_share: Optional[float]) -> float:
    """Equalize RC_i with soft penalty if any risk share > cap."""
    RC = risk_contribs(S, w)
    port_var = float(w.T @ S @ w)
    n = len(w)
    avgRC = port_var / n
    dev = RC - avgRC
    obj = float(np.dot(dev, dev))
    if cap_share is not None and port_var > 0:
        shares = RC / (RC.sum() if RC.sum() > 0 else 1e-16)
        over = np.clip(shares - cap_share, 0.0, None)
        obj += port_var * 1000.0 * float(np.dot(over, over))
    return obj

def gradient_numeric(f, w, eps=1e-6):
    g = np.zeros_like(w)
    f0 = f(w)
    for i in range(len(w)):
        wi = w.copy()
        wi[i] += eps
        g[i] = (f(wi) - f0) / eps
    return g

def erc_optimize(
    cov: pd.DataFrame,
    cap_share: Optional[float] = RISK_SHARE_CAP,
    weight_cap: Optional[float] = WEIGHT_CAP,
    tol: float = TOL,
    max_iters: int = MAX_ITERS,
) -> Tuple[pd.Series, pd.Series, float, pd.Series]:
    """
    Solve ERC with non-negativity, sum=1, optional hard weight cap,
    and soft cap on risk shares. Returns:
      weights (Series), risk_shares (Series), portfolio_vol (float),
      risk_contrib_vol (Series)  # absolute contributions in volatility units
    """
    S = cov.values.astype(float)
    n = S.shape[0]
    tickers = cov.index.tolist()
    w = np.ones(n) / n
    alpha = 0.5

    def obj(wvec): return erc_objective(wvec, S, cap_share)

    for _ in range(max_iters):
        g = gradient_numeric(obj, w)
        w_new = w - alpha * g
        if weight_cap is not None:
            w_new = np.minimum(w_new, weight_cap)
        w_new = project_to_simplex(w_new)

        o_old, o_new = obj(w), obj(w_new)
        bt = 0
        while o_new > o_old and bt < 8:
            alpha *= 0.5
            w_try = w - alpha * g
            if weight_cap is not None:
                w_try = np.minimum(w_try, weight_cap)
            w_try = project_to_simplex(w_try)
            o_new = obj(w_try)
            w_new = w_try
            bt += 1

        if np.linalg.norm(w_new - w, ord=1) < tol:
            w = w_new
            break
        w = w_new

    RC = risk_contribs(S, w)                     # variance units
    port_var = float(w.T @ S @ w)
    port_vol = float(np.sqrt(port_var))
    RC_vol = pd.Series(RC / (port_vol if port_vol > 0 else 1e-16), index=tickers, name="risk_contrib_vol")
    shares = pd.Series(RC / (RC.sum() if RC.sum() > 0 else 1e-16), index=tickers, name="risk_share")

    w_s = pd.Series(w, index=tickers, name="weight")
    return w_s, shares, port_vol, RC_vol

def save_panel(title: str, cov: pd.DataFrame, out_stub: str):
    w, s, vol, rc_vol = erc_optimize(cov)
    df = pd.concat([w, s, rc_vol], axis=1)  # weight (fraction), risk_share (fraction), risk_contrib_vol (abs vol)
    df_sorted = df.sort_values("risk_share", ascending=False)
    df_sorted.to_csv(OUTDIR / f"{out_stub}.csv")
    print(f"\n=== {title} ===")
    print(f"Portfolio vol (annualized): {vol:.4f}")
    print("Top 10 risk shares (%, sorted):")
    print((df_sorted.head(10)[["weight","risk_share"]] * 100).round(2))
    # also save “pretty” version with percents for quick viewing
    pretty = df.copy()
    pretty["weight_%"] = pretty["weight"] * 100
    pretty["risk_share_%"] = pretty["risk_share"] * 100
    pretty = pretty.drop(columns=["weight","risk_share"])
    pretty = pretty[["weight_%","risk_share_%","risk_contrib_vol"]]
    pretty.sort_values("risk_share_%", ascending=False).to_csv(OUTDIR / f"{out_stub}_pretty.csv")

def main():
    os.makedirs(OUTDIR, exist_ok=True)

    # --- Ledoit–Wolf baseline ---
    cov_lw = load_cov(LW_FILE)
    save_panel("ERC — Ledoit–Wolf (baseline)", cov_lw, "erc_ledoit_wolf")

    # --- Winsorized + LW (optional) ---
    if WINSOR_FILE.exists():
        cov_w = load_cov(WINSOR_FILE).reindex(index=cov_lw.index, columns=cov_lw.columns)
        save_panel("ERC — Winsorized returns + LW", cov_w, "erc_winsor_lw")
    else:
        print("\n[INFO] Skipping 'Winsorized + LW' (file not found).")

    # --- 70/30 LW/EWMA blend (optional) ---
    if EWMA_FILE.exists():
        cov_ewma = load_cov(EWMA_FILE).reindex(index=cov_lw.index, columns=cov_lw.columns)
        cov_blend = blend_cov(cov_lw, cov_ewma, alpha=0.70)
        save_panel("ERC — 70/30 LW/EWMA blend", cov_blend, "erc_blend_70_30")
    else:
        print("\n[INFO] Skipping '70/30 LW/EWMA' (EWMA file not found).")

if __name__ == "__main__":
    main()
