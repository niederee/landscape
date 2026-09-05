"""Offline comparison of Python-resolved snapshots in one shared parcel frame."""
from __future__ import annotations

from html import escape
from pathlib import Path
import re

from landscape_planner.analysis.validation import validate_project
from landscape_planner.estimating.quantities import format_quantity
from landscape_planner.model.project import LandscapeProject
from landscape_planner.planning.concepts import compare_projects
from landscape_planner.rendering.html import existing_conditions_html, _hash_source

_CSS = """
*{box-sizing:border-box}body{margin:0;background:#f4f5f0;color:#202923;font:16px system-ui,sans-serif}
header,main{padding:20px}header{background:#173f35;color:white}h1{margin:0}h2{font-size:1.2rem}
.controls{display:none;gap:16px;flex-wrap:wrap;padding:16px;background:white}.enhanced .controls{display:flex}
label{display:flex;align-items:center;gap:8px}select{font:inherit;padding:8px;max-width:100%}
.snapshots{display:grid;grid-template-columns:minmax(0,1fr);gap:16px}.snapshots.paired{grid-template-columns:repeat(2,minmax(0,1fr))}
.snapshot{min-width:0;background:white;border:1px solid #ccd5cd;padding:12px;overflow-wrap:anywhere}
.snapshot[hidden]{display:none}iframe{width:100%;height:1000px;border:1px solid #ccd5cd;background:white}
table{border-collapse:collapse;width:100%}th,td{padding:7px;text-align:left;border-bottom:1px solid #ddd}
details{margin:12px 0}summary{cursor:pointer}select:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid #126bd3}
@media(max-width:850px){.snapshots.paired{grid-template-columns:1fr}main,header{padding:12px}}
@media print{.controls{display:none!important}.snapshots.paired{grid-template-columns:1fr}iframe{height:1800px}.snapshot{break-before:page}}
"""
_JS = """'use strict';
(() => {
 const cards = Array.from(document.querySelectorAll('.snapshot'));
 const frames = cards.map(card => card.querySelector('iframe'));
 const left = document.getElementById('snapshot-left');
 const right = document.getElementById('snapshot-right');
 const paired = document.getElementById('paired');
 const sync = document.getElementById('sync-camera');
 let selection = null;
 function inspect(frame) {
   if (!selection || !frame.contentDocument) return;
   const doc = frame.contentDocument;
   const button = Array.from(doc.querySelectorAll('#entity-list button')).find(b => b.dataset.entityId === selection);
   if (button) button.click();
   else {
     doc.querySelectorAll('.selected').forEach(n => n.classList.remove('selected'));
     doc.querySelectorAll('#entity-list button').forEach(n => n.setAttribute('aria-pressed', 'false'));
     const inspector = doc.getElementById('inspector');
     if (inspector) inspector.textContent = selection + ': not present in this option.';
   }
 }
 function show() {
   cards.forEach((card,i) => {card.hidden = String(i)!==left.value && !(paired.checked && String(i)===right.value);});
   document.getElementById('snapshots').classList.toggle('paired', paired.checked && left.value!==right.value);
   right.disabled = !paired.checked;
   frames.forEach(inspect);
 }
 [left,right,paired].forEach(control => control.addEventListener('change',show));
 frames.forEach(frame => {
   function ready() {
     const doc = frame.contentDocument;
     const svg = doc && doc.querySelector('#viewport svg');
     if (!svg || frame.dataset.bound) return;
     frame.dataset.bound = 'true';
     doc.addEventListener('click', event => {
       const entity = event.target.closest('[data-entity-id]');
       if (entity) selection = entity.dataset.entityId;
     });
     doc.addEventListener('keydown', event => {
       const entity = event.target.closest('[data-entity-id]');
       if (entity && (event.key==='Enter' || event.key===' ')) selection = entity.dataset.entityId;
     });
     // Every sheet uses the same parcel-derived world-to-sheet transform. Copying
     // its SVG viewBox synchronizes world coordinates, independent of CSS size.
     new MutationObserver(() => {
       if (!sync.checked) return;
       const box = svg.getAttribute('viewBox');
       frames.forEach(other => {
         const target = other.contentDocument && other.contentDocument.querySelector('#viewport svg');
         if (target && target.getAttribute('viewBox') !== box) {
           other.contentWindow.dispatchEvent(new other.contentWindow.CustomEvent('landscape-camera', {detail:box.split(' ').map(Number)}));
         }
       });
     }).observe(svg,{attributes:true,attributeFilter:['viewBox']});
     inspect(frame);
   }
   frame.addEventListener('load',ready); ready();
 });
 document.documentElement.classList.add('enhanced'); show();
})();
"""


