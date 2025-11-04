import json
import os
from typing import Any, Dict, List


def generate_json_report(results: List[Dict[str, Any]]) -> str:
    return json.dumps({"results": results}, ensure_ascii=False, indent=2)


def save_report(content: str, name: str = "report.json"):
    out_dir = os.getenv("REPORT_DIR", "/app/logs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_html_report(results: List[Dict[str, Any]]) -> str:
    rows = []
    for r in results:
        rows.append(
            f"<tr><td>{r.get('deployment','')}</td><td>{r.get('image','')}</td><td>{r.get('old_sha','')}</td>"
            f"<td>{r.get('new_sha','')}</td><td>{r.get('updated', False)}</td><td>{r.get('error','')}</td></tr>"
        )
    table = """
    <html>
    <head><meta charset='utf-8'><title>ECR Check Report</title>
    <style>table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px}</style>
    </head>
    <body>
    <h2>ECR Check Report</h2>
    <table>
      <thead>
        <tr><th>Deployment</th><th>Image</th><th>Old SHA</th><th>New SHA</th><th>Updated</th><th>Error</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    </body>
    </html>
    """.replace("{rows}", "\n".join(rows))
    return table