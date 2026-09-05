"""Portable, deterministic review documents over the existing SVG renderer.

No source assets are embedded. The share profile deliberately projects metadata
before rendering; it is a minimized plan, not an anonymization guarantee.
"""
from __future__ import annotations

import base64
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET

from landscape_planner import __version__
from landscape_planner.analysis.constraints import constraint_shape
from landscape_planner.analysis.validation import ValidationResult, validate_project
from landscape_planner.estimating.quantities import existing_condition_quantities, format_quantity, summarize_quantities
from landscape_planner.model.project import LandscapeProject
from landscape_planner.rendering.svg import existing_conditions_svg

_LAYERS = (
    ("10_property", "Property boundary"),
    ("20_existing_structures", "Structures · gray"),
    ("30_existing_hardscape", "Hardscape and linear features · tan"),
    ("40_existing_vegetation", "Vegetation · green / brown"),
    ("45_existing_utilities", "Utilities and clearances · amber"),
    ("50_site_constraints", "Scoped exclusions · red"),
    ("55_existing_fences", "Actual fences · purple"),
)

_CSS = """
*{box-sizing:border-box}body{margin:0;background:#f4f5f0;color:#202923;font:16px system-ui,sans-serif}
header,footer{overflow-wrap:anywhere;padding:20px 28px;background:#173f35;color:#fff}h1{margin:0;font-size:1.6rem}h2{font-size:1.1rem}
main{padding:20px;max-width:1800px;margin:auto}.layout{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:20px}
.card{background:white;border:1px solid #ccd5cd;border-radius:8px;padding:16px;margin-bottom:16px}
#viewport{overflow:hidden;touch-action:none}#viewport svg{width:100%;height:auto;display:block;min-height:280px;max-height:75vh}
button,input{font:inherit}button{padding:7px 12px;border:1px solid #73877b;border-radius:4px;background:#fff;cursor:pointer}
button:focus-visible,input:focus-visible,[data-entity-id]:focus-visible{outline:3px solid #126bd3;outline-offset:2px}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}.layers label{display:block;margin:8px 0}
#entity-list{max-height:310px;overflow:auto;list-style:none;padding:0}#entity-list button{width:100%;text-align:left;margin:3px 0}
#entity-list button[aria-pressed=true]{background:#dce9ff;border-color:#126bd3}#search{width:100%;padding:8px}
#inspector{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.55}table{width:100%;border-collapse:collapse}
th,td{text-align:left;border-bottom:1px solid #ddd;padding:8px}small,.muted{color:#506058}.notice{border-left:4px solid #b48624}
.js-only{display:none}.enhanced .js-only{display:block}.enhanced .toolbar.js-only{display:flex}
svg .label,svg .utility-clearance{pointer-events:none}svg [data-entity-id]{cursor:pointer}svg .selected{filter:drop-shadow(0 0 4px #146dde)}
svg [hidden]{display:none}#entity-list [hidden]{display:none}
@media(max-width:850px){.layout{grid-template-columns:1fr}header,footer{padding:16px}main{padding:10px}}
@media print{header,footer{background:white;color:black}.js-only,aside{display:none!important}.layout{display:block}
svg [hidden]{display:initial}#viewport svg{max-height:none;min-height:0}.card{break-inside:avoid}body{background:white}}
"""

