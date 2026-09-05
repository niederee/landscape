"""Optional real-browser checks: install the browser extra and Chromium first."""

from pathlib import Path
import os
import shutil

import pytest

from landscape_planner.io.yaml_loader import load_project
from landscape_planner.rendering.html import render_existing_conditions_html


REQUIRE_BROWSER = os.environ.get("LANDSCAPE_REQUIRE_BROWSER") == "1"
if REQUIRE_BROWSER:
    from playwright import sync_api as playwright
else:
    playwright = pytest.importorskip("playwright.sync_api")


@pytest.fixture
def browser():
    with playwright.sync_playwright() as runtime:
        try:
            instance = runtime.chromium.launch()
        except playwright.Error as exc:
            if "Executable doesn't exist" in str(exc):
                if REQUIRE_BROWSER:
                    pytest.fail("Required Chromium is absent; run: playwright install chromium")
                pytest.skip("Install Chromium with: playwright install chromium")
            raise
        yield instance
        instance.close()


def test_file_url_works_offline_with_controls_and_safe_inspection(tmp_path, browser):
    project = load_project(Path("tests/fixtures/synthetic"))
    hostile = '</script><img src="https://invalid.example/x" onerror="alert(1)">'
    project.existing_conditions.structures[0].name = hostile
    original = render_existing_conditions_html(project, tmp_path / "original/plan.html")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    output = unrelated / "plan.html"
    shutil.copyfile(original, output)
    shutil.rmtree(original.parent)
    context = browser.new_context(offline=True)
    requests = []
    errors = []
    page = context.new_page()
    page.on("request", lambda request: requests.append(request.url))
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.goto(output.as_uri())
    assert page.locator("html").get_attribute("class") == "enhanced"
    svg = page.locator("#viewport svg")
    initial = svg.get_attribute("viewBox")
    page.locator("#zoom-in").click()
    assert svg.get_attribute("viewBox") != initial
    page.locator("#fit").click()
    assert svg.get_attribute("viewBox") == initial

    original_box = [float(value) for value in initial.split()]
    page.get_by_role("button", name="Pan right", exact=True).click()
    panned_box = [float(value) for value in svg.get_attribute("viewBox").split()]
    assert panned_box[0] > original_box[0]
    assert panned_box[1:] == original_box[1:]
    page.get_by_role("button", name="Pan down", exact=True).click()
    assert float(svg.get_attribute("viewBox").split()[1]) > original_box[1]
    page.locator("#fit").click()
    assert svg.get_attribute("viewBox") == initial

    toggle = page.locator("input[data-layer]").first
    layer = page.locator("#" + toggle.get_attribute("data-layer"))
    toggle.uncheck()
    assert layer.get_attribute("hidden") is not None
    toggle.check()
    assert layer.get_attribute("hidden") is None

    page.locator("#search").fill("HOUSE001")
    assert page.locator("#entity-list button:visible").count() == 1
    page.locator('#entity-list button[data-entity-id="HOUSE001"]').click()
    inspector = page.locator("#inspector").inner_text()
    assert hostile in inspector
    assert "2,475" in inspector
    assert "Confidence:" in inspector
    assert page.locator("img").count() == 0
    page.locator("#search").fill("")
    feature = page.locator('#viewport [data-entity-id="TREE001"]').first
    feature.focus()
    page.keyboard.press("Enter")
    assert "TREE001" in page.locator("#inspector").inner_text()

    # On a phone-width viewport, the alternative to tiny SVG targets stays usable.
    page.set_viewport_size({"width": 390, "height": 844})
    page.locator("#search").fill("DOES_NOT_EXIST")
    assert page.locator("#entity-list button:visible").count() == 0
    page.locator("#search").fill("TREE001")
    page.locator('#entity-list button[data-entity-id="TREE001"]').click()
    assert "TREE001" in page.locator("#inspector").inner_text()
    page.locator("#fit").click()
    assert svg.get_attribute("viewBox") == initial
    assert svg.is_visible()
    page.emulate_media(media="print")
    assert not page.locator("#zoom-in").is_visible()
    assert svg.is_visible()
    assert not errors
    assert not [url for url in requests if url.startswith(("http:", "https:"))]
    context.close()


def test_file_url_retains_plan_and_quantities_without_javascript(tmp_path, browser):
    output = render_existing_conditions_html(
        load_project(Path("tests/fixtures/synthetic")), tmp_path / "plan.html"
    )
    context = browser.new_context(java_script_enabled=False, offline=True)
    page = context.new_page()
    page.goto(output.as_uri())
    assert page.locator("#viewport svg").is_visible()
    assert page.locator("table").first.is_visible()
    assert "2,475" in page.locator("body").inner_text()
    assert "Measurement provenance" in page.locator("body").inner_text()
    assert "manual_estimate" in page.locator("table").nth(1).inner_text()
    assert "unknown" in page.locator("table").nth(1).inner_text()
    assert not page.locator("#zoom-in").is_visible()
    context.close()
