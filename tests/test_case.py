import shutil
import subprocess
import sys
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from hpg import analysis, config, deck, excel_model, worldbank  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return analysis.run(worldbank.make_sample())


def test_cagr():
    s = pd.Series([100.0, 110.0, 121.0], index=[2020, 2021, 2022])
    assert analysis.cagr(s, 10) == pytest.approx(0.10)


def test_oop_path_is_linear_and_stops_at_target(res):
    b = res["base"]
    assert analysis.oop_path(b, 0.2, b.year) == pytest.approx(b.oop_pct)
    assert analysis.oop_path(b, 0.2, config.TARGET_YEAR) == pytest.approx(0.2)
    assert analysis.oop_path(b, 0.2, config.TARGET_YEAR + 5) == pytest.approx(0.2)


def test_status_quo_has_no_incremental_premium(res):
    assert res["projections"]["Status quo"]["premium_usd"].abs().sum() == 0


def test_shift_never_exceeds_insurable_pool(res):
    b, a = res["base"], res["assumptions"]
    for p in res["projections"].values():
        pool = p["che_total_usd"] * b.oop_pct * a["insurable_share"]
        assert (p["oop_shift_usd"] <= pool + 1e-6).all()


def test_premium_chain(res):
    a = res["assumptions"]
    last = res["projections"]["Peer convergence"].iloc[-1]
    assert last["premium_usd"] == pytest.approx(last["oop_shift_usd"] * a["private_capture"] / a["loss_ratio"])
    assert last["client_premium_usd"] == pytest.approx(last["premium_usd"] * a["client_share"])


def test_sensitivity_moves_in_expected_direction(res):
    sens = res["sensitivity"].set_index("driver")
    assert sens.loc["Client market share", "result_high"] > sens.loc["Client market share", "result_low"]
    assert sens.loc["Loss ratio", "result_high"] < sens.loc["Loss ratio", "result_low"]  # premium = claims / LR


def test_storyline_titles_reflect_numbers(res):
    s = deck.storyline(res)
    assert ("above" in s["title_benchmark"]) == (s["gap_peer_pts"] > 0)
    assert f"{s['oop_pct']:.0%}" in s["title_benchmark"]


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice not installed")
def test_excel_formulas_match_python(res, tmp_path):
    """Recalculate the workbook in LibreOffice and compare with the Python engine."""
    src = tmp_path / "model.xlsx"
    anchors = excel_model.build_workbook(res, src)
    out = tmp_path / "recalc"
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(out), str(src)],
                   check=True, capture_output=True, timeout=180)
    wb = openpyxl.load_workbook(out / "model.xlsx", data_only=True)
    ws = wb["Projection"]
    for scen, row in anchors.items():
        py = res["projections"][scen].iloc[-1]
        assert ws[f"M{row}"].value == pytest.approx(py["premium_inr_cr"], rel=1e-9, abs=1e-6)
        assert ws[f"N{row}"].value == pytest.approx(py["client_premium_inr_cr"], rel=1e-9, abs=1e-6)
    sizing = res["sizing"]
    assert wb["Sizing"]["B5"].value == pytest.approx(sizing["premium_equivalent_usd"], rel=1e-9)
