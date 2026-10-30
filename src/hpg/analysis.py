"""Benchmarking, market sizing, scenario projection and sensitivity.

The same formulas are written into the Excel model (excel_model.py), and a
test recalculates the workbook to prove both give the same answer.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config

CRORE = 1e7


@dataclass
class Base:
    year: int
    population: float
    che_pc_usd: float
    oop_pct: float          # as a fraction (0.5 = 50%)
    fx: float
    gdp_pc_ppp: float
    g_pop: float
    g_che_pc: float
    peer_median_oop: float
    income_implied_oop: float
    reg_slope: float
    reg_intercept: float
    reg_r2: float
    reg_n: int


def latest_complete_year(df, iso, cols) -> int:
    d = df[(df["iso3"] == iso)].dropna(subset=cols)
    if d.empty:
        raise ValueError(f"No year with complete data for {iso}: {cols}")
    return int(d["year"].max())


def cagr(series: pd.Series, years: int) -> float:
    s = series.dropna().sort_index()
    end = s.index.max()
    start = max(s.index.min(), end - years)
    n = end - start
    return float((s.loc[end] / s.loc[start]) ** (1 / n) - 1) if n > 0 else 0.0


def latest_per_country(df, year, cols, window=3) -> pd.DataFrame:
    """Each country's most recent observation within [year - window, year]."""
    d = df[(df["year"] <= year) & (df["year"] >= year - window)].dropna(subset=cols)
    return d.sort_values("year").groupby("iso3").tail(1)


def income_regression(df, year):
    """Cross-country: OOP share of health spending vs log GDP per capita (PPP)."""
    d = latest_per_country(df, year, ["oop_pct_che", "gdp_pc_ppp"])
    x, y = np.log(d["gdp_pc_ppp"]), d["oop_pct_che"] / 100
    slope, intercept = np.polyfit(x, y, 1)
    pred = intercept + slope * x
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
    return float(slope), float(intercept), float(r2), int(len(d)), d.assign(predicted=pred)


def build_base(df) -> tuple[Base, pd.DataFrame]:
    cols = ["population", "che_pc_usd", "oop_pct_che", "fx_lcu_per_usd", "gdp_pc_ppp"]
    year = latest_complete_year(df, config.FOCUS, cols)
    ind = df[df["iso3"] == config.FOCUS].set_index("year")
    row = ind.loc[year]
    peers = latest_per_country(df[df["iso3"].isin(config.PEERS)], year, ["oop_pct_che"])
    slope, intercept, r2, n, reg_df = income_regression(df, year)
    base = Base(
        year=year, population=float(row["population"]), che_pc_usd=float(row["che_pc_usd"]),
        oop_pct=float(row["oop_pct_che"]) / 100, fx=float(row["fx_lcu_per_usd"]),
        gdp_pc_ppp=float(row["gdp_pc_ppp"]),
        g_pop=cagr(ind.loc[:year, "population"], config.CAGR_YEARS),
        g_che_pc=cagr(ind.loc[:year, "che_pc_usd"], config.CAGR_YEARS),
        peer_median_oop=float(peers["oop_pct_che"].median()) / 100,
        income_implied_oop=float(intercept + slope * np.log(row["gdp_pc_ppp"])),
        reg_slope=slope, reg_intercept=intercept, reg_r2=r2, reg_n=n,
    )
    return base, reg_df


def benchmark_table(df, year) -> pd.DataFrame:
    isos = [config.FOCUS] + config.PEERS
    cols = ["oop_pct_che", "che_pc_usd", "gdp_pc_ppp", "gov_pct_che", "che_pct_gdp"]
    d = latest_per_country(df[df["iso3"].isin(isos)], year, ["oop_pct_che", "che_pc_usd"])
    out = d[["iso3", "name", "year"] + [c for c in cols if c in d.columns]].copy()
    return out.sort_values("oop_pct_che", ascending=False).reset_index(drop=True)