def _difference_html(baseline: LandscapeProject, snapshot: LandscapeProject, *, phase_scope: bool = False) -> str:
    difference = compare_projects(baseline, snapshot)
    if hasattr(difference, "model_dump"):
        difference = difference.model_dump(mode="json")
    groups = "".join(
        f'<p><strong>{label}:</strong> {escape(", ".join(difference.get(key, []))) or "None"}</p>'
        for key, label in (("added", "Added"), ("removed", "Removed"),
                           ("modified", "Modified"), ("preserved", "Unchanged"))
    )
    rows = "".join(
        f'<tr><td>{escape(row["category"].replace("_", " "))}</td><td>{escape(row["unit"])}</td>'
        + "".join(f'<td>{format_quantity(row[key])}</td>' for key in ("before", "after", "delta"))
        + '</tr>' for row in difference.get("quantity_deltas", [])
    )
    heading = "Changes in this phase (from previous cumulative state)" if phase_scope else "Changes from baseline"
    before_label = "Previous state" if phase_scope else "Baseline"
    return (f'<details open><summary>{heading}</summary>{groups}'
            '<p>Whole-plan geometric quantities; overlapping categories are not additive. Net change is not construction or demolition quantity. Unmodeled shade, water use and maintenance are unknown. Costs are unknown unless explicitly supplied below.</p>'
            f'<table><thead><tr><th>Category</th><th>Unit</th><th>{before_label}</th><th>Snapshot</th><th>Net change</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></details>')


