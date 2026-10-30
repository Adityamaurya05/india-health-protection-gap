"""Build the Excel model with LIVE formulas: change an input, every number updates.

Colour convention used in banking and consulting models:
  blue font  = hard-coded input (data or assumption)
  black font = formula
  yellow fill = judgement assumption the client should challenge
"""

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

from . import config

BLUE = Font(color="1F4E9E")
BOLD = Font(bold=True)
HEAD = Font(bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="1F3A5F")
ASSUME_FILL = PatternFill("solid", fgColor="FFF2CC")
THIN = Border(bottom=Side(style="thin", color="BBBBBB"))
PCT, NUM0, NUM2, USD = "0.0%", "#,##0", "#,##0.00", "#,##0"

PROJ_COLS = [
    ("Year", None), ("t", "0"), ("Population", NUM0), ("CHE per capita (US$)", NUM2),
    ("CHE total (US$)", NUM0), ("OOP % status quo", PCT), ("OOP % scenario", PCT),
    ("Insurable OOP pool (US$)", NUM0), ("OOP shifted to insurance (US$)", NUM0),
    ("Private insured claims (US$)", NUM0), ("Private premium (US$)", NUM0),
    ("Client premium (US$)", NUM0), ("Private premium (INR cr)", NUM0), ("Client premium (INR cr)", NUM0),
]


def _name(wb, name, ref):
    wb.defined_names[name] = DefinedName(name, attr_text=ref)


def _header(ws, row, labels):
    for j, lab in enumerate(labels, 1):
        c = ws.cell(row, j, lab)
        c.font, c.fill = HEAD, HEAD_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center")


def _widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _readme(wb, b):
    ws = wb.active
    ws.title = "README"
    lines = [
        ("India Health Protection Gap: Market Sizing Model", BOLD),
        ("Question: how large is the retail health insurance opportunity created if India's out-of-pocket "
         "(OOP) health spending moves toward peer levels, and what could a mid-size insurer capture by "
         f"{config.TARGET_YEAR}?", None),
        ("", None),
        ("How to use", BOLD),
        ("1. Change blue / yellow cells on the 'Inputs' sheet. Every other number is a formula.", None),
        ("2. 'Projection' shows the three scenarios year by year; 'Summary' shows the target-year answer.", None),
        ("3. 'BottomUp' is a cross-check template. Fill it from the IRDAI Annual Report.", None),
        ("", None),
        ("Colour code", BOLD),
        ("Blue font = input. Black = formula. Yellow fill = judgement assumption (challenge these first).", None),
        ("", None),
        ("Sources", BOLD),
        ("World Bank World Development Indicators API (indicator codes listed on 'Inputs'). Data year "
         f"{b.year}. Assumptions are the author's and are labelled as such.", None),
    ]
    for i, (text, font) in enumerate(lines, 1):
        c = ws.cell(i, 1, text)
        if font:
            c.font = font
        c.alignment = Alignment(wrap_text=True)
    ws.column_dimensions["A"].width = 120