_JS = """'use strict';
(() => {
 const data = JSON.parse(document.getElementById('plan-data').textContent);
 const viewport = document.getElementById('viewport');
 const svg = viewport.querySelector('svg');
 const inspector = document.getElementById('inspector');
 const features = Array.from(svg.querySelectorAll('[data-entity-id]'));
 const buttons = Array.from(document.querySelectorAll('#entity-list button'));
 const entities = new Map(data.entities.map(e => [e.id, e]));
 const initial = [0, 0, 1632, 1056]; let box = initial.slice(); let drag = null;
 function draw() { svg.setAttribute('viewBox', box.join(' ')); }
 window.addEventListener('landscape-camera', e => {
   const next = e.detail;
   if (Array.isArray(next) && next.length === 4 && next.every(Number.isFinite) && next[2] > 0 && next[3] > 0) {
     box = next.slice(); draw();
   }
 });
 function select(id) {
   const e = entities.get(id); if (!e) return;
   features.forEach(n => n.classList.toggle('selected', n.dataset.entityId === id));
   buttons.forEach(n => n.setAttribute('aria-pressed', String(n.dataset.entityId === id)));
   const lines = [e.name + ' (' + e.id + ')', 'Type: ' + e.type,
     'Source: ' + e.source, 'Confidence: ' + e.confidence,
     'Estimated accuracy: ' + (e.accuracy_ft == null ? 'unknown' : e.accuracy_ft + ' ft')];
   if (e.applies_to) lines.push('Excludes: ' + e.applies_to.join(', ') + ' only');
   if (e.edge_index != null) lines.push('Property boundary edge index: ' + e.edge_index);
   if (e.placement) lines.push('Placement: ' + e.placement);
   e.measurements.forEach(m => lines.push(m));
   if (!e.measurements.length) lines.push('Measurements: not supplied');
   e.warnings.forEach(w => lines.push('Validation: ' + w));
   if (e.notes) e.notes.forEach(n => lines.push('Note: ' + n));
   if (e.source_reference) lines.push('Source reference: ' + e.source_reference);
   inspector.textContent = lines.join('\\n');
 }
 features.forEach(n => {
   n.addEventListener('click', () => { if (!drag || !drag.moved) select(n.dataset.entityId); });
   n.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') {
     e.preventDefault(); select(n.dataset.entityId); } });
 });
 buttons.forEach(n => n.addEventListener('click', () => select(n.dataset.entityId)));
 document.getElementById('search').addEventListener('input', e => {
   const q = e.target.value.toLocaleLowerCase();
   buttons.forEach(b => { b.parentElement.hidden = !b.textContent.toLocaleLowerCase().includes(q); });
 });
 document.querySelectorAll('[data-layer]').forEach(n => n.addEventListener('change', () => {
   const layer = document.getElementById(n.dataset.layer);
   if (n.checked) layer.removeAttribute('hidden'); else layer.setAttribute('hidden', '');
 }));
 function zoom(factor) {
   const width = Math.max(initial[2] / 12, Math.min(initial[2] * 3, box[2] * factor));
   const ratio = width / box[2];
   box = [box[0] + box[2] * (1-ratio)/2, box[1] + box[3] * (1-ratio)/2, width, box[3] * ratio]; draw();
 }
 document.getElementById('zoom-in').addEventListener('click', () => zoom(0.8));
 document.getElementById('zoom-out').addEventListener('click', () => zoom(1.25));
 document.getElementById('fit').addEventListener('click', () => { box = initial.slice(); draw(); });
 document.querySelectorAll('[data-pan]').forEach(n => n.addEventListener('click', () => {
   const d = n.dataset.pan; box[0] += (d==='left' ? -1 : d==='right' ? 1 : 0)*box[2]/8;
   box[1] += (d==='up' ? -1 : d==='down' ? 1 : 0)*box[3]/8; draw();
 }));
 svg.addEventListener('pointerdown', e => {
   if (e.button !== 0) return;
   const matrix = svg.getScreenCTM(); if (!matrix) return;
   drag = {x:e.clientX,y:e.clientY,box:box.slice(),scale:matrix.a,moved:false};
 });
 window.addEventListener('pointermove', e => {
   if (!drag || !e.buttons) return;
   const dx = e.clientX-drag.x, dy=e.clientY-drag.y;
   if (Math.abs(dx)+Math.abs(dy)>4) drag.moved=true;
   box = [drag.box[0]-dx/drag.scale,drag.box[1]-dy/drag.scale,drag.box[2],drag.box[3]]; draw();
 });
 window.addEventListener('pointerup', () => { setTimeout(() => {drag=null;}, 0); });
 window.addEventListener('pointercancel', () => {drag=null;});
 window.addEventListener('beforeprint', () => {svg.setAttribute('viewBox', initial.join(' '));});
 window.addEventListener('afterprint', draw);
 document.documentElement.classList.add('enhanced');
})();
"""


def render_existing_conditions_html(
    project: LandscapeProject, output_path: str | Path, profile: str = "share",
    validation_result: ValidationResult | None = None,
) -> Path:
    """Write one offline HTML file, after successful rendering and validation."""
    document = existing_conditions_html(project, profile, validation_result)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                         prefix=f".{output.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(document)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return output