def _phase_html(metadata: dict, profile: str) -> str:
    parts = []
    if metadata:
        parts.append('<p>Cost ranges cover only supplied line items, not a complete project quote. Unlisted work is not included. Source-backed allowances are estimates in USD.</p>')
    rows = []
    for item in metadata.get("cost_items", []):
        quantity = item.get("quantity")
        low, high = item.get("rate_low"), item.get("rate_high")
        known = quantity is not None and low is not None and high is not None
        rates = f"{low}–{high}" if known else "unknown"
        extension = f"{format_quantity(quantity * low)}–{format_quantity(quantity * high)}" if known else "unknown"
        source = (str(item.get("source") or "unknown") if profile == "private"
                  else "Sourced allowance" if item.get("source") else "unknown")
        cells = [str(item.get("name") or item.get("id", "")), str(item.get("id", "")),
                 str(quantity) if quantity is not None else "unknown", str(item.get("unit", "unknown")), rates, extension, source]
        rows.append("<tr>" + "".join("<td>" + escape(cell) + "</td>" for cell in cells) + "</tr>")
    if rows:
        parts.append('<details open><summary>Phase cost allowances</summary><table><thead><tr><th>Item</th><th>ID</th><th>Quantity</th><th>Unit</th><th>Unit rate (USD)</th><th>Extension (USD)</th><th>Source</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></details>")
    for key, label in (("cost", "Phase cost"), ("cumulative_cost", "Cumulative cost")):
        cost = metadata.get(key)
        if not isinstance(cost, dict):
            continue
        low, high = cost.get("known_low"), cost.get("known_high")
        if low is None or high is None:
            parts.append(f'<p>{label}: unknown.</p>')
            continue
        complete = cost.get("complete") is True
        qualifier = "estimate" if complete else "known subtotal; incomplete estimate"
        parts.append(f'<p>{label} ({qualifier}): USD {escape(str(low))}–{escape(str(high))}.</p>')
        unknown = cost.get("unknown_item_ids", [])
        if unknown:
            parts.append('<p>Unknown cost items: ' + escape(', '.join(str(item) for item in unknown)) + '.</p>')
    dependencies = metadata.get("depends_on", [])
    if dependencies:
        parts.append('<p>Prerequisite phases: ' + escape(', '.join(str(item) for item in dependencies)) + '.</p>')
    warnings = metadata.get("warnings", [])
    if warnings:
        if profile == "private":
            parts.append('<ul>' + ''.join('<li>' + escape(str(w)) + '</li>' for w in warnings) + '</ul>')
        else:
            parts.append(f'<p>{len(warnings)} phase warning(s). Consult the private planning report for details.</p>')
    return ''.join(parts)


def comparison_html(
    snapshots: list[tuple[str, str, LandscapeProject]], profile: str = "share",
    project_root: Path | None = None, metadata: dict[str, dict] | None = None,
) -> str:
    """Render baseline first, followed by explicit concept or cumulative snapshots.

    Titles and snapshot IDs are public review labels in the share profile. Raw
    planning metadata is never embedded. Snapshot documents have separate DOMs.
    """
    if not snapshots:
        raise ValueError("At least one baseline snapshot is required.")
    if profile not in {"share", "private"}:
        raise ValueError("HTML profile must be 'share' or 'private'.")
    ids = [item[0] for item in snapshots]
    if len(ids) != len(set(ids)):
        raise ValueError("Snapshot IDs must be unique.")
    baseline = snapshots[0][2]
    documents = []
    cards = []
    for index, (identifier, title, project) in enumerate(snapshots):
        if (project.coordinate_system != baseline.coordinate_system or
                project.existing_conditions.parcel.boundary != baseline.existing_conditions.parcel.boundary):
            raise ValueError("Comparison snapshots must share the same parcel boundary and coordinate frame.")
        result = validate_project(project, project_root=project_root)
        document = existing_conditions_html(project, profile, result)
        phase = (metadata or {}).get(identifier, {})
        state = "Existing conditions" if index == 0 else ("Cumulative phase state" if phase else "Proposed concept")
        document = document.replace('· Existing conditions</title>', f'· {state}</title>', 1)
        document = document.replace('L1.0 · Existing conditions · Read-only review', f'L1.0 · {state} · Read-only review', 1)
        document = document.replace('aria-label="Existing conditions landscape plan"', f'aria-label="{state} landscape plan"', 1)
        document = re.sub(r'(<text class="meta"[^>]*>)Existing Conditions(</text>)', lambda match: match[1] + state + match[2], document, count=1)
        documents.append(document)
        summary = _difference_html(baseline, project) if index else '<p>Existing-conditions reference.</p>'
        if index and phase:
            summary += _difference_html(snapshots[index - 1][2], project, phase_scope=True)
        cards.append(f'<section class="snapshot" id="snapshot-{index}"{ " hidden" if index else ""}>'
                     f'<h2>{escape(title)}</h2><p>{state}</p>{summary}{_phase_html(phase, profile)}'
                     f'<iframe title="{escape(title, quote=True)}" srcdoc="{escape(document, quote=True)}"></iframe></section>')
    options = ''.join(f'<option value="{index}">{escape(title)}</option>' for index, (_, title, _) in enumerate(snapshots))
    right_options = options.replace('value="1"', 'value="1" selected', 1)
    body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="__CSP__"><title>Landscape snapshot comparison</title><style>{_CSS}</style></head>
<body><header><h1>Landscape snapshot comparison</h1><p>Read-only alternatives and cumulative construction states.</p></header><main>
<p>Planning review — not a construction or survey document. Each snapshot retains source confidence and validation warnings. Snapshot labels and entity labels are included in share exports; review them before sharing.</p>
<p>All plans use the same parcel coordinate frame. Construction phases do not represent plant growth.</p>
<div class="controls"><label>View <select id="snapshot-left">{options}</select></label>
<label><input type="checkbox" id="paired">Side by side</label><label>Compare with <select id="snapshot-right" disabled>{right_options}</select></label>
<label><input type="checkbox" id="sync-camera" checked>Synchronize navigation</label></div>
<noscript><p>The baseline plan and its quantities remain available without JavaScript. Enable JavaScript to switch snapshots and compare alternatives.</p></noscript>
<div class="snapshots" id="snapshots">{''.join(cards)}</div></main><script>{_JS}</script></body></html>'''
    # srcdoc inherits its parent's CSP; authorize exactly the generated child
    # styles/scripts as well as the shell's. No network resources are permitted.
    styles = [_CSS] + [s for doc in documents for s in re.findall(r'<style>(.*?)</style>', doc, re.DOTALL)]
    scripts = [_JS] + [s for doc in documents for s in re.findall(r'<script>(.*?)</script>', doc, re.DOTALL)]
    policy = ("default-src 'none'; frame-src 'self' about:; script-src " + ' '.join(sorted({_hash_source(s) for s in scripts}))
              + '; style-src ' + ' '.join(sorted({_hash_source(s) for s in styles}))
              + "; img-src 'none'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'")
    return body.replace('__CSP__', escape(policy, quote=True), 1)
