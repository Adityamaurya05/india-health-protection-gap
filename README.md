# Closing India's Health Protection Gap: A Consulting-Style Market Sizing Case

**Client question (hypothetical):** *A mid-size Indian health insurer wants to grow retail health. How big is
the opportunity if India's out-of-pocket (OOP) health spending moves toward peer levels, and what could
the insurer realistically capture by 2030?*

This repo answers it the way a strategy consulting team would: hypothesis-driven, built on public data,
with a **fully linked Excel model**, a **10-slide action-titled deck** and a one-page memo. Every number
in the deck is generated from the model, so changing an assumption rewrites the storyline consistently.

![OOP vs income](outputs/figures/oop_vs_income.png)

## Deliverables (generated into `outputs/`)

| File | What it is |
|---|---|
| `India_Health_Protection_Gap_Deck.pptx` | 10 slides: exec summary, peer benchmark, income regression, sizing, scenarios, client prize, tornado, next steps, appendix. Native PowerPoint charts, so they're editable |
| `India_Health_Protection_Gap_Model.xlsx` | Inputs → Sizing → Projection (3 scenarios) → Summary, plus Sensitivity, a **bottom-up cross-check template** and raw data. Blue = input, black = formula, yellow = judgement |
| `case_memo.md` | One-page answer-first memo (pyramid principle) |
| `resume_bullets.md` | Bullets filled with the numbers from your run |

## Approach (issue tree)

```
How big is the opportunity for the client by 2030?
├── How big is the protection gap today?
│   ├── OOP share vs peers                         (World Bank: SH.XPD.OOPC.CH.ZS)
│   └── OOP share vs what India's income predicts  (cross-country regression on ln GDP pc PPP)
├── How much of it is insurable, and what premium does that imply?
│   └── Total health spend x OOP share x insurable share ÷ loss ratio
├── How fast does it grow, and how much shifts to insurance?
│   └── 3 scenarios: status quo / peer convergence / income-implied, capped at the insurable pool
└── What can the client capture, and what does the answer depend on?
    └── Market share assumption + tornado sensitivity on every driver
```

## Run it

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_case.py              # pulls World Bank data once (free API, no key) and builds everything
python -m pytest -q             # 8 tests, incl. Excel-vs-Python parity if LibreOffice is installed
```

`--refresh` re-downloads; `--sample` uses synthetic data for an offline smoke test only.

## What's data and what's judgement (important)

* **Data (World Bank WDI):** population, health expenditure per capita, OOP share, GDP per capita (PPP),
  exchange rate, and the peer and cross-country values used in the regression.
* **Judgement (yellow cells, flagged on every slide that uses them):** insurable share of OOP (30%), loss ratio
  (85%), private insurers' capture of the OOP shift (50%), client market share (5%). Each has a stated range and a
  suggested source (National Health Accounts, IRDAI Annual Report) for the next phase.
* Health-spend growth uses US$ CAGRs held at a constant exchange rate. This is a simplification, stated in the appendix.

## How I'd extend it
* Fill the bottom-up sheet from the IRDAI Annual Report and reconcile it with the top-down figure.
* Go state by state (NFHS / NSS health surveys) to decide *where to play*.
* Build unit economics (CAC, claims ratio, persistency) by channel to decide *how to win*.

## Structure
```
src/hpg/config.py        peers, indicators, assumptions (with sources/ranges)
src/hpg/worldbank.py     API client + cache
src/hpg/analysis.py      benchmark, regression, sizing, scenarios, tornado
src/hpg/excel_model.py   linked Excel model
src/hpg/deck.py          PowerPoint deck with data-driven action titles
run_case.py              builds every deliverable
```
