"""World Bank Indicators API client (no API key needed), with a CSV cache."""

import time

import numpy as np
import pandas as pd
import requests

from . import config


def _get(url, params, retries=4):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))


def country_metadata() -> pd.DataFrame:
    js = _get(f"{config.WB_API}/country", {"format": "json", "per_page": 500})
    rows = [{"iso3": c["id"], "name": c["name"], "region": c["region"]["value"],
             "income": c["incomeLevel"]["value"]} for c in js[1]]
    meta = pd.DataFrame(rows)
    return meta[meta["region"] != "Aggregates"]


def fetch_indicator(code: str) -> pd.DataFrame:
    js = _get(f"{config.WB_API}/country/all/indicator/{code}",
              {"format": "json", "per_page": 20000, "date": f"{config.START_YEAR}:{config.END_YEAR}"})
    if len(js) < 2 or js[1] is None:
        return pd.DataFrame(columns=["iso3", "year", "value"])
    rows = [{"iso3": d["countryiso3code"], "year": int(d["date"]), "value": d["value"]}
            for d in js[1] if d["countryiso3code"]]
    return pd.DataFrame(rows).dropna()


def download() -> pd.DataFrame:
    meta = country_metadata()
    frames = []
    for code, name in config.INDICATORS.items():
        print(f"    fetching {code} ({name})")
        df = fetch_indicator(code)
        df["indicator"] = name
        frames.append(df)
    long = pd.concat(frames)
    long = long[long["iso3"].isin(meta["iso3"])]
    wide = long.pivot_table(index=["iso3", "year"], columns="indicator", values="value").reset_index()
    return wide.merge(meta, on="iso3", how="left")


def load(refresh=False, sample=False) -> pd.DataFrame:
    if sample:
        return make_sample()
    if config.CACHE_FILE.exists() and not refresh:
        return pd.read_csv(config.CACHE_FILE)
    df = download()
    config.DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(config.CACHE_FILE, index=False)
    return df


def make_sample(seed=3) -> pd.DataFrame:
    """Synthetic panel with the same columns, for tests and offline demos ONLY."""
    rng = np.random.default_rng(seed)
    isos = [config.FOCUS] + config.PEERS + [f"C{i:02d}" for i in range(80)]
    rows = []
    for iso in isos:
        gdp0 = np.exp(rng.uniform(7, 11))
        pop0 = rng.uniform(5e6, 3e8) if iso != config.FOCUS else 1.05e9
        oop0 = np.clip(95 - 7 * np.log(gdp0) + rng.normal(0, 8), 5, 80)
        if iso == config.FOCUS:  # make the demo case non-trivial; real values come from the API
            gdp0, oop0 = 3500.0, 62.0
        for k, yr in enumerate(range(config.START_YEAR, 2023)):
            gdp = gdp0 * 1.04 ** k
            rows.append({
                "iso3": iso, "year": yr, "name": iso, "region": "Sample", "income": "Sample",
                "population": pop0 * 1.012 ** k, "gdp_pc_ppp": gdp, "gdp_pc_usd": gdp / 3,
                "che_pc_usd": gdp / 3 * 0.045 * 1.01 ** k,
                "che_pct_gdp": 4.5, "oop_pct_che": max(oop0 - 0.4 * k, 3), "gov_pct_che": 100 - oop0 - 10,
                "fx_lcu_per_usd": 45 + 1.5 * k if iso == config.FOCUS else 10.0,
                "pop_65plus_pct": 5 + 0.1 * k, "urban_pct": 30 + 0.4 * k,
            })
    return pd.DataFrame(rows)