def base_sizing(b: Base, a: dict) -> dict:
    che_total = b.population * b.che_pc_usd
    oop = che_total * b.oop_pct
    insurable = oop * a["insurable_share"]
    return {"che_total_usd": che_total, "oop_usd": oop, "insurable_oop_usd": insurable,
            "premium_equivalent_usd": insurable / a["loss_ratio"]}


def oop_path(b: Base, target_oop: float, year: int) -> float:
    progress = min(1.0, max(0.0, (year - b.year) / (config.TARGET_YEAR - b.year)))
    return b.oop_pct + (target_oop - b.oop_pct) * progress


def project(b: Base, a: dict, scenario: str) -> pd.DataFrame:
    target = {"Status quo": b.oop_pct, "Peer convergence": b.peer_median_oop,
              "Income-implied": b.income_implied_oop}[scenario]
    rows = []
    for yr in range(b.year, config.TARGET_YEAR + 1):
        t = yr - b.year
        pop = b.population * (1 + b.g_pop) ** t
        che_pc = b.che_pc_usd * (1 + b.g_che_pc) ** t
        che = pop * che_pc
        oop_s = oop_path(b, target, yr)
        insurable_pool = che * b.oop_pct * a["insurable_share"]
        shift = min(max(b.oop_pct - oop_s, 0) * che, insurable_pool)  # can only insure the insurable part
        claims = shift * a["private_capture"]
        premium = claims / a["loss_ratio"]
        rows.append({"year": yr, "population": pop, "che_pc_usd": che_pc, "che_total_usd": che,
                     "oop_pct_status_quo": b.oop_pct, "oop_pct_scenario": oop_s,
                     "oop_shift_usd": shift, "private_claims_usd": claims, "premium_usd": premium,
                     "client_premium_usd": premium * a["client_share"]})
    df = pd.DataFrame(rows)
    for c in ["che_total_usd", "oop_shift_usd", "premium_usd", "client_premium_usd"]:
        df[c.replace("_usd", "_inr_cr")] = df[c] * b.fx / CRORE
    return df


def assumption_values(overrides=None) -> dict:
    a = {k: v["value"] for k, v in config.ASSUMPTIONS.items()}
    return a | (overrides or {})


def sensitivity(b: Base, scenario="Peer convergence") -> pd.DataFrame:
    """Tornado: client premium in the target year when each driver moves to its low/high case."""
    def result(a, base=b):
        return project(base, a, scenario).iloc[-1]["client_premium_inr_cr"]

    a0 = assumption_values()
    central = result(a0)
    rows = []
    for k, spec in config.ASSUMPTIONS.items():
        rows.append({"driver": spec["short"], "low_case": spec["low"], "high_case": spec["high"],
                     "result_low": result(a0 | {k: spec["low"]}), "result_high": result(a0 | {k: spec["high"]})})
    for label, field, delta in [("Health spend growth +/-2 pts", "g_che_pc", 0.02),
                                ("Population growth +/-0.5 pts", "g_pop", 0.005)]:
        lo = Base(**(b.__dict__ | {field: getattr(b, field) - delta}))
        hi = Base(**(b.__dict__ | {field: getattr(b, field) + delta}))
        rows.append({"driver": label, "low_case": getattr(lo, field), "high_case": getattr(hi, field),
                     "result_low": result(a0, lo), "result_high": result(a0, hi)})
    df = pd.DataFrame(rows)
    df["swing"] = (df["result_high"] - df["result_low"]).abs()
    df["central"] = central
    return df.sort_values("swing", ascending=False).reset_index(drop=True)


def run(df) -> dict:
    b, reg_df = build_base(df)
    a = assumption_values()
    proj = {s: project(b, a, s) for s in config.SCENARIOS}
    return {"base": b, "assumptions": a, "sizing": base_sizing(b, a), "projections": proj,
            "benchmark": benchmark_table(df, b.year), "regression": reg_df,
            "sensitivity": sensitivity(b), "data": df}
