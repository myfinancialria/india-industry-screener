"""
Render docs/index.html from docs/data.json — a self-contained, responsive,
theme-aware static page for GitHub Pages.

Framed strictly as an educational quantitative screen: factual metrics only,
no buy/sell/target language, prominent 'not investment advice' disclaimer.
"""
import json
import os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "docs", "data.json")
OUT = os.path.join(HERE, "docs", "index.html")


def fmt(v, suffix="", dash="—"):
    if not isinstance(v, (int, float)):
        return dash
    if suffix == "cr":
        return f"₹{v:,.0f} cr"
    return f"{v:g}{suffix}"


def metric_cell(v, suffix, good=None):
    txt = fmt(v, suffix)
    cls = ""
    if good is not None and isinstance(v, (int, float)):
        cls = " ok" if good(v) else " weak"
    return f'<td class="num{cls}">{txt}</td>'


def render_row(c):
    badge = ('<span class="badge pass">PASS</span>' if c["passed"]
             else f'<span class="badge flag" title="{escape(", ".join(c["fails"]))}">flagged</span>')
    fails = f'<div class="fails">misses: {escape(", ".join(c["fails"]))}</div>' if c["fails"] else ""
    return f"""<tr>
      <td class="tk"><span class="sym">{escape(c['ticker'])}</span>{badge}
        <div class="cname">{escape(c.get('name') or '')}</div>{fails}</td>
      {metric_cell(c.get('mcap'), 'cr')}
      {metric_cell(c.get('roce'), '%', lambda v: v >= 15)}
      {metric_cell(c.get('roe'), '%', lambda v: v >= 15)}
      {metric_cell(c.get('sales_cagr_5y'), '%', lambda v: v >= 10)}
      {metric_cell(c.get('profit_cagr_5y'), '%', lambda v: v >= 12)}
      {metric_cell(c.get('opm'), '%')}
      {metric_cell(c.get('de'), '', lambda v: v <= 1)}
      {metric_cell(c.get('pe'), '')}
    </tr>"""


def render_industry(ind):
    rows = "".join(render_row(c) for c in ind["top3"]) or \
        '<tr><td colspan="9" class="empty">No data fetched this run.</td></tr>'
    kind_tag = f'<span class="kind {ind["kind"]}">{ind["kind"]}</span>'
    return f"""<section class="ind">
      <div class="ind-head">
        <h3>{escape(ind['name'])} {kind_tag}</h3>
        <span class="cov">{ind['candidates_fetched']}/{ind['candidates_total']} screened</span>
      </div>
      <p class="kpi"><b>Deciding metric:</b> {escape(ind['kpi'])}</p>
      <p class="note">{escape(ind['note'])}</p>
      <div class="twrap"><table>
        <thead><tr>
          <th>Company</th><th class="num">Mkt Cap</th><th class="num">ROCE</th>
          <th class="num">ROE</th><th class="num">Sales 5y</th><th class="num">PAT 5y</th>
          <th class="num">OPM</th><th class="num">D/E</th><th class="num">P/E</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
    </section>"""