def existing_conditions_html(
    project: LandscapeProject, profile: str = "share",
    validation_result: ValidationResult | None = None,
) -> str:
    """Build a minimized share or private document; never embed external assets.

    Callers with source-file access should pass validation including project_root
    so missing referenced assets are checked before export as well.
    """
    if profile not in {"share", "private"}:
        raise ValueError("HTML profile must be 'share' or 'private'.")
    geometry_result = validate_project(project)
    result = validation_result if validation_result is not None else geometry_result
    if not geometry_result.ok or not result.ok:
        raise ValueError("Cannot export HTML: project validation failed.")
    view = project.model_copy(deep=True)
    if profile == "share":
        view.project.name = "Residential landscape review"
        view.project.id = "SHARED_PLAN"
        view.project.location.city = None
        view.project.location.state = None
        view.project.location.country = None
    conditions = view.existing_conditions
    groups = [("parcel", [conditions.parcel])]
    groups += [(key, getattr(conditions, key)) for key in (
        "structures", "hardscape", "linear_features", "lawn", "planting_beds", "trees", "utilities", "site_constraints")]
    entities = []
    for kind, items in groups:
        for item in sorted(items, key=lambda e: e.id):
            measurements = []
            for attr, label, unit in (
                ("area_sqft", "Area", "sqft"), ("length_ft", "Length", "ft"),
                ("perimeter_ft", "Perimeter", "ft"), ("canopy_radius_ft", "Canopy radius", "ft"),
                ("distance_ft", "Exclusion distance from property edge", "ft"),
                ("height_ft", "Height", "ft"), ("trunk_diameter_in", "Trunk diameter", "in"),
            ):
                value = getattr(item, attr, None)
                if value is not None:
                    measurements.append(f"{label}: {format_quantity(value)} {unit}")
            entity = {
                "id": item.id, "name": item.name or item.id, "type": kind,
                "source": item.source.type if item.source else "unknown",
                "confidence": item.source.confidence if item.source else "unknown",
                "accuracy_ft": item.source.estimated_accuracy_ft if item.source else None,
                "measurements": measurements,
                "warnings": [f"{m.severity}: {m.code}" for m in result.messages if m.entity_id == item.id],
            }
            if kind == "site_constraints":
                shape = constraint_shape(item, conditions.parcel.boundary)
                measurements.append(f"Exclusion area: {format_quantity(shape.area)} sqft")
                entity["applies_to"] = item.applies_to
                entity["edge_index"] = item.edge_index
            if kind == "linear_features":
                entity["placement"] = item.placement
            if profile == "private":
                entity["notes"] = item.notes
                entity["source_reference"] = item.source.reference if item.source else None
            entities.append(entity)
    # Parse only application-generated SVG. Namespace DOM IDs independently of
    # user IDs so arbitrary identifiers cannot collide with viewer controls.
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(existing_conditions_svg(view))
    known_ids = {e["id"] for e in entities}
    for index, node in enumerate(root.iter()):
        old_id = node.get("id")
        if old_id is not None:
            node.set("id", f"plan-{old_id}" if old_id in dict(_LAYERS) and node.get("data-entity-id") is None else f"plan-node-{index}")
        entity_id = node.get("data-entity-id")
        if entity_id in known_ids and node.get("class") != "utility-clearance":
            node.set("tabindex", "0")
            node.set("role", "button")
            node.set("aria-label", f"Inspect {entity_id}")
        elif entity_id is not None:
            del node.attrib["data-entity-id"]
    svg = ET.tostring(root, encoding="unicode")
    payload = _safe_json({"profile": profile, "entities": entities, "schema_version": project.schema_version,
                          "exporter_version": __version__, "view_schema_version": 1})
    view_digest = hashlib.sha256((svg + payload).encode("utf-8")).hexdigest()
    source_rows = "".join(
        f'<tr><td>{escape(e["id"])}</td><td>{escape(e["source"])}</td>'
        f'<td>{escape(e["confidence"])}</td><td>{escape(str(e["accuracy_ft"])) + " ft" if e["accuracy_ft"] is not None else "unknown"}</td></tr>'
        for e in entities
    )
    constraint_rows = "".join(
        f'<tr><td>{escape(e["id"])}</td><td>{escape(", ".join(e["applies_to"]))} only</td>'
        f'<td>{escape("; ".join(e["measurements"]))}</td></tr>'
        for e in entities if "applies_to" in e
    )
    constraint_summary = (
        '<h2>Supplied exclusions</h2><p>These exclusions apply only to the listed uses. '
        'Source and confidence are listed above; property edges determine setback distances.</p>'
        '<table><thead><tr><th scope="col">Constraint</th><th scope="col">Excludes</th>'
        '<th scope="col">Dimensions</th></tr></thead><tbody>' + constraint_rows + '</tbody></table>'
    ) if constraint_rows else ""
    layers = "".join(f'<label><input type="checkbox" checked data-layer="plan-{key}"> {escape(label)}</label>' for key, label in _LAYERS)
    entity_list = "".join(f'<li><button type="button" data-entity-id="{escape(e["id"], quote=True)}" aria-pressed="false">{escape(e["name"])} · {escape(e["id"])}</button></li>' for e in entities)
    totals = summarize_quantities(existing_condition_quantities(view))
    rows = "".join(f'<tr><td>{escape(category.replace("_", " "))}</td><td>{format_quantity(quantity)} {unit}</td></tr>' for (category, unit), quantity in totals.items())
    warnings = "".join(f'<li>{escape(m.severity)} · {escape(m.code)}{(" · " + escape(m.entity_id)) if m.entity_id and (profile == "private" or m.entity_id in known_ids) else ""}{(": " + escape(m.message)) if profile == "private" else ""}</li>' for m in result.messages)
    privacy = ("Share profile: geometry and entity labels are included. Project identity, location, internal notes and source files are omitted. Review labels before sharing; this plan is not anonymous."
               if profile == "share" else "Private profile: project identity, location, notes and source references are included. Source files and photographs are not embedded.")
    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="__CSP__">