def _inputs(wb, b):
    ws = wb.create_sheet("Inputs")
    _header(ws, 1, ["Input", "Value", "Unit", "Source / note"])
    data_rows = [
        ("base_year", "Base (latest complete) data year", b.year, "year", "World Bank WDI", "0"),
        ("target_year", "Target year", config.TARGET_YEAR, "year", "Case horizon", "0"),
        ("population", "Population", b.population, "people", "SP.POP.TOTL", NUM0),
        ("che_pc_usd", "Current health expenditure per capita", b.che_pc_usd, "US$", "SH.XPD.CHEX.PC.CD", NUM2),
        ("oop_pct", "Out-of-pocket share of health spending", b.oop_pct, "%", "SH.XPD.OOPC.CH.ZS", PCT),
        ("fx", "Exchange rate", b.fx, "INR per US$", "PA.NUS.FCRF (held constant in projection)", NUM2),
        ("g_pop", f"Population CAGR (last {config.CAGR_YEARS}y)", b.g_pop, "% p.a.", "Computed from SP.POP.TOTL", "0.00%"),
        ("g_che_pc", f"Health spend per capita CAGR (last {config.CAGR_YEARS}y)", b.g_che_pc, "% p.a.",
         "Computed from SH.XPD.CHEX.PC.CD (US$, so includes FX moves)", "0.00%"),
        ("peer_median_oop", "Peer median OOP share", b.peer_median_oop, "%", "Peers: " + ", ".join(config.PEERS), PCT),
        ("income_implied_oop", "Income-implied OOP share for India", b.income_implied_oop, "%",
         f"Cross-country regression on ln(GDP pc PPP), n={b.reg_n}, R2={b.reg_r2:.2f}", PCT),
    ]
    r = 2
    for name, label, val, unit, src, fmt in data_rows:
        ws.cell(r, 1, label)
        c = ws.cell(r, 2, val)
        c.font, c.number_format = BLUE, fmt
        ws.cell(r, 3, unit)
        ws.cell(r, 4, src)
        _name(wb, name, f"Inputs!$B${r}")
        r += 1
    r += 1
    ws.cell(r, 1, "Judgement assumptions (challenge these)").font = BOLD
    r += 1
    for key, spec in config.ASSUMPTIONS.items():
        ws.cell(r, 1, spec["label"])
        c = ws.cell(r, 2, spec["value"])
        c.font, c.fill, c.number_format = BLUE, ASSUME_FILL, PCT
        ws.cell(r, 3, f"range {spec['low']:.0%} - {spec['high']:.0%}")
        ws.cell(r, 4, spec["source"])
        _name(wb, key, f"Inputs!$B${r}")
        r += 1
    _widths(ws, [62, 16, 22, 95])
    ws.freeze_panes = "A2"


def _sizing(wb):
    ws = wb.create_sheet("Sizing")
    _header(ws, 1, ["Base-year market sizing (top-down)", "US$", "INR crore", "Logic"])
    rows = [
        ("Current health expenditure (CHE)", "=population*che_pc_usd", "Population x CHE per capita"),
        ("Out-of-pocket spend (OOP)", "=B2*oop_pct", "CHE x OOP share"),
        ("Insurable OOP", "=B3*insurable_share", "OOP x insurable share (assumption)"),
        ("Premium equivalent of insurable OOP", "=B4/loss_ratio", "Claims / loss ratio = premium needed"),
    ]
    for i, (label, f, logic) in enumerate(rows, 2):
        ws.cell(i, 1, label)
        ws.cell(i, 2, f).number_format = USD
        ws.cell(i, 3, f"=B{i}*fx/10^7").number_format = NUM0
        ws.cell(i, 4, logic)
    _widths(ws, [42, 22, 18, 50])


def _projection(wb, b):
    ws = wb.create_sheet("Projection")
    targets = {"Status quo": "=oop_pct", "Peer convergence": "=peer_median_oop",
               "Income-implied": "=income_implied_oop"}
    years = list(range(b.year, config.TARGET_YEAR + 1))
    row = 1
    anchors = {}
    for scen, target_formula in targets.items():
        ws.cell(row, 1, f"Scenario: {scen}").font = BOLD
        ws.cell(row, 3, config.SCENARIOS[scen])
        ws.cell(row + 1, 1, "Target OOP share")
        tc = ws.cell(row + 1, 2, target_formula)
        tc.number_format = PCT
        target_ref = f"$B${row + 1}"
        _header(ws, row + 2, [c for c, _ in PROJ_COLS])
        first = row + 3
        for k, yr in enumerate(years):
            r = first + k
            f = {
                1: yr, 2: f"=A{r}-base_year", 3: f"=population*(1+g_pop)^B{r}",
                4: f"=che_pc_usd*(1+g_che_pc)^B{r}", 5: f"=C{r}*D{r}", 6: "=oop_pct",
                7: f"=oop_pct+({target_ref}-oop_pct)*MIN(1,MAX(0,(A{r}-base_year)/(target_year-base_year)))",
                8: f"=E{r}*oop_pct*insurable_share", 9: f"=MIN(MAX(F{r}-G{r},0)*E{r},H{r})",
                10: f"=I{r}*private_capture", 11: f"=J{r}/loss_ratio", 12: f"=K{r}*client_share",
                13: f"=K{r}*fx/10^7", 14: f"=L{r}*fx/10^7",
            }
            for col, val in f.items():
                c = ws.cell(r, col, val)
                fmt = PROJ_COLS[col - 1][1]
                if fmt:
                    c.number_format = fmt
                if col == 1:
                    c.font = BLUE
        anchors[scen] = first + len(years) - 1  # target-year row
        row = first + len(years) + 2
    _widths(ws, [10, 6, 16, 12, 18, 10, 10, 18, 18, 18, 18, 16, 14, 14])
    return anchors


