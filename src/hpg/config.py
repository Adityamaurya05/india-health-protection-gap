"""Case set-up: data series, peer set and every judgement-based assumption.

Data-driven inputs come from the World Bank API. Assumptions below are NOT
facts. Each has a note on where to source a better number, and the deck and
Excel model flag them in a different colour.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
CACHE_FILE = DATA_DIR / "worldbank.csv"

FOCUS = "IND"
PEERS = ["CHN", "IDN", "THA", "VNM", "PHL", "MYS", "BRA", "MEX", "ZAF", "TUR", "BGD", "LKA"]
START_YEAR, END_YEAR = 2000, 2024

WB_API = "https://api.worldbank.org/v2"
INDICATORS = {
    "SP.POP.TOTL": "population",
    "NY.GDP.PCAP.PP.CD": "gdp_pc_ppp",             # GDP per capita, PPP (current intl $)
    "NY.GDP.PCAP.CD": "gdp_pc_usd",
    "SH.XPD.CHEX.PC.CD": "che_pc_usd",             # current health expenditure per capita (US$)
    "SH.XPD.CHEX.GD.ZS": "che_pct_gdp",
    "SH.XPD.OOPC.CH.ZS": "oop_pct_che",            # out-of-pocket, % of current health expenditure
    "SH.XPD.GHED.CH.ZS": "gov_pct_che",            # domestic general government, % of CHE
    "PA.NUS.FCRF": "fx_lcu_per_usd",               # official exchange rate
    "SP.POP.65UP.TO.ZS": "pop_65plus_pct",
    "SP.URB.TOTL.IN.ZS": "urban_pct",
}

CAGR_YEARS = 10      # history window for growth rates
TARGET_YEAR = 2030   # horizon for the opportunity

# ---- Assumptions (judgement; replace with sourced figures where possible) ----
ASSUMPTIONS = {
    "insurable_share": {
        "short": "Insurable share of OOP",
        "value": 0.30, "low": 0.20, "high": 0.45,
        "label": "Share of out-of-pocket spend that is insurable (mainly hospitalisation)",
        "source": "ASSUMPTION. Replace with the inpatient share of OOP from India's National Health Accounts estimates.",
    },
    "loss_ratio": {
        "short": "Loss ratio",
        "value": 0.85, "low": 0.75, "high": 0.95,
        "label": "Claims as % of premium (incurred claims ratio)",
        "source": "ASSUMPTION. Replace with the retail health ICR from the IRDAI Annual Report.",
    },
    "private_capture": {
        "short": "Private capture of OOP shift",
        "value": 0.50, "low": 0.30, "high": 0.70,
        "label": "Share of the OOP reduction captured by private insurance (rest goes to government schemes)",
        "source": "ASSUMPTION. Policy-dependent (e.g. expansion of government schemes vs retail growth).",
    },
    "client_share": {
        "short": "Client market share",
        "value": 0.05, "low": 0.03, "high": 0.08,
        "label": "Client's achievable share of the incremental private premium pool",
        "source": "ASSUMPTION. Set from the client's current retail health market share (IRDAI segment data).",
    },
}

SCENARIOS = {
    "Status quo": "OOP share stays at today's level",
    "Peer convergence": "OOP share moves linearly to the peer median by the target year",
    "Income-implied": "OOP share moves to the level predicted by India's income (cross-country regression)",
}
