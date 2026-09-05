"""Actual standalone file acceptance for comparison, CSP and snapshot navigation."""
from pathlib import Path
import os

import pytest

from landscape_planner.io.yaml_loader import load_project
from landscape_planner.rendering.comparison import comparison_html

REQUIRE_BROWSER = os.environ.get('LANDSCAPE_REQUIRE_BROWSER') == '1'
if REQUIRE_BROWSER:
    from playwright import sync_api as playwright
else:
    playwright = pytest.importorskip('playwright.sync_api')


@pytest.fixture
def browser():
    with playwright.sync_playwright() as runtime:
        try:
            instance = runtime.chromium.launch()
        except playwright.Error as exc:
            if "Executable doesn't exist" in str(exc):
                if REQUIRE_BROWSER:
                    pytest.fail('Required Chromium is absent; run: playwright install chromium')
                pytest.skip('Install Chromium with: playwright install chromium')
            raise
        yield instance
        instance.close()


def make_file(tmp_path):
    base = load_project(Path('tests/fixtures/synthetic'))
    proposed = base.model_copy(deep=True)
    proposed.existing_conditions.trees = []
    hostile = '</iframe><script>alert(1)</script><img src="https://invalid.example">'
    result = tmp_path / 'copied-review.html'
    result.write_text(comparison_html([
        ('existing', 'Baseline', base), ('option', hostile, proposed),
        ('second', 'Second alternative', base.model_copy(deep=True)),
    ]), encoding='utf-8')
    return result


def test_offline_comparison_preserves_world_frame_and_selection(tmp_path, browser):
    output = make_file(tmp_path)
    context = browser.new_context(offline=True)
    page = context.new_page()
    errors, requests = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
    page.on('request', lambda request: requests.append(request.url))
    page.goto(output.as_uri())
    baseline = page.frame_locator('#snapshot-0 iframe')
    proposed = page.frame_locator('#snapshot-1 iframe')
    baseline.locator('#zoom-in').wait_for(state='visible')
    assert page.locator('img').count() == 0
    house = baseline.locator('#viewport [data-entity-id="HOUSE001"]').first.get_attribute('points')
    assert house
    assert proposed.locator('#viewport [data-entity-id="HOUSE001"]').first.get_attribute('points') == house
    baseline.locator('#entity-list button[data-entity-id="TREE001"]').click()
    page.locator('#snapshot-left').select_option('1')
    assert 'TREE001: not present' in proposed.locator('#inspector').inner_text()
    page.locator('#paired').check()
    page.locator('#snapshot-right').select_option('0')
    assert baseline.locator('#viewport svg').is_visible()
    assert proposed.locator('#viewport svg').is_visible()
    proposed.locator('#zoom-in').click()
    playwright.expect(baseline.locator('#viewport svg')).to_have_attribute('viewBox', proposed.locator('#viewport svg').get_attribute('viewBox'))
    width = float(proposed.locator('#viewport svg').get_attribute('viewBox').split()[2])
    baseline.locator('#zoom-in').click()
    expected = width * 0.8
    playwright.expect(proposed.locator('#viewport svg')).to_have_attribute('viewBox', baseline.locator('#viewport svg').get_attribute('viewBox'))
    assert float(baseline.locator('#viewport svg').get_attribute('viewBox').split()[2]) == pytest.approx(expected)
    page.locator('#snapshot-left').select_option('2')
    third = page.frame_locator('#snapshot-2 iframe')
    assert 'TREE001' in third.locator('#inspector').inner_text()
    assert 'not present' not in third.locator('#inspector').inner_text()
    assert not errors
    assert not [url for url in requests if url.startswith(('http:', 'https:'))]
    context.close()


def test_no_javascript_keeps_baseline_quantities_and_provenance(tmp_path, browser):
    context = browser.new_context(java_script_enabled=False, offline=True)
    page = context.new_page()
    page.goto(make_file(tmp_path).as_uri())
    baseline = page.frame_locator('#snapshot-0 iframe')
    assert baseline.locator('#viewport svg').is_visible()
    assert 'Whole-plan quantities' in baseline.locator('body').inner_text()
    assert 'Measurement provenance' in baseline.locator('body').inner_text()
    assert not page.locator('#snapshot-1').is_visible()
    assert not page.locator('#snapshot-left').is_visible()
    context.close()
