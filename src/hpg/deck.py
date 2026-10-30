"""Consulting-style deck with action titles and native (editable) PowerPoint charts.

Every title is generated from the numbers, so the storyline stays truthful if
the data or assumptions change.
"""

import numpy as np
from pptx import Presentation
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_LABEL_POSITION
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from . import config

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
TEAL = RGBColor(0x2A, 0x9D, 0x8F)
GREY = RGBColor(0x8D, 0x99, 0xAE)
RED = RGBColor(0xC0, 0x39, 0x2B)
SOURCE = "Source: World Bank World Development Indicators; team analysis"


def inr_cr(x):
    return f"INR {x:,.0f} cr"


def _title(slide, text, sub=None):
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size, p.font.bold, p.font.color.rgb = Pt(24), True, NAVY
    if sub:
        q = tf.add_paragraph()
        q.text = sub
        q.font.size, q.font.color.rgb = Pt(13), GREY
    line = slide.shapes.add_connector(1, Inches(0.5), Inches(1.45), Inches(12.8), Inches(1.45))
    line.line.color.rgb = NAVY


def _footer(slide, text=SOURCE, n=None):
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(7.0), Inches(11.5), Inches(0.35))
    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size, p.font.color.rgb = Pt(9), GREY
    if n:
        nb = slide.shapes.add_textbox(Inches(12.3), Inches(7.0), Inches(0.6), Inches(0.35))
        nb.text_frame.paragraphs[0].text = str(n)
        nb.text_frame.paragraphs[0].font.size = Pt(9)


def _bullets(slide, items, left=0.6, top=1.7, width=12.0, height=5.0, size=16):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        bold = isinstance(item, tuple)
        p.text = item[0] if bold else item
        p.font.size = Pt(size)
        p.font.bold = bold
        p.space_after = Pt(10)
    return tb


def _style_chart(chart, legend=True, number_format=None):
    chart.font.size = Pt(11)
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
    if number_format and hasattr(chart, "value_axis"):
        chart.value_axis.tick_labels.number_format = number_format
        chart.value_axis.tick_labels.number_format_is_linked = False
        chart.value_axis.has_major_gridlines = False


def _callout(slide, text, left=9.4, top=1.9, width=3.5, height=4.6):
    box = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0xF1, 0xF4, 0xF8)
    box.line.color.rgb = NAVY
    tf = box.text_frame
    tf.word_wrap = True
    for i, t in enumerate(text):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = t
        p.font.size, p.font.color.rgb = Pt(13), NAVY
        p.space_after = Pt(8)
        p.alignment = PP_ALIGN.LEFT


def storyline(res) -> dict:
    """All the numbers and sentences the deck and memo need."""
    b, sz = res["base"], res["sizing"]
    proj = res["projections"]
    fx = b.fx / 1e7
    t = {s: p.iloc[-1] for s, p in proj.items()}
    gap_inc = (b.oop_pct - b.income_implied_oop) * 100
    gap_peer = (b.oop_pct - b.peer_median_oop) * 100
    central = t["Peer convergence"]
    top_driver = res["sensitivity"].iloc[0]
    has_gap = gap_peer > 0 or gap_inc > 0
    s = {
        "base_year": b.year, "oop_pct": b.oop_pct, "peer_median": b.peer_median_oop,
        "income_implied": b.income_implied_oop, "gap_income_pts": gap_inc, "gap_peer_pts": gap_peer,
        "oop_inr_cr": sz["oop_usd"] * fx, "insurable_inr_cr": sz["insurable_oop_usd"] * fx,
        "premium_eq_inr_cr": sz["premium_equivalent_usd"] * fx, "che_inr_cr": sz["che_total_usd"] * fx,
        "central_premium_cr": central["premium_inr_cr"], "central_client_cr": central["client_premium_inr_cr"],
        "income_premium_cr": t["Income-implied"]["premium_inr_cr"],
        "income_client_cr": t["Income-implied"]["client_premium_inr_cr"],
        "top_driver": top_driver["driver"], "top_driver_low": top_driver["result_low"],
        "top_driver_high": top_driver["result_high"], "has_gap": has_gap,
    }
    rel = lambda g: f"{abs(g):.0f} pts {'above' if g > 0 else 'below'}"  # noqa: E731
    s["title_benchmark"] = (f"Indians pay {b.oop_pct:.0%} of health spending out of pocket, "
                            f"{rel(gap_peer)} the peer median")
    s["title_income"] = f"India's out-of-pocket share is {rel(gap_inc)} what its income level predicts"
    s["title_sizing"] = (f"Today's insurable out-of-pocket spend implies a premium pool of about "
                         f"{inr_cr(s['premium_eq_inr_cr'])}")
    s["title_scenarios"] = (f"Converging to peers would create about {inr_cr(s['central_premium_cr'])} of new "
                            f"private premium by {config.TARGET_YEAR}" if central["premium_inr_cr"] > 0 else
                            f"On these data, peer convergence creates no incremental premium by {config.TARGET_YEAR}")
    s["title_client"] = (f"A {res['assumptions']['client_share']:.0%} share would be worth about "
                         f"{inr_cr(s['central_client_cr'])} of annual premium for the client by {config.TARGET_YEAR}")
    s["title_sens"] = f"The answer is most sensitive to: {top_driver['driver'].lower()}"
    return s


