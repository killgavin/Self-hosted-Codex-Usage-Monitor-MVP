"""Static regression prerequisites for the real-browser T-63 layout check."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_mobile_viewport_and_single_column_rules_are_present() -> None:
    html = (ROOT / "web" / "index.html").read_text()
    css = (ROOT / "web" / "assets" / "styles.css").read_text()

    assert 'name="viewport"' in html
    assert 'width=device-width' in html
    assert "@media (max-width: 40rem)" in css
    mobile = css.split("@media (max-width: 40rem)", 1)[1]
    assert "grid-template-columns: minmax(0, 1fr)" in mobile
    assert "flex-direction: column" in mobile


def test_mobile_css_contains_overflow_guards() -> None:
    css = (ROOT / "web" / "assets" / "styles.css").read_text()

    assert "box-sizing: border-box" in css
    assert "min-width: 0" in css
    assert "overflow-wrap: anywhere" in css
    assert ".rate-limit-window progress { width: 100%; }" in css


def test_real_browser_fixture_checks_exact_360px_overflow_metrics() -> None:
    fixture = ROOT / "server" / "tests" / "fixtures" / "mobile_layout_browser.mjs"
    source = fixture.read_text()

    assert "width: 360" in source
    assert "rootScrollWidth > metrics.rootClientWidth" in source
    assert "bodyScrollWidth > metrics.bodyClientWidth" in source
    assert "very-long-unknown-limit-identifier" in source
