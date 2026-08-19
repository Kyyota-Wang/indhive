from __future__ import annotations

import argparse
import html
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ind_m1_poc.loader import list_cases, load_source_case  # noqa: E402
from ind_m1_poc.orchestrator import generate_module1_package  # noqa: E402
from ind_m1_poc.paths import OUTPUTS_DIR  # noqa: E402


class POCHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        cases = list_cases()
        selected_case_id = params.get("case_id", [cases[0]["case_id"]])[0]
        should_generate = params.get("generate", ["0"])[0] == "1"

        package = None
        error = None
        if should_generate:
            try:
                package = generate_module1_package(selected_case_id, use_llm=True)
            except Exception as exc:  # noqa: BLE001 - show demo error in UI.
                error = f"{type(exc).__name__}: {exc}"

        source_case = load_source_case(selected_case_id)
        page = render_page(cases, selected_case_id, source_case, package, error)
        body = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def render_page(
    cases: list[dict[str, str]],
    selected_case_id: str,
    source_case: dict,
    package: dict | None,
    error: str | None,
) -> str:
    options = "\n".join(
        f'<option value="{case["case_id"]}" {"selected" if case["case_id"] == selected_case_id else ""}>'
        f'{html.escape(case["case_id"])} - {html.escape(case["case_label"].split(" - ", 1)[-1])}'
        "</option>"
        for case in cases
    )
    source_json = html.escape(json.dumps(source_case, indent=2))
    generated_html = render_generated(package, error)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IND Module 1 POC Agent</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --line: #d9dee7;
      --text: #202631;
      --muted: #5d6675;
      --accent: #2457c5;
      --pass: #157347;
      --warn: #9a6700;
      --missing: #b54708;
      --conflict: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
      letter-spacing: 0;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      padding: 18px 28px;
    }}
    h1 {{ font-size: 24px; margin: 0 0 4px; }}
    h2 {{ font-size: 18px; margin: 0 0 12px; }}
    h3 {{ font-size: 15px; margin: 18px 0 8px; }}
    p {{ margin: 0; color: var(--muted); }}
    main {{
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 18px;
      padding: 18px 28px 32px;
    }}
    section, aside {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    label {{ display: block; font-weight: 700; margin-bottom: 8px; }}
    select, button {{
      width: 100%;
      min-height: 38px;
      font-size: 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      background: #fff;
    }}
    button {{
      margin-top: 10px;
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }}
    pre {{
      white-space: pre-wrap;
      overflow-x: auto;
      background: #f3f5f8;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      font-size: 13px;
      line-height: 1.45;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(90px, 1fr));
      gap: 10px;
      margin: 12px 0 16px;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fbfcfe;
    }}
    .metric strong {{ display: block; font-size: 22px; }}
    .PASS {{ color: var(--pass); }}
    .WARNING {{ color: var(--warn); }}
    .MISSING {{ color: var(--missing); }}
    .CONFLICT {{ color: var(--conflict); }}
    .note {{
      color: var(--muted);
      font-size: 13px;
      margin: 8px 0 14px;
    }}
    .error {{
      border: 1px solid var(--conflict);
      background: #fff5f5;
      color: var(--conflict);
      border-radius: 8px;
      padding: 12px;
    }}
    @media (max-width: 860px) {{
      main {{ grid-template-columns: 1fr; padding: 14px; }}
      header {{ padding: 16px 14px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>IND Module 1 POC Agent</h1>
    <p>Synthetic data demo. Outputs are POC drafts and are not FDA-submission-ready.</p>
  </header>
  <main>
    <aside>
      <form method="get">
        <label for="case_id">Demo Case</label>
        <select id="case_id" name="case_id">{options}</select>
        <input type="hidden" name="generate" value="1">
        <button type="submit">Generate Module 1 Package</button>
      </form>
      <h3>Case Snapshot</h3>
      <p>Scenario: <code>{html.escape(source_case["scenario_type"])}</code></p>
      <p>Source records: <code>{len(source_case["source_records"])}</code></p>
      <h3>Agent-Visible Source Data</h3>
      <pre>{source_json}</pre>
    </aside>
    <section>
      {generated_html}
    </section>
  </main>
</body>
</html>"""


def render_generated(package: dict | None, error: str | None) -> str:
    if error:
        return f'<div class="error">{html.escape(error)}</div>'
    if not package:
        return "<h2>Ready</h2><p>Select a case and generate the package.</p>"

    summary = package["validation"]["summary"]
    metrics = "".join(
        f'<div class="metric"><span class="{status}">{status}</span><strong>{summary[status]}</strong></div>'
        for status in ["PASS", "WARNING", "MISSING", "CONFLICT"]
    )
    form_rows = "".join(
        "<tr>"
        f"<td>{html.escape(field['label'])}</td>"
        f"<td class=\"{field['status']}\">{field['status']}</td>"
        f"<td>{html.escape(str(field['value'] if field['value'] is not None else '-'))}</td>"
        f"<td>{html.escape(field.get('message') or '')}</td>"
        "</tr>"
        for field in package["form_1571"]["fields"]
    )
    validation_rows = "".join(
        "<tr>"
        f"<td class=\"{issue['status']}\">{issue['status']}</td>"
        f"<td>{html.escape(issue.get('field') or '')}</td>"
        f"<td>{html.escape(issue['message'])}</td>"
        "</tr>"
        for issue in package["validation"]["issues"]
    )
    warnings = "".join(
        f"<p class=\"note\">{html.escape(warning)}</p>"
        for warning in package["cover_letter"].get("warnings", [])
    )

    return f"""
<h2>Generated Package</h2>
<p class="note">Artifacts persisted to <code>{html.escape(str(OUTPUTS_DIR / package["case_id"]))}</code></p>
<div class="summary">{metrics}</div>
{warnings}
<h3>Cover Letter</h3>
<pre>{html.escape(package["cover_letter"]["text"])}</pre>
<h3>FDA 1571 Field View</h3>
<table>
  <thead><tr><th>Field</th><th>Status</th><th>Value</th><th>Note</th></tr></thead>
  <tbody>{form_rows}</tbody>
</table>
<h3>Module 1 TOC</h3>
<pre>{html.escape(package["toc"]["markdown"])}</pre>
<h3>Validation</h3>
<table>
  <thead><tr><th>Status</th><th>Field</th><th>Message</th></tr></thead>
  <tbody>{validation_rows}</tbody>
</table>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the no-dependency IND Module 1 POC web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), POCHandler)
    print(f"Serving IND Module 1 POC Agent at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

