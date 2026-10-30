"""Build the whole case: data -> analysis -> Excel model -> PowerPoint deck -> memo.

    python run_case.py            # real World Bank data (cached in data/worldbank.csv)
    python run_case.py --refresh  # re-download
    python run_case.py --sample   # synthetic data, offline smoke test only
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent / "src"))
from hpg import analysis, config, deck, excel_model, worldbank  # noqa: E402


def charts(res, figs: Path):
    figs.mkdir(parents=True, exist_ok=True)
    b, reg = res["base"], res["regression"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(reg["gdp_pc_ppp"], reg["oop_pct_che"] / 100, s=12, color="#8d99ae", label="Countries")
    peers = reg[reg["iso3"].isin(config.PEERS)]
    ax.scatter(peers["gdp_pc_ppp"], peers["oop_pct_che"] / 100, s=30, color="#2a9d8f", label="Peers")
    ind = reg[reg["iso3"] == config.FOCUS]
    ax.scatter(ind["gdp_pc_ppp"], ind["oop_pct_che"] / 100, s=90, color="#c0392b", label="India", zorder=3)
    x = np.geomspace(reg["gdp_pc_ppp"].min(), reg["gdp_pc_ppp"].max(), 50)
    ax.plot(x, b.reg_intercept + b.reg_slope * np.log(x), color="#1f3a5f", label="Cross-country fit")
    ax.set_xscale("log")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set(xlabel="GDP per capita, PPP (log)", ylabel="Out-of-pocket % of health spending",
           title=f"OOP share vs income ({b.year})")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(figs / "oop_vs_income.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    for scen, p in res["projections"].items():
        ax.plot(p["year"], p["premium_inr_cr"], marker="o", label=scen)
    ax.set(title="Incremental private health premium (INR crore)", ylabel="INR crore")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figs / "scenarios.png", dpi=130)
    plt.close(fig)


def memo(s, res, sample) -> str:
    warn = "> **WARNING: SYNTHETIC sample data. Do not quote these numbers.**\n\n" if sample else ""
    a = res["assumptions"]
    return f"""# Case memo: Closing India's health protection gap
{warn}**Client question.** How big is the retail health insurance opportunity if India's out-of-pocket (OOP)
health spending falls toward peer levels, and what could a mid-size insurer capture by {config.TARGET_YEAR}?

**Answer (central case).** About **INR {s['central_premium_cr']:,.0f} crore** of new private premium by
{config.TARGET_YEAR}. Of that, the client could target **INR {s['central_client_cr']:,.0f} crore** at a
{a['client_share']:.0%} share. The income-implied case gives INR {s['income_premium_cr']:,.0f} crore.

## Supporting points
1. **The gap is real.** OOP was {s['oop_pct']:.0%} of health spending in {s['base_year']}, versus a peer median of
   {s['peer_median']:.0%} ({s['gap_peer_pts']:+.0f} pts). It is {s['gap_income_pts']:+.0f} pts versus what India's income predicts.
2. **The pool is large today.** Households pay about INR {s['oop_inr_cr']:,.0f} crore a year out of pocket. About
   INR {s['insurable_inr_cr']:,.0f} crore of it is insurable, worth INR {s['premium_eq_inr_cr']:,.0f} crore of premium.
3. **The answer depends on a few assumptions.** The biggest swing factor is *{s['top_driver'].lower()}*
   (INR {s['top_driver_low']:,.0f} to {s['top_driver_high']:,.0f} crore for the client).

## Method
Top-down: population x health spend per capita x OOP share (World Bank WDI). Three OOP paths to
{config.TARGET_YEAR}: status quo, peer convergence, and income-implied (cross-country regression). The OOP
reduction is capped at the insurable pool, split between government and private insurers, and converted
to premium through a loss ratio.

## Assumptions to validate (judgement, not data)
""" + "\n".join(f"* {v['label']}: **{v['value']:.0%}** (range {v['low']:.0%}-{v['high']:.0%}). {v['source']}"
                for v in config.ASSUMPTIONS.values()) + """

## Next steps
Validate the assumptions with NHA and IRDAI data. Complete the bottom-up check. Go to state level to decide where to play.
"""


def resume_bullets(s, res) -> str:
    b = res["base"]
    return f"""# Resume bullets (generated from YOUR run)

**Consulting Case: India Health Protection Gap (Market Sizing & Strategy)** | Excel, PowerPoint, Python | [GitHub link]
- Sized India's retail health insurance opportunity top-down from World Bank data on {b.reg_n} countries: about INR {s['oop_inr_cr']:,.0f} crore of annual out-of-pocket spend, an insurable premium pool of INR {s['premium_eq_inr_cr']:,.0f} crore, and INR {s['central_premium_cr']:,.0f} crore of new private premium by {config.TARGET_YEAR} under peer convergence
- Benchmarked India against {len(config.PEERS)} emerging-market peers and a cross-country income regression (R² {b.reg_r2:.2f}), showing an OOP share {s['gap_peer_pts']:+.0f} pts vs the peer median
- Built a fully linked Excel model (inputs, 3 scenarios, sensitivity, bottom-up cross-check) and a 10-slide action-titled deck with a tornado analysis and a phased next-steps plan
"""


def main(sample=False, refresh=False):
    out = config.OUTPUT_DIR
    out.mkdir(exist_ok=True)
    print("1/5 Loading World Bank data ...")
    df = worldbank.load(refresh=refresh, sample=sample)
    print(f"    {df['iso3'].nunique()} countries, {df['year'].min()}-{df['year'].max()}")
    print("2/5 Benchmarking, sizing, scenarios, sensitivity ...")
    res = analysis.run(df)
    print("3/5 Building Excel model ...")
    excel_model.build_workbook(res, out / "India_Health_Protection_Gap_Model.xlsx")
    print("4/5 Building PowerPoint deck ...")
    s = deck.build_deck(res, out / "India_Health_Protection_Gap_Deck.pptx", sample_mode=sample)
    print("5/5 Writing memo, charts, metrics ...")
    charts(res, out / "figures")
    (out / "case_memo.md").write_text(memo(s, res, sample))
    (out / "resume_bullets.md").write_text(resume_bullets(s, res))
    res["benchmark"].to_csv(out / "benchmark.csv", index=False)
    res["sensitivity"].to_csv(out / "sensitivity.csv", index=False)
    for scen, p in res["projections"].items():
        p.to_csv(out / f"projection_{scen.lower().replace(' ', '_').replace('-', '_')}.csv", index=False)
    metrics = {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in s.items()}
    metrics |= {"sample_mode": sample, "base": {k: float(v) for k, v in res["base"].__dict__.items()}}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    print(f"\nCentral case: INR {s['central_premium_cr']:,.0f} cr new private premium by {config.TARGET_YEAR}; "
          f"client INR {s['central_client_cr']:,.0f} cr")
    if sample:
        print("NOTE: synthetic sample data - do not quote these numbers.")
    return res, s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    main(sample=a.sample, refresh=a.refresh)