def build_deck(res, path, sample_mode=False):
    s = storyline(res)
    b = res["base"]
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    n = 0

    def new():
        nonlocal n
        n += 1
        return prs.slides.add_slide(blank)

    # 1. Title
    sl = new()
    tb = sl.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(11.5), Inches(2.5))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = "Closing India's health protection gap"
    tf.paragraphs[0].font.size, tf.paragraphs[0].font.bold = Pt(40), True
    tf.paragraphs[0].font.color.rgb = NAVY
    p = tf.add_paragraph()
    p.text = f"Sizing the retail health insurance opportunity for a mid-size insurer to {config.TARGET_YEAR}"
    p.font.size, p.font.color.rgb = Pt(20), GREY
    p = tf.add_paragraph()
    p.text = "Independent case study | Public data only"
    p.font.size, p.font.color.rgb = Pt(14), GREY
    if sample_mode:
        p = tf.add_paragraph()
        p.text = "SYNTHETIC SAMPLE DATA - NOT REAL RESULTS"
        p.font.size, p.font.bold, p.font.color.rgb = Pt(18), True, RED

    # 2. Executive summary
    sl = new()
    _title(sl, "Executive summary")
    _bullets(sl, [
        ("Situation",),
        f"In {s['base_year']}, {s['oop_pct']:.0%} of India's health spending was paid out of pocket, vs a peer median of "
        f"{s['peer_median']:.0%}. That is roughly {inr_cr(s['oop_inr_cr'])} a year paid directly by households.",
        ("Opportunity",),
        f"About {inr_cr(s['insurable_inr_cr'])} of that is insurable (assumption: {res['assumptions']['insurable_share']:.0%}), "
        f"equivalent to a premium pool of {inr_cr(s['premium_eq_inr_cr'])}.",
        f"If OOP converges to the peer median by {config.TARGET_YEAR}, new private premium is about "
        f"{inr_cr(s['central_premium_cr'])} (income-implied case: {inr_cr(s['income_premium_cr'])}).",
        ("So what for the client",),
        f"At a {res['assumptions']['client_share']:.0%} share: about {inr_cr(s['central_client_cr'])} of annual premium by "
        f"{config.TARGET_YEAR}. The biggest swing factor is {s['top_driver'].lower()}, so validate it first.",
    ], size=15)
    _footer(sl, n=n)

    # 3. Peer benchmark (bar)
    sl = new()
    _title(sl, s["title_benchmark"], f"Out-of-pocket expenditure, % of current health expenditure (latest year up to {b.year})")
    bm = res["benchmark"]
    cd = CategoryChartData()
    cd.categories = list(bm["name"])
    cd.add_series("OOP % of health spending", [v / 100 for v in bm["oop_pct_che"]])
    gf = sl.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(1.6), Inches(8.6), Inches(5.3), cd)
    ch = gf.chart
    _style_chart(ch, legend=False, number_format="0%")
    ch.plots[0].has_data_labels = True
    ch.plots[0].data_labels.number_format, ch.plots[0].data_labels.number_format_is_linked = "0%", False
    ch.category_axis.reverse_order = True
    for i, iso in enumerate(bm["iso3"]):
        pt = ch.plots[0].series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = RED if iso == config.FOCUS else GREY
    _callout(sl, [f"India: {s['oop_pct']:.0%}", f"Peer median: {s['peer_median']:.0%}",
                  f"Gap: {s['gap_peer_pts']:+.0f} pts",
                  "High OOP means households carry health shocks themselves, which is the core protection gap."])
    _footer(sl, n=n)

    # 4. Income regression (scatter)
    sl = new()
    reg = res["regression"]
    _title(sl, s["title_income"],
           f"OOP share vs GDP per capita (PPP, log scale), {b.reg_n} countries; line = cross-country fit (R² {b.reg_r2:.2f})")
    xy = XyChartData()
    others = reg[~reg["iso3"].isin([config.FOCUS] + config.PEERS)]
    for label, d in [("Other countries", others), ("Peers", reg[reg["iso3"].isin(config.PEERS)]),
                     ("India", reg[reg["iso3"] == config.FOCUS])]:
        ser = xy.add_series(label)
        for _, r in d.iterrows():
            ser.add_data_point(r["gdp_pc_ppp"], r["oop_pct_che"] / 100)
    fit = xy.add_series("Fit")
    for x in np.geomspace(reg["gdp_pc_ppp"].min(), reg["gdp_pc_ppp"].max(), 30):
        fit.add_data_point(float(x), float(b.reg_intercept + b.reg_slope * np.log(x)))
    gf = sl.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(0.5), Inches(1.6), Inches(8.6), Inches(5.3), xy)
    ch = gf.chart
    _style_chart(ch, number_format="0%")
    ch.category_axis.axis_title.text_frame.text = "GDP per capita, PPP (log scale)"
    scaling = ch.category_axis._element.find(qn("c:scaling"))
    log = scaling.makeelement(qn("c:logBase"), {"val": "10"})
    scaling.insert(0, log)
    colors = [GREY, TEAL, RED, NAVY]
    for ser, col in zip(ch.plots[0].series, colors):
        ser.marker.style = XL_MARKER_STYLE.CIRCLE
        ser.marker.format.fill.solid()
        ser.marker.format.fill.fore_color.rgb = col
        ser.format.line.fill.background()
        ser.marker.size = 11 if col == RED else 6
    fit_ser = ch.plots[0].series[3]
    fit_ser.marker.style = XL_MARKER_STYLE.NONE
    fit_ser.format.line.fill.solid()
    fit_ser.format.line.color.rgb = NAVY
    _callout(sl, [f"India actual: {s['oop_pct']:.0%}", f"Income-implied: {s['income_implied']:.0%}",
                  f"Gap: {s['gap_income_pts']:+.0f} pts",
                  "Reading: richer countries pool more health risk. The gap is a policy and market-design gap, "
                  "not just an income gap."])
    _footer(sl, n=n)

    # 5. Base-year sizing
    sl = new()
    _title(sl, s["title_sizing"], f"Top-down sizing, {b.year}, INR crore")
    cd = CategoryChartData()
    cd.categories = ["Total health spend", "Out-of-pocket", "Insurable OOP", "Premium equivalent"]
    cd.add_series("INR crore", [s["che_inr_cr"], s["oop_inr_cr"], s["insurable_inr_cr"], s["premium_eq_inr_cr"]])
    gf = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.5), Inches(1.6), Inches(8.6), Inches(5.3), cd)
    ch = gf.chart
    _style_chart(ch, legend=False, number_format="#,##0")
    ch.plots[0].has_data_labels = True
    ch.plots[0].data_labels.number_format, ch.plots[0].data_labels.number_format_is_linked = "#,##0", False
    for i, col in enumerate([GREY, NAVY, TEAL, TEAL]):
        pt = ch.plots[0].series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = col
    a = res["assumptions"]
    _callout(sl, ["Logic:", "Population x health spend per capita = total",
                  f"x OOP share ({b.oop_pct:.0%}) = out-of-pocket",
                  f"x insurable share ({a['insurable_share']:.0%}, assumption) = insurable",
                  f"÷ loss ratio ({a['loss_ratio']:.0%}, assumption) = premium needed"])
    _footer(sl, n=n)

    # 6. Scenarios over time (line)
    sl = new()
    _title(sl, s["title_scenarios"], f"Incremental private health premium by scenario, INR crore, {b.year}-{config.TARGET_YEAR}")
    cd = CategoryChartData()
    years = list(res["projections"]["Status quo"]["year"])
    cd.categories = [str(y) for y in years]
    for scen, p in res["projections"].items():
        cd.add_series(scen, list(p["premium_inr_cr"]))
    gf = sl.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.5), Inches(1.6), Inches(8.6), Inches(5.3), cd)
    ch = gf.chart
    _style_chart(ch, number_format="#,##0")
    for ser, col in zip(ch.plots[0].series, [GREY, NAVY, TEAL]):
        ser.format.line.color.rgb = col
        ser.format.line.width = Pt(2.5)
    capped = [k for k, p in res["projections"].items()
              if p.iloc[-1]["oop_shift_usd"] > 0 and abs(p.iloc[-1]["oop_shift_usd"] - p.iloc[-1]["che_total_usd"]
                                                          * b.oop_pct * res["assumptions"]["insurable_share"]) < 1]
    note = ([f"Capped at the insurable pool in: {', '.join(capped)}. Insurance can only absorb insurable spend, "
             "so these cases converge."] if capped else [])
    _callout(sl, [f"{k}: {v}" for k, v in config.SCENARIOS.items()] +
             [f"Health spend per capita grows {b.g_che_pc:.1%} p.a. and population {b.g_pop:.1%} p.a. "
              f"(last {config.CAGR_YEARS}-year CAGRs)."] + note)
    _footer(sl, n=n)

    # 7. Client opportunity
    sl = new()
    _title(sl, s["title_client"], f"Client premium opportunity in {config.TARGET_YEAR}, INR crore")
    cd = CategoryChartData()
    cd.categories = list(res["projections"])
    cd.add_series("Client premium", [p.iloc[-1]["client_premium_inr_cr"] for p in res["projections"].values()])
    gf = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.5), Inches(1.6), Inches(8.6), Inches(5.3), cd)
    ch = gf.chart
    _style_chart(ch, legend=False, number_format="#,##0")
    ch.plots[0].series[0].format.fill.solid()
    ch.plots[0].series[0].format.fill.fore_color.rgb = NAVY
    ch.plots[0].has_data_labels = True
    ch.plots[0].data_labels.number_format, ch.plots[0].data_labels.number_format_is_linked = "#,##0", False
    _callout(sl, [f"Assumes the client wins {a['client_share']:.0%} of new private premium and private insurers "
                  f"capture {a['private_capture']:.0%} of the OOP shift (the rest goes to government schemes).",
                  "Benchmark this against the client's current retail premium to judge ambition."])
    _footer(sl, n=n)

    # 8. Sensitivity tornado
    sl = new()
    sens = res["sensitivity"]
    _title(sl, s["title_sens"], f"Client premium in {config.TARGET_YEAR} (Peer convergence), low vs high case, INR crore")
    cd = CategoryChartData()
    cd.categories = list(sens["driver"])
    cd.add_series("Low case", list(sens["result_low"] - sens["central"]))
    cd.add_series("High case", list(sens["result_high"] - sens["central"]))
    gf = sl.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(1.6), Inches(8.6), Inches(5.3), cd)
    ch = gf.chart
    _style_chart(ch, number_format="#,##0")
    ch.plots[0].overlap = 100
    ch.category_axis.reverse_order = True
    ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    for ser, col in zip(ch.plots[0].series, [RED, TEAL]):
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = col
    _callout(sl, [f"Central case: {inr_cr(sens['central'].iloc[0])}",
                  "Bars show the change vs central when one driver moves to its low or high case.",
                  "A driver with zero swing is not binding in this scenario."])
    _footer(sl, n=n)

    # 9. Recommendations (framed as hypotheses to test)
    sl = new()
    _title(sl, "Recommended next steps: validate the three biggest assumptions, then choose where to play")
    _bullets(sl, [
        ("1. Validate the size of the prize (weeks 1-2)",),
        "Replace the insurable-share and loss-ratio assumptions with National Health Accounts and IRDAI figures. "
        "Complete the bottom-up check in the Excel model.",
        ("2. Where to play (weeks 2-4)",),
        "Hypothesis to test: the gap is largest outside the metros, where OOP is high and retail penetration is low. "
        "This needs state-level NSS / NFHS and insurer distribution data.",
        ("3. How to win (weeks 4-6)",),
        "Hypothesis to test: low-ticket hospitalisation and top-up products sold through bancassurance and digital "
        "partners can reach price-sensitive households. Test with unit economics (CAC, claims ratio, persistency).",
        ("4. Risks to monitor",),
        "Expansion of government schemes reduces the private share. Medical inflation pushes up loss ratios. "
        "Mis-selling and regulatory changes affect distribution.",
    ], size=14)
    _footer(sl, "These are hypotheses for the next phase, not conclusions from this model.", n=n)

    # 10. Appendix: methodology & assumptions
    sl = new()
    _title(sl, "Appendix: methodology, data and assumptions")
    rows = [("Item", "Value", "Basis")]
    rows += [("Data year", str(b.year), "Latest year with complete World Bank data for India"),
             ("Peers", ", ".join(config.PEERS), "Emerging markets with comparable income or size"),
             ("Income-implied OOP", f"{b.income_implied_oop:.1%}", f"OLS of OOP share on ln(GDP pc PPP), n={b.reg_n}"),
             ("Growth", f"CHE pc {b.g_che_pc:.1%}, pop {b.g_pop:.1%}", f"{config.CAGR_YEARS}-year CAGRs; constant FX {b.fx:.1f}")]
    rows += [(spec["label"], f"{spec['value']:.0%} ({spec['low']:.0%}-{spec['high']:.0%})",
              "ASSUMPTION. " + spec["source"].split(". ", 1)[-1]) for spec in config.ASSUMPTIONS.values()]
    tbl = sl.shapes.add_table(len(rows), 3, Inches(0.5), Inches(1.7), Inches(12.3), Inches(4.8)).table
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            cell = tbl.cell(i, j)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(10 if i else 12)
            cell.text_frame.paragraphs[0].font.bold = i == 0
    tbl.columns[0].width, tbl.columns[1].width, tbl.columns[2].width = Inches(4.4), Inches(2.6), Inches(5.3)
    _footer(sl, SOURCE + ". Indicator codes: " + ", ".join(list(config.INDICATORS)[:6]) + ".", n=n)

    path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(path)
    return s