<title>{escape(view.project.name)} · Existing conditions</title><style>{_CSS}</style></head>
<body><header><h1>{escape(view.project.name)}</h1><p>L1.0 · Existing conditions · Read-only review · Local coordinates in feet</p></header>
<main><section class="card notice"><strong>Planning review — not a construction or survey document.</strong>
<p>Measurements are calculated from supplied geometry and inherit its uncertainty. Confirm dimensions and source accuracy before design or construction. Missing information is unknown, not zero. Supplied exclusions are checked only against their named hardscape subtypes; legal requirements are not independently verified. Drainage, planting suitability, costs and phasing are not evaluated here. Doors, easements, setbacks and rights-of-way are not drawn in this first viewer.</p>
<p>{escape(privacy)}</p><p>Browser printing is for review; verify scale on the fixed-page SVG for scaled output.</p></section>
<div class="layout"><div><section class="card"><h2>Site plan</h2>
<div class="toolbar js-only" aria-label="Plan navigation"><button id="zoom-in" type="button">Zoom in</button><button id="zoom-out" type="button">Zoom out</button><button id="fit" type="button">Fit plan</button>
<button type="button" data-pan="left" aria-label="Pan left">←</button><button type="button" data-pan="right" aria-label="Pan right">→</button><button type="button" data-pan="up" aria-label="Pan up">↑</button><button type="button" data-pan="down" aria-label="Pan down">↓</button></div>
<p class="muted">Legend: gray structures; tan hardscape; green lawn and trees; brown beds; amber utilities and clearances; black parcel boundary; purple actual fences; translucent dashed red exclusions. Red excludes only the listed uses (such as pools), not all landscaping. Exclusion distances use property edges, never fences.</p><p class="muted">Fences are independent of ownership boundaries. Context fences outside the parcel may extend beyond the fixed sheet; verify their full geometry in the source data.</p><p class="js-only muted">Drag to pan. Select a feature or use the searchable list to inspect it.</p><div id="viewport">{svg}</div>
<noscript><p>The default plan, quantities and validation summary remain available. Enable JavaScript for navigation, layers and feature inspection.</p></noscript></section>
<section class="card"><h2>Whole-plan quantities</h2><p>Layer visibility does not change these totals. Categories may overlap; do not add them to infer parcel coverage.</p>
<table><thead><tr><th scope="col">Category</th><th scope="col">Quantity</th></tr></thead><tbody>{rows}</tbody></table></section>
<section class="card"><h2>Validation and source status</h2><p>{len(result.errors)} errors · {len(result.warnings)} warnings · {len(result.infos)} information notices.</p>
<p>Checks cover modeled geometry and references, not site safety or professional approval. Share exports show validation codes; use the original validation report for full details.</p><ul>{warnings}</ul><h2>Measurement provenance</h2><table><thead><tr><th scope="col">Entity</th><th scope="col">Source</th><th scope="col">Confidence</th><th scope="col">Estimated accuracy</th></tr></thead><tbody>{source_rows}</tbody></table>{constraint_summary}</section></div>
<aside class="js-only"><section class="card layers"><h2>Layers / legend</h2>{layers}</section>
<section class="card"><h2>Find a feature</h2><label for="search">Search name or ID</label><input id="search" type="search"><ul id="entity-list">{entity_list}</ul></section>
<section class="card"><h2>Feature details</h2><div id="inspector" aria-live="polite">Select a feature to view its measurements and source confidence.</div></section></aside></div></main>
<footer>Standalone review document · Project schema {project.schema_version} · Export profile: {profile}<p>Exporter {__version__} · View schema 1</p><p>View digest (SHA-256): <code>{view_digest}</code></p></footer>
<script type="application/json" id="plan-data">{payload}</script><script>{_JS}</script></body></html>
"""
    styles = re.findall(r"<style>(.*?)</style>", body, re.DOTALL)
    policy = ("default-src 'none'; script-src " + _hash_source(_JS) + "; style-src "
              + " ".join(_hash_source(style) for style in styles)
              + "; img-src 'none'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'")
    return body.replace("__CSP__", escape(policy, quote=True), 1)


def _safe_json(value: object) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    for char, encoded in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        text = text.replace(char, encoded)
    return text


def _hash_source(text: str) -> str:
    digest = base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode("ascii")
    return f"'sha256-{digest}'"