def _summary(wb, anchors):
    ws = wb.create_sheet("Summary", 1)
    _header(ws, 1, ["Scenario", f"{config.TARGET_YEAR} private premium opportunity (INR cr)",
                    f"{config.TARGET_YEAR} client premium (INR cr)", f"OOP share in {config.TARGET_YEAR}"])
    for i, (scen, r) in enumerate(anchors.items(), 2):
        ws.cell(i, 1, scen)
        ws.cell(i, 2, f"=Projection!M{r}").number_format = NUM0
        ws.cell(i, 3, f"=Projection!N{r}").number_format = NUM0
        ws.cell(i, 4, f"=Projection!G{r}").number_format = PCT
    _widths(ws, [24, 38, 30, 20])


def _bottom_up(wb):
    ws = wb.create_sheet("BottomUp")
    ws.cell(1, 1, "Bottom-up cross-check (fill from IRDAI Annual Report / insurer disclosures)").font = BOLD
    _header(ws, 2, ["Item", "Value", "Note"])
    rows = [
        ("Lives covered by retail (individual + family floater) health policies, crore", None,
         "ENTER: IRDAI annual report, health insurance section"),
        ("Average premium per life (INR)", None, "ENTER: retail health premium / retail lives"),
        ("Implied retail health premium (INR crore)", "=IF(AND(ISNUMBER(B3),ISNUMBER(B4)),B3*B4,\"enter inputs\")",
         "Lives (crore) x premium per life = INR crore"),
        ("Top-down premium equivalent of insurable OOP (INR crore)", "=Sizing!C5", "From 'Sizing'"),
        ("Current retail premium as % of top-down headroom", "=IFERROR(B5/B6,\"enter inputs\")",
         "Low % = large untapped market; >100% = top-down assumptions too low"),
    ]
    for i, (label, f, note) in enumerate(rows, 3):
        ws.cell(i, 1, label)
        c = ws.cell(i, 2, f)
        if f is None:
            c.fill, c.font = ASSUME_FILL, BLUE
        ws.cell(i, 3, note)
    ws["B7"].number_format = PCT
    ws["B5"].number_format = ws["B6"].number_format = NUM0
    _widths(ws, [70, 20, 70])


def _table_sheet(wb, title, df, fmts=None):
    ws = wb.create_sheet(title)
    _header(ws, 1, list(df.columns))
    for i, rec in enumerate(df.itertuples(index=False), 2):
        for j, v in enumerate(rec, 1):
            c = ws.cell(i, j, v.item() if hasattr(v, "item") else v)
            c.font = BLUE
            if fmts and df.columns[j - 1] in fmts:
                c.number_format = fmts[df.columns[j - 1]]
    _widths(ws, [max(12, min(45, len(str(c)) + 4)) for c in df.columns])
    ws.freeze_panes = "A2"
    return ws


def build_workbook(res, path):
    b = res["base"]
    wb = Workbook()
    _readme(wb, b)
    _inputs(wb, b)
    _sizing(wb)
    anchors = _projection(wb, b)
    _summary(wb, anchors)
    _bottom_up(wb)
    _table_sheet(wb, "Benchmark", res["benchmark"],
                 {"oop_pct_che": NUM2, "che_pc_usd": NUM2, "gdp_pc_ppp": NUM0})
    sens = res["sensitivity"].drop(columns=["central"])
    ws = _table_sheet(wb, "Sensitivity", sens, {"result_low": NUM0, "result_high": NUM0, "swing": NUM0})
    ws.cell(len(sens) + 3, 1, "Values computed in Python (tornado on client premium, Peer convergence). "
                              "Flex 'Inputs' to test any case live.")
    india = res["data"][res["data"]["iso3"] == config.FOCUS].sort_values("year")
    keep = ["year"] + [c for c in config.INDICATORS.values() if c in india.columns]
    _table_sheet(wb, "Data_India", india[keep])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return anchors