def render(data):
    groups = {}
    for ind in data["industries"]:
        groups.setdefault(ind["group"], []).append(ind)

    sections = ""
    for group, inds in groups.items():
        cards = "".join(render_industry(i) for i in inds)
        sections += f'<div class="group"><h2>{escape(group)}</h2>{cards}</div>'

    bf = data["base_filter"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>India Industry Screener — Top 3 per Industry</title>
<meta name="description" content="Educational quantitative stock screen: top 3 companies per Indian industry on fundamental-quality metrics. Not investment advice.">
<style>
  :root {{
    --bg:#f7f8fa; --card:#fff; --ink:#12151c; --muted:#5b6472; --line:#e6e9ee;
    --accent:#1f6feb; --ok:#0f8a4f; --weak:#c2410c; --flag:#b45309; --pass:#0f8a4f;
    --chip:#eef1f6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#0d1117; --card:#161b22; --ink:#e6edf3; --muted:#9aa4b2;
      --line:#272e38; --accent:#4c8dff; --ok:#3fb950; --weak:#f0883e; --flag:#d29922;
      --pass:#3fb950; --chip:#21262d; }}
  }}
  :root[data-theme="dark"] {{ --bg:#0d1117; --card:#161b22; --ink:#e6edf3; --muted:#9aa4b2;
    --line:#272e38; --accent:#4c8dff; --ok:#3fb950; --weak:#f0883e; --flag:#d29922; --pass:#3fb950; --chip:#21262d; }}
  :root[data-theme="light"] {{ --bg:#f7f8fa; --card:#fff; --ink:#12151c; --muted:#5b6472;
    --line:#e6e9ee; --accent:#1f6feb; --ok:#0f8a4f; --weak:#c2410c; --flag:#b45309; --pass:#0f8a4f; --chip:#eef1f6; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:24px 18px 80px; }}
  header h1 {{ font-size:1.9rem; margin:0 0 6px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); margin:0 0 4px; }}
  .stamp {{ color:var(--muted); font-size:.85rem; }}
  .disclaimer {{ background:var(--card); border:1px solid var(--line); border-left:4px solid var(--flag);
    border-radius:10px; padding:14px 16px; margin:18px 0 8px; font-size:.9rem; color:var(--muted); }}
  .disclaimer b {{ color:var(--ink); }}
  .method {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:14px 16px; margin:14px 0 26px; font-size:.9rem; }}
  .method summary {{ cursor:pointer; font-weight:600; color:var(--ink); }}
  .method ul {{ margin:10px 0 0; padding-left:18px; color:var(--muted); }}
  .group > h2 {{ font-size:1.15rem; margin:34px 0 8px; padding-bottom:6px; border-bottom:2px solid var(--line); }}
  .ind {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px; margin:14px 0; }}
  .ind-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; flex-wrap:wrap; }}
  .ind h3 {{ margin:0; font-size:1.05rem; }}
  .cov {{ color:var(--muted); font-size:.8rem; white-space:nowrap; }}
  .kind {{ font-size:.65rem; text-transform:uppercase; letter-spacing:.04em; padding:2px 7px;
    border-radius:20px; background:var(--chip); color:var(--muted); vertical-align:middle; margin-left:6px; }}
  .kind.cyclical {{ color:var(--weak); }} .kind.financial {{ color:var(--accent); }}
  .kind.realestate {{ color:var(--flag); }}
  .kpi {{ margin:8px 0 2px; font-size:.86rem; color:var(--muted); }}
  .kpi b {{ color:var(--ink); }}
  .note {{ margin:2px 0 10px; font-size:.82rem; color:var(--muted); font-style:italic; }}
  .twrap {{ overflow-x:auto; }}
  table {{ width:100%; border-collapse:collapse; font-size:.86rem; min-width:640px; }}
  th, td {{ padding:8px 10px; text-align:left; border-bottom:1px solid var(--line); }}
  th.num, td.num {{ text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }}
  thead th {{ color:var(--muted); font-weight:600; font-size:.78rem; }}
  td.num.ok {{ color:var(--ok); }} td.num.weak {{ color:var(--weak); }}
  .tk .sym {{ font-weight:700; }}
  .cname {{ color:var(--muted); font-size:.76rem; margin-top:2px; }}
  .fails {{ color:var(--flag); font-size:.72rem; margin-top:2px; }}
  .badge {{ font-size:.62rem; text-transform:uppercase; letter-spacing:.03em; padding:2px 6px;
    border-radius:20px; margin-left:8px; vertical-align:middle; }}
  .badge.pass {{ background:color-mix(in srgb,var(--pass) 18%,transparent); color:var(--pass); }}
  .badge.flag {{ background:color-mix(in srgb,var(--flag) 18%,transparent); color:var(--flag); }}
  .empty {{ color:var(--muted); text-align:center; font-style:italic; }}
  .toggle {{ position:fixed; top:14px; right:14px; background:var(--card); border:1px solid var(--line);
    color:var(--ink); border-radius:20px; padding:6px 12px; font-size:.8rem; cursor:pointer; }}
  footer {{ margin-top:40px; color:var(--muted); font-size:.8rem; text-align:center; }}
  a {{ color:var(--accent); }}
</style>
</head>
<body>
<button class="toggle" onclick="tt()">◐ theme</button>
<div class="wrap">
  <header>
    <h1>India Industry Screener</h1>
    <p class="sub">Top 3 companies per industry on fundamental-quality metrics · ranked automatically from screener.in data</p>
    <p class="stamp">Last refreshed: <b>{escape(data['generated_at'])}</b> · {data['industry_count']} industries · refreshes on the 1st &amp; 15th of each month</p>
  </header>

  <div class="disclaimer">
    <b>Educational tool — not investment advice.</b> This page is the output of an automated
    quantitative screen and is for information and educational purposes only. It is <b>not</b> a
    recommendation, solicitation, or advice to buy, sell, or hold any security, and contains no
    price targets or buy/sell calls. The author is <b>not</b> a SEBI-registered Research Analyst or
    Investment Adviser. Rankings are mechanical, may contain data errors, and must not be relied
    upon for any financial decision. Do your own research and consult a SEBI-registered adviser.
  </div>

  <details class="method">
    <summary>How this screen works</summary>
    <ul>
      <li><b>Base quality filter:</b> ROCE ≥ {bf['roce_min']:g}%, ROE ≥ {bf['roe_min']:g}%,
        5yr sales CAGR ≥ {bf['sales_cagr_min']:g}%, 5yr profit CAGR ≥ {bf['profit_cagr_min']:g}%,
        Debt/Equity ≤ {bf['de_max']:g}. A <span class="badge pass">PASS</span> badge means all
        applicable thresholds are met; <span class="badge flag">flagged</span> means the name ranks
        top-3 but misses one or more (hover to see which).</li>
      <li><b>Financials</b> (banks, NBFCs, insurers) are ranked on ROE + profit/sales growth —
        ROCE, OPM and D/E are not meaningful for lenders. Their true KPIs (ROA, NIM, GNPA, combined
        ratio, VNB) are <i>not</i> scraped; treat those rankings as indicative and review manually.</li>
      <li><b>Cyclicals</b> (metals, cement, power, oil &amp; gas, hotels) and <b>real estate</b>
        structurally fail the quality filter — they are ranked on relative strength, not absolute pass.</li>
      <li>Metrics are scraped from public screener.in company pages (consolidated where available)
        and reflect trailing reported figures. Sector KPIs shown as "Deciding metric" are analyst
        context, not live data.</li>
    </ul>
  </details>

  {sections}

  <footer>
    Generated by an open-source screening pipeline · data © screener.in ·
    metrics are trailing/approximate — verify on the source before use.
  </footer>
</div>
<script>
  function tt(){{var r=document.documentElement;var d=r.getAttribute('data-theme');
    var cur=d||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
    r.setAttribute('data-theme',cur==='dark'?'light':'dark');}}
</script>
</body>
</html>"""


def main():
    with open(DATA) as f:
        data = json.load(f)
    with open(OUT, "w") as f:
        f.write(render(data))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
